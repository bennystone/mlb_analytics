"""
MLB Leaderboards Router

Handles statistical leaderboards for hitting, pitching, and fielding categories.
"""

import time
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/leaders", tags=["leaderboards"])

MLB_API_BASE_URL = "https://statsapi.mlb.com/api/v1"

# Valid statistical categories
VALID_CATEGORIES = {
    "hitting": [
        "avg", "hr", "rbi", "r", "sb", "obp", "slg", "ops", "hits", "doubles", "triples"
    ],
    "pitching": [
        "era", "wins", "losses", "saves", "strikeouts", "whip", "innings_pitched", "quality_starts"
    ],
    "fielding": [
        "fielding_percentage", "assists", "putouts", "errors", "double_plays_turned"
    ]
}


async def fetch_mlb_data(path: str, params: Optional[Dict] = None) -> Dict:
    """Fetch data from MLB API with error handling."""
    url = f"{MLB_API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error("MLB API request failed", url=url, error=str(e))
        raise HTTPException(status_code=502, detail="MLB API temporarily unavailable")


def validate_category(category: str, stat_type: str) -> bool:
    """Validate that the category is valid for the given stat type."""
    if stat_type not in VALID_CATEGORIES:
        return False
    
    return category in VALID_CATEGORIES[stat_type]


@router.get("/categories")
async def get_available_categories():
    """
    Get list of available statistical categories.
    
    Returns all valid categories organized by stat type for reference.
    """
    return {
        "categories": VALID_CATEGORIES,
        "description": "Available statistical categories for leaderboards"
    }


@router.get("/hitting/top")
async def get_hitting_leaders(
    season: int = Query(default=2024, ge=1900, le=2030, description="MLB season year"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of leaders to return"),
    leagueId: Optional[str] = Query(default=None, description="League ID filter (103=AL, 104=NL)")
):
    """
    Get top hitting leaders across multiple categories.
    
    Returns leaders in batting average, home runs, RBIs, and other key hitting stats.
    """
    logger.info("Fetching hitting leaders", season=season, limit=limit)
    
    try:
        # Fetch multiple hitting categories
        categories = ["avg", "hr", "rbi", "r", "sb"]
        results = {}
        
        for cat in categories:
            params = {
                "leaderCategories": cat,
                "season": season,
                "limit": limit,
            }
            
            if leagueId:
                params["leagueId"] = leagueId
            
            data = await fetch_mlb_data("stats/leaders", params=params)
            results[cat] = data
        
        return {
            "stat_type": "hitting",
            "season": season,
            "categories": results,
            "last_updated": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to fetch hitting leaders", season=season, error=str(e))
        raise


@router.get("/pitching/top")
async def get_pitching_leaders(
    season: int = Query(default=2024, ge=1900, le=2030, description="MLB season year"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of leaders to return"),
    leagueId: Optional[str] = Query(default=None, description="League ID filter (103=AL, 104=NL)")
):
    """
    Get top pitching leaders across multiple categories.
    
    Returns leaders in ERA, wins, strikeouts, saves, and other key pitching stats.
    """
    logger.info("Fetching pitching leaders", season=season, limit=limit)
    
    try:
        # Fetch multiple pitching categories
        categories = ["era", "wins", "strikeouts", "saves", "whip"]
        results = {}
        
        for cat in categories:
            params = {
                "leaderCategories": cat,
                "season": season,
                "limit": limit,
            }
            
            if leagueId:
                params["leagueId"] = leagueId
            
            data = await fetch_mlb_data("stats/leaders", params=params)
            results[cat] = data
        
        return {
            "stat_type": "pitching",
            "season": season,
            "categories": results,
            "last_updated": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to fetch pitching leaders", season=season, error=str(e))
        raise


@router.get("/{stat_type}/{category}")
async def get_leaders(
    stat_type: str,
    category: str,
    season: int = Query(default=2024, ge=1900, le=2030, description="MLB season year"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of leaders to return"),
    leagueId: Optional[str] = Query(default=None, description="League ID filter (103=AL, 104=NL)")
):
    """
    Get statistical leaders for specific categories.
    
    Returns leaderboards for hitting, pitching, and fielding statistics with
    player information and season totals.
    """
    logger.info("Fetching leaders", stat_type=stat_type, category=category, season=season, limit=limit)
    
    # Validate stat type
    if stat_type.lower() not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stat_type. Must be one of: {', '.join(VALID_CATEGORIES.keys())}"
        )
    
    # Validate category for the stat type
    if not validate_category(category, stat_type.lower()):
        valid_cats = ", ".join(VALID_CATEGORIES[stat_type.lower()])
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}' for {stat_type}. Valid categories: {valid_cats}"
        )
    
    params = {
        "leaderCategories": category,
        "season": season,
        "limit": limit,
    }
    
    if leagueId:
        params["leagueId"] = leagueId
    
    try:
        data = await fetch_mlb_data("stats/leaders", params=params)
        
        return {
            "stat_type": stat_type,
            "category": category,
            "season": season,
            "limit": limit,
            "leaders": data,
            "last_updated": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to fetch leaders", stat_type=stat_type, category=category, season=season, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard data")
