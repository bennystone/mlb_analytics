import os
import time
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="MLB Analytics API", version="0.1.0")

MLB_API_BASE_URL = os.getenv("MLB_API_BASE_URL", "https://statsapi.mlb.com/api/v1")


async def fetch_json(path: str, params: Optional[dict] = None, retries: int = 3, timeout: float = 10.0):
    url = f"{MLB_API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    last_exc = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            last_exc = exc
            # simple backoff
            time.sleep(0.5 * (2 ** attempt))
    raise HTTPException(status_code=502, detail=f"Upstream MLB API error: {last_exc}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/standings")
async def standings(
    season: int = Query(default=2024, ge=1900, description="Season year"),
    leagueId: Optional[str] = Query(default="103,104", description="Comma-separated league IDs (103=AL,104=NL)"),
):
    params = {"season": season}
    if leagueId:
        params["leagueId"] = leagueId
    data = await fetch_json("standings", params=params)
    return data


@app.get("/leaders/{category}")
async def leaders(
    category: str,
    season: int = Query(default=2024, ge=1900),
    limit: int = Query(default=10, ge=1, le=100),
):
    params = {
        "leaderCategories": category,
        "season": season,
        "limit": limit,
    }
    data = await fetch_json("stats/leaders", params=params)
    return data
