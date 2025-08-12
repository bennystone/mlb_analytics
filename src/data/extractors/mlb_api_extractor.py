"""
MLB API Data Extractor

Cloud Functions for API data extraction with:
- Fetch daily schedule, games, standings
- Handle GUMBO live feed for in-progress games
- Implement exponential backoff retry logic
- Parse JSON responses into structured data
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import httpx
import structlog
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

# Configure structured logging
logger = structlog.get_logger()

class MLBAPIExtractor:
    """MLB API data extractor with retry logic and structured data parsing."""
    
    def __init__(self, base_url: str = "https://statsapi.mlb.com/api/v1"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.max_retries = 5
        self.base_delay = 1.0
        self.max_delay = 60.0
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    async def _make_request_with_retry(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with exponential backoff retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            retries: Number of retries (defaults to self.max_retries)
            
        Returns:
            JSON response data
            
        Raises:
            httpx.HTTPError: If all retries fail
        """
        if retries is None:
            retries = self.max_retries
            
        url = urljoin(self.base_url, endpoint)
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                logger.info(
                    "Making MLB API request",
                    url=url,
                    params=params,
                    attempt=attempt + 1,
                    max_attempts=retries + 1
                )
                
                response = await self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                logger.info(
                    "MLB API request successful",
                    url=url,
                    status_code=response.status_code,
                    data_size=len(str(data))
                )
                
                return data
                
            except httpx.HTTPError as e:
                last_exception = e
                status_code = getattr(e.response, 'status_code', None)
                
                logger.warning(
                    "MLB API request failed",
                    url=url,
                    attempt=attempt + 1,
                    status_code=status_code,
                    error=str(e)
                )
                
                # Don't retry on client errors (4xx)
                if status_code and 400 <= status_code < 500:
                    logger.error("Client error, not retrying", status_code=status_code)
                    raise e
                
                if attempt < retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                last_exception = e
                logger.error(
                    "Unexpected error in MLB API request",
                    url=url,
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                if attempt < retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
        
        logger.error(
            "All retries exhausted for MLB API request",
            url=url,
            total_attempts=retries + 1
        )
        raise last_exception
    
    async def fetch_daily_schedule(self, date: datetime) -> Dict[str, Any]:
        """
        Fetch daily game schedule.
        
        Args:
            date: Date to fetch schedule for
            
        Returns:
            Schedule data
        """
        date_str = date.strftime("%Y-%m-%d")
        params = {"date": date_str}
        
        logger.info("Fetching daily schedule", date=date_str)
        return await self._make_request_with_retry("schedule", params=params)
    
    async def fetch_game_details(self, game_id: int) -> Dict[str, Any]:
        """
        Fetch detailed game information.
        
        Args:
            game_id: MLB game ID
            
        Returns:
            Game details
        """
        logger.info("Fetching game details", game_id=game_id)
        return await self._make_request_with_retry(f"game/{game_id}/feed/live")
    
    async def fetch_gumbo_live_feed(self, game_id: int) -> Dict[str, Any]:
        """
        Fetch GUMBO live feed for in-progress games.
        
        Args:
            game_id: MLB game ID
            
        Returns:
            Live feed data
        """
        logger.info("Fetching GUMBO live feed", game_id=game_id)
        return await self._make_request_with_retry(f"game/{game_id}/feed/live/diffPatch")
    
    async def fetch_standings(self, season: int = None) -> Dict[str, Any]:
        """
        Fetch current standings.
        
        Args:
            season: MLB season year (defaults to current year)
            
        Returns:
            Standings data
        """
        if season is None:
            season = datetime.now().year
            
        params = {"season": season}
        logger.info("Fetching standings", season=season)
        return await self._make_request_with_retry("standings", params=params)
    
    async def fetch_team_stats(self, team_id: int, season: int = None) -> Dict[str, Any]:
        """
        Fetch team statistics.
        
        Args:
            team_id: MLB team ID
            season: MLB season year (defaults to current year)
            
        Returns:
            Team stats data
        """
        if season is None:
            season = datetime.now().year
            
        params = {"teamId": team_id, "season": season}
        logger.info("Fetching team stats", team_id=team_id, season=season)
        return await self._make_request_with_retry("teams/stats", params=params)
    
    async def fetch_player_stats(
        self, 
        player_id: int, 
        season: int = None,
        stat_type: str = "hitting"
    ) -> Dict[str, Any]:
        """
        Fetch player statistics.
        
        Args:
            player_id: MLB player ID
            season: MLB season year (defaults to current year)
            stat_type: Type of stats (hitting, pitching, fielding)
            
        Returns:
            Player stats data
        """
        if season is None:
            season = datetime.now().year
            
        params = {
            "personId": player_id,
            "season": season,
            "group": stat_type
        }
        
        logger.info(
            "Fetching player stats",
            player_id=player_id,
            season=season,
            stat_type=stat_type
        )
        return await self._make_request_with_retry("people/stats", params=params)


class DataExtractionOrchestrator:
    """Orchestrates data extraction for the entire pipeline."""
    
    def __init__(self, extractor: MLBAPIExtractor):
        self.extractor = extractor
        
    async def extract_daily_data(self, date: datetime) -> Dict[str, Any]:
        """
        Extract all daily data for a given date.
        
        Args:
            date: Date to extract data for
            
        Returns:
            Dictionary containing all extracted data
        """
        logger.info("Starting daily data extraction", date=date.strftime("%Y-%m-%d"))
        
        try:
            # Extract schedule
            schedule_data = await self.extractor.fetch_daily_schedule(date)
            
            # Extract standings
            standings_data = await self.extractor.fetch_standings(date.year)
            
            # Extract game details for all games
            games_data = []
            if schedule_data.get("dates"):
                for date_data in schedule_data["dates"]:
                    for game in date_data.get("games", []):
                        game_id = game.get("gamePk")
                        if game_id:
                            try:
                                game_details = await self.extractor.fetch_game_details(game_id)
                                games_data.append(game_details)
                                
                                # If game is live, also fetch GUMBO feed
                                if game.get("status", {}).get("detailedState") == "In Progress":
                                    try:
                                        gumbo_data = await self.extractor.fetch_gumbo_live_feed(game_id)
                                        game_details["gumbo_live_feed"] = gumbo_data
                                    except Exception as e:
                                        logger.warning(
                                            "Failed to fetch GUMBO data",
                                            game_id=game_id,
                                            error=str(e)
                                        )
                                        
                            except Exception as e:
                                logger.error(
                                    "Failed to fetch game details",
                                    game_id=game_id,
                                    error=str(e)
                                )
            
            extraction_result = {
                "extraction_date": date.isoformat(),
                "schedule": schedule_data,
                "standings": standings_data,
                "games": games_data,
                "metadata": {
                    "total_games": len(games_data),
                    "extraction_timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(
                "Daily data extraction completed",
                date=date.strftime("%Y-%m-%d"),
                total_games=len(games_data)
            )
            
            return extraction_result
            
        except Exception as e:
            logger.error(
                "Daily data extraction failed",
                date=date.strftime("%Y-%m-%d"),
                error=str(e)
            )
            raise


# Cloud Function entry points
async def extract_daily_schedule_cloud_function(request):
    """Cloud Function to extract daily schedule data."""
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        date_str = request_json.get('date') if request_json else None
        
        if date_str:
            date = datetime.fromisoformat(date_str)
        else:
            date = datetime.now()
        
        # Extract data
        async with MLBAPIExtractor() as extractor:
            orchestrator = DataExtractionOrchestrator(extractor)
            result = await orchestrator.extract_daily_data(date)
        
        return {
            'status': 'success',
            'data': result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Cloud function failed", error=str(e))
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500


async def extract_live_game_data_cloud_function(request):
    """Cloud Function to extract live game data."""
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        game_id = request_json.get('game_id') if request_json else None
        
        if not game_id:
            return {
                'status': 'error',
                'error': 'game_id parameter required',
                'timestamp': datetime.now().isoformat()
            }, 400
        
        # Extract live data
        async with MLBAPIExtractor() as extractor:
            game_details = await extractor.fetch_game_details(game_id)
            gumbo_data = await extractor.fetch_gumbo_live_feed(game_id)
            
            result = {
                'game_id': game_id,
                'game_details': game_details,
                'gumbo_live_feed': gumbo_data,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'status': 'success',
            'data': result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Live game extraction failed", error=str(e))
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500
