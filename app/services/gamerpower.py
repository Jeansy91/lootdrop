import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

GAMERPOWER_BASE = "https://www.gamerpower.com/api"


async def fetch_giveaways() -> list[dict[str, Any]]:
    """Fetch all active game giveaways from GamerPower (all platforms, one call)."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{GAMERPOWER_BASE}/giveaways",
                params={"type": "game"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    log.info("Fetched %d giveaways from GamerPower", len(data))
                    return data
            elif resp.status_code == 201:
                log.info("GamerPower: no active giveaways")
            else:
                log.warning("GamerPower API returned %d", resp.status_code)
        except httpx.RequestError as exc:
            log.error("Failed to reach GamerPower API: %s", exc)
    return []
