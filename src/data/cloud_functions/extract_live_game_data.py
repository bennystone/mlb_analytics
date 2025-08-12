"""
Cloud Function for Live MLB Game Data Extraction

This function extracts live MLB game data and loads it into BigQuery.
Simplified version for 1st gen Cloud Functions.
"""

import functions_framework
import os
import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_live_game_data() -> List[Dict[str, Any]]:
    """Fetch live MLB game data from the API."""
    try:
        # Get today's games
        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {
            'sportId': 1,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'hydrate': 'game(content(media(epg)))'
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            schedule_data = response.json()
        
        # Get live data for games that are in progress
        live_games = []
        dates = schedule_data.get('dates', [])
        
        for date_data in dates:
            games = date_data.get('games', [])
            for game in games:
                if game.get('status', {}).get('detailedState') == 'In Progress':
                    game_id = game.get('gamePk')
                    if game_id:
                        # Fetch detailed game data
                        game_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/feed/live"
                        try:
                            game_response = client.get(game_url, timeout=30.0)
                            game_response.raise_for_status()
                            live_games.append(game_response.json())
                        except Exception as e:
                            logger.warning(f"Could not fetch live data for game {game_id}: {e}")
        
        return live_games
        
    except Exception as e:
        logger.error(f"Error fetching live game data: {e}")
        return []

def transform_game_data(raw_game_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw game data into BigQuery format."""
    try:
        game = raw_game_data.get('gameData', {})
        live_data = raw_game_data.get('liveData', {})
        
        # Extract basic game information
        game_info = game.get('game', {})
        teams = game.get('teams', {})
        venue = game.get('venue', {})
        
        # Extract scoring information
        scoring = live_data.get('plays', {}).get('scoringPlays', [])
        
        transformed_data = {
            'game_id': game_info.get('pk'),
            'game_date': game_info.get('officialDate'),
            'game_type': game_info.get('type'),
            'season': game_info.get('season'),
            'status': game_info.get('status', {}).get('detailedState'),
            'venue_id': venue.get('id'),
            'venue_name': venue.get('name'),
            'home_team_id': teams.get('home', {}).get('id'),
            'away_team_id': teams.get('away', {}).get('id'),
            'home_score': live_data.get('boxscore', {}).get('teams', {}).get('home', {}).get('teamStats', {}).get('batting', {}).get('runs', 0),
            'away_score': live_data.get('boxscore', {}).get('teams', {}).get('away', {}).get('teamStats', {}).get('batting', {}).get('runs', 0),
            'scoring_plays_count': len(scoring),
            'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
            'partition_date': game_info.get('officialDate')
        }
        
        return transformed_data
        
    except Exception as e:
        logger.error(f"Error transforming game data: {e}")
        return {}

def load_to_bigquery(data: List[Dict[str, Any]], project_id: str, dataset_id: str):
    """Load data to BigQuery."""
    try:
        client = bigquery.Client(project=project_id)
        table_id = f"{project_id}.{dataset_id}.games"
        
        # Load data to BigQuery
        errors = client.insert_rows_json(table_id, data)
        if errors:
            logger.error(f"Errors inserting rows: {errors}")
        else:
            logger.info(f"Successfully loaded {len(data)} records to BigQuery")
            
    except Exception as e:
        logger.error(f"Error loading to BigQuery: {e}")
        raise

@functions_framework.http
def extract_live_game_data_cloud_function(request):
    """
    Cloud Function entry point for live MLB game data extraction.
    """
    try:
        # Get environment variables
        project_id = os.environ.get('PROJECT_ID')
        dataset_id = os.environ.get('DATASET_ID')
        
        if not project_id or not dataset_id:
            raise ValueError("PROJECT_ID and DATASET_ID environment variables must be set")
        
        logger.info(f"Starting live game data extraction for project: {project_id}, dataset: {dataset_id}")
        
        # Extract live game data
        logger.info("Fetching live game data from MLB API...")
        live_data = fetch_live_game_data()
        
        if not live_data:
            logger.warning("No live game data retrieved")
            return json.dumps({
                'status': 'warning',
                'message': 'No live game data retrieved',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        
        # Transform data
        logger.info("Transforming live game data...")
        transformed_games = []
        
        for game_data in live_data:
            transformed_game = transform_game_data(game_data)
            if transformed_game:
                transformed_games.append(transformed_game)
        
        if not transformed_games:
            logger.warning("No transformed game data")
            return json.dumps({
                'status': 'warning',
                'message': 'No transformed game data',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        
        # Load to BigQuery
        logger.info(f"Loading {len(transformed_games)} game records to BigQuery...")
        load_to_bigquery(transformed_games, project_id, dataset_id)
        
        logger.info("Live game data extraction completed successfully")
        
        return json.dumps({
            'status': 'success',
            'message': f'Successfully extracted and loaded {len(transformed_games)} game records',
            'records_processed': len(transformed_games),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in live game data extraction: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

# For local testing
if __name__ == "__main__":
    # Simulate a request for local testing
    class MockRequest:
        def __init__(self):
            self.method = 'GET'
            self.headers = {}
    
    response = extract_live_game_data_cloud_function(MockRequest())
    print(response)
