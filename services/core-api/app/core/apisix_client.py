import uuid

import httpx

from neurix_shared.config import settings


def consumer_name_for_api_key(api_key_id: uuid.UUID) -> str:
    # APISIX consumer usernames must match ^[a-zA-Z0-9_]+$ — UUIDs contain hyphens, so
    # use .hex (no separators) rather than str(). One helper so create/revoke can never
    # drift onto different naming schemes.
    return f"apikey_{api_key_id.hex}"


async def create_consumer(username: str, api_key: str) -> None:
    """One APISIX Consumer per API key, not per user — key-auth matches on the key value
    globally, so two keys for the same user each need their own consumer. Consumer name
    is derived from the key's own id (see router.py) precisely so revoke can find it."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.put(
            f"{settings.apisix_admin_url}/apisix/admin/consumers/{username}",
            headers={"X-API-KEY": settings.apisix_admin_key, "Content-Type": "application/json"},
            json={"username": username, "plugins": {"key-auth": {"key": api_key}}},
        )
        resp.raise_for_status()


async def delete_consumer(username: str) -> None:
    # A revoked key must stop working at the gateway immediately, not just look revoked
    # in our own DB — deleting the consumer is what actually enforces that.
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.delete(
            f"{settings.apisix_admin_url}/apisix/admin/consumers/{username}",
            headers={"X-API-KEY": settings.apisix_admin_key},
        )
        if resp.status_code not in (200, 404):  # 404 = already gone, fine
            resp.raise_for_status()
