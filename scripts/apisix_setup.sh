#!/usr/bin/env bash
# Applies infra/apisix/route-reference-data.yaml via the APISIX Admin API, binding the
# APISIX consumer to the SAME raw API key that scripts/seed.py already hashed into the
# api_keys table — so gateway auth and our own usage/audit bookkeeping refer to one key,
# not two independently-generated ones.
#
# Usage: python scripts/seed.py                # prints a raw key
#        source infra/.env
#        ./scripts/apisix_setup.sh <raw-key-from-seed.py>
set -euo pipefail

: "${APISIX_ADMIN_KEY:?APISIX_ADMIN_KEY not set — source infra/.env first}"
TEST_API_KEY="${1:?usage: apisix_setup.sh <raw-api-key-printed-by-scripts/seed.py>}"

ADMIN_URL="http://127.0.0.1:9180"

curl -sf -X PUT "${ADMIN_URL}/apisix/admin/consumers/milestone0_test_consumer" \
  -H "X-API-KEY: ${APISIX_ADMIN_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
        \"username\": \"milestone0_test_consumer\",
        \"plugins\": { \"key-auth\": { \"key\": \"${TEST_API_KEY}\" } }
      }" > /dev/null

curl -sf -X PUT "${ADMIN_URL}/apisix/admin/routes/reference-data" \
  -H "X-API-KEY: ${APISIX_ADMIN_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
        "uri": "/v1/reference/*",
        "upstream": {
          "type": "roundrobin",
          "nodes": { "core-api:8000": 1 }
        },
        "plugins": {
          "key-auth": {},
          "limit-count": {
            "count": 120,
            "time_window": 60,
            "key": "$consumer_name",
            "key_type": "var",
            "rejected_code": 429
          }
        }
      }' > /dev/null

curl -sf -X PUT "${ADMIN_URL}/apisix/admin/routes/environment-data" \
  -H "X-API-KEY: ${APISIX_ADMIN_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
        "uri": "/v1/environment/*",
        "upstream": {
          "type": "roundrobin",
          "nodes": { "core-api:8000": 1 }
        },
        "plugins": {
          "key-auth": {},
          "limit-count": {
            "count": 120,
            "time_window": 60,
            "key": "$consumer_name",
            "key_type": "var",
            "rejected_code": 429
          }
        }
      }' > /dev/null

echo "APISIX routes + consumer created."
echo "Test API key: ${TEST_API_KEY}"
echo
echo "Verify with:"
echo "  curl -H \"apikey: ${TEST_API_KEY}\" http://127.0.0.1:9080/v1/reference/provinces"
echo "  curl -H \"apikey: ${TEST_API_KEY}\" http://127.0.0.1:9080/v1/environment/pm25"
echo "  curl http://127.0.0.1:9080/v1/reference/provinces   # expect 401, no key"
