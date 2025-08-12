"""
MLB Standings Router

Handles division standings, playoff races, and playoff probability calculations.
"""

import time
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/standings", tags=["standings"])

MLB_API_BASE_URL = "https://statsapi.mlb.com/api/v1"


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


def calculate_playoff_probabilities(standings_data: Dict) -> Dict[int, float]:
    """
    Calculate playoff probabilities based on current standings.
    
    This is a simplified calculation - in production, you'd use more sophisticated
    models like Monte Carlo simulations.
    """
    playoff_probs = {}
    
    try:
        for record in standings_data.get("records", []):
            division = record.get("division", {})
            division_id = division.get("id")
            
            if not division_id:
                continue
                
            teams = record.get("teamRecords", [])
            
            # Simple probability based on games back
            for team in teams:
                team_id = team.get("team", {}).get("id")
                games_back = team.get("gamesBack", 0)
                
                if team_id:
                    # Basic probability calculation
                    if games_back == 0:
                        prob = 0.85  # Division leader
                    elif games_back <= 2:
                        prob = 0.60  # Close race
                    elif games_back <= 5:
                        prob = 0.30  # Still in contention
                    elif games_back <= 10:
                        prob = 0.10  # Long shot
                    else:
                        prob = 0.01  # Very unlikely
                    
                    playoff_probs[team_id] = round(prob, 3)
    
    except Exception as e:
        logger.error("Error calculating playoff probabilities", error=str(e))
    
    return playoff_probs


@router.get("/")
async def get_standings(
    season: int = Query(default=2024, ge=1900, le=2030, description="MLB season year"),
    leagueId: Optional[str] = Query(
        default="103,104", 
        description="Comma-separated league IDs (103=AL, 104=NL)"
    ),
    include_probabilities: bool = Query(default=True, description="Include playoff probabilities")
):
    """
    Get current MLB division standings with optional playoff probabilities.
    
    Returns real-time standings data organized by division with team records,
    games back, and calculated playoff probabilities.
    """
    logger.info("Fetching standings", season=season, leagueId=leagueId)
    
    params = {"season": season}
    if leagueId:
        params["leagueId"] = leagueId
    
    try:
        standings_data = await fetch_mlb_data("standings", params=params)
        
        response = {
            "season": season,
            "standings": standings_data,
            "last_updated": time.time()
        }
        
        if include_probabilities:
            playoff_probs = calculate_playoff_probabilities(standings_data)
            response["playoff_probabilities"] = playoff_probs
        
        return response
        
    except Exception as e:
        logger.error("Failed to fetch standings", season=season, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch standings data")


@router.get("/division/{division_id}")
async def get_division_standings(
    division_id: int,
    season: int = Query(default=2024, ge=1900, le=2030, description="MLB season year")
):
    """
    Get standings for a specific division.
    
    Returns detailed standings for a single division with team records and statistics.
    """
    logger.info("Fetching division standings", division_id=division_id, season=season)
    
    try:
        standings_data = await fetch_mlb_data("standings", params={
            "season": season,
            "divisionId": division_id
        })
        
        playoff_probs = calculate_playoff_probabilities(standings_data)
        
        return {
            "division_id": division_id,
            "season": season,
            "standings": standings_data,
            "playoff_probabilities": playoff_probs,
            "last_updated": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to fetch division standings", division_id=division_id, season=season, error=str(e))
        raise


@router.get("/wildcard")
async def get_wildcard_standings(
    season: int = Query(default=2024, ge=1900, le=2030, description="MLB season year"),
    leagueId: Optional[str] = Query(
        default="103,104", 
        description="Comma-separated league IDs (103=AL, 104=NL)"
    )
):
    """
    Get wildcard standings and race.
    
    Returns wildcard standings showing teams competing for playoff spots.
    """
    logger.info("Fetching wildcard standings", season=season, leagueId=leagueId)
    
    params = {"season": season}
    if leagueId:
        params["leagueId"] = leagueId
    
    try:
        standings_data = await fetch_mlb_data("standings", params=params)
        
        # Extract wildcard information from standings
        wildcard_data = {}
        for record in standings_data.get("records", []):
            league = record.get("league", {})
            league_id = league.get("id")
            
            if league_id:
                wildcard_data[f"league_{league_id}"] = {
                    "league": league,
                    "wildcard_standings": record.get("teamRecords", [])
                }
        
        return {
            "season": season,
            "wildcard_standings": wildcard_data,
            "last_updated": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to fetch wildcard standings", season=season, error=str(e))
        raise
