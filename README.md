# NeurixAI Data Platform

Thai open-data API platform — province/district/subdistrict, postal codes, public
holidays, BOT exchange rates, weather, PM2.5 — behind a subscription-metered gateway.

See [`docs/architecture.md`](docs/architecture.md) for the full design.

**All 6 of 6 connectors are live**: province/district/subdistrict (+ postal codes, same
dataset), public holidays, PM2.5 (Air4Thai), weather forecasts (TMD nwpapi), and BOT
exchange rates — across three core-api domains (`reference_data`, `environment_data`,
`market_data`), wired end to end through Postgres, Redis, and an APISIX gateway with
API-key auth.

**Developer Portal (Milestone P0) is live** at `services/portal` — Next.js + NextAuth
Credentials auth, signup/login/dashboard/API-key management, verified end to end in a
real browser. No direct DB access — pure HTTP client of core-api's new `platform` domain.

**Deferred, blocked on external registration** (same pattern as BOT/TMD were): Google and
Microsoft OAuth sign-in for the Developer Portal, and the Admin Portal (needs a Microsoft
Entra ID app registration on the company's Azure tenant). Also not yet built: light/dark
theme toggle, TOTP MFA for the Developer Portal (not blocked — buildable now), and email
verification on signup.

## Layout

```
services/
  shared/       # neurix_shared: SQLAlchemy models (schema source of truth) + Alembic migrations
  core-api/     # FastAPI — reads DB/cache, serves the public API
  ingestion/    # Connector framework + scheduler worker — writes DB
infra/          # docker-compose.yml (postgres, redis, etcd, apisix) + apisix config
scripts/        # seed.py, apisix_setup.sh
docs/           # architecture.md
```

## Prerequisites

- Podman + `podman-compose` (or Docker + `docker-compose` — the compose file is engine-agnostic)
- `uv` (https://docs.astral.sh/uv/) if running services outside containers
- `openssl` (for generating the APISIX admin key)

## Run it

Migrations and the seed script run **inside the `core-api` container** (it already has
`neurix-shared`, Alembic, and `scripts/` baked in) — no local Python/uv setup required on
the host.

```bash
# 1. Configure secrets
cp infra/.env.example infra/.env
# edit infra/.env — set APISIX_ADMIN_KEY to: openssl rand -hex 24
source infra/.env

# 2. Bring up infra + services
cd infra
podman-compose up -d --build
podman-compose ps   # wait until all services report healthy

# 3. Apply the DB schema (applies every migration already in services/shared/alembic/versions/;
#    only re-run --autogenerate if you've changed a model and need a new migration file)
podman exec -w /app/shared neurix-core-api alembic upgrade head

# 4. Seed test fixtures (connector/product/plan/user/subscription/api key)
podman exec neurix-core-api python /app/scripts/seed.py
# prints a raw API key — copy it

# 5. Trigger ingestion manually (normally runs on each connector's own schedule)
podman exec neurix-ingestion python worker.py --once

# 6. Wire the API key into APISIX (creates routes for /v1/reference/*, /v1/environment/*, /v1/market/*)
cd ..
source infra/.env
./scripts/apisix_setup.sh <raw-api-key-from-step-4>

# 7. Verify end to end
curl http://localhost:8000/v1/reference/provinces | head                              # direct to core-api
curl http://localhost:8000/v1/reference/holidays?year=2026 | head
curl http://localhost:8000/v1/environment/pm25 | head
curl http://localhost:8000/v1/environment/weather?province_code=10 | head
curl http://localhost:8000/v1/market/exchange-rates?currency_code=USD | head
curl -H "apikey: <raw-api-key>" http://localhost:9080/v1/reference/provinces | head   # through the gateway
curl -H "apikey: <raw-api-key>" http://localhost:9080/v1/environment/pm25 | head
curl -H "apikey: <raw-api-key>" http://localhost:9080/v1/environment/weather | head
curl -H "apikey: <raw-api-key>" http://localhost:9080/v1/market/exchange-rates | head
curl http://localhost:9080/v1/reference/provinces                                     # no key — expect 401

# Alternative: sign up through the Developer Portal instead (http://localhost:3000) —
# it creates the account, subscription, and API key (synced to APISIX) all through the UI.
```

## Notes

- `services/shared` is the schema source of truth. Both `core-api` (reads) and
  `ingestion` (writes) depend on it as a local editable package via `uv` — see
  `[tool.uv.sources]` in their `pyproject.toml`.
- Ingestion upserts are idempotent — keyed on each table's natural identity (`code` for
  reference data, `(date, name_en)` for holidays, `(station_id, observed_at)` for PM2.5,
  `(province_code, forecast_date)` for weather, `(currency_code, rate_date)` for exchange
  rates — the last two upsert on purpose, since BOT/TMD can both revise an already
  published day, unlike PM2.5's accumulated history). Safe to re-run after a crash or
  manual retry.
- BOT's `Authorization` header takes the raw subscription key with no `Bearer ` prefix —
  confirmed from BOT's own interactive docs sample, don't "fix" this to add one.
- TMD's nwpapi rate-limits at 60 requests/window; the weather connector makes 77 (one
  per province) every run, so hitting 429 partway through is normal, not a bug — it's
  handled per-request via the `Retry-After` header (see `weather.py`), not by failing
  the whole batch.
- **If a new connector's target `.go.th` (or similar) host fails with `CERTIFICATE_VERIFY_FAILED`**:
  check `openssl s_client -connect <host>:443 -showcerts` for an incomplete chain before
  assuming it's our bug — several Thai government sites don't serve their intermediate
  certificate. See `services/ingestion/certs/letsencrypt_gen_y_root_yr.pem` for how this
  was diagnosed and fixed for air4thai.pcd.go.th (a missing/very-new Let's Encrypt root,
  fixed by appending the officially-published cross-signed cert to the image's trust
  store — never fix this by disabling verification).
- The APISIX admin API (port 9180) is not published beyond localhost in this compose
  file. Do not reuse this setup as-is for a non-local environment without revisiting
  network exposure.
