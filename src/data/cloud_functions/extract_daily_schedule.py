"""
Cloud Function for Daily MLB Schedule Extraction

This function extracts daily MLB schedule data and loads it into BigQuery.
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

def fetch_daily_schedule() -> Dict[str, Any]:
    """Fetch daily MLB schedule from the API."""
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {
            'sportId': 1,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'hydrate': 'game(content(media(epg)))'
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching daily schedule: {e}")
        return {}

def transform_schedule_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Transform raw schedule data into BigQuery format."""
    try:
        dates = raw_data.get('dates', [])
        transformed_schedule = []
        
        for date_data in dates:
            date = date_data.get('date')
            games = date_data.get('games', [])
            
            for game in games:
                teams = game.get('teams', {})
                venue = game.get('venue', {})
                
                transformed_game = {
                    'game_id': game.get('gamePk'),
                    'game_date': date,
                    'game_type': game.get('gameType'),
                    'season': game.get('season'),
                    'status': game.get('status', {}).get('detailedState'),
                    'venue_id': venue.get('id'),
                    'venue_name': venue.get('name'),
                    'home_team_id': teams.get('home', {}).get('team', {}).get('id'),
                    'away_team_id': teams.get('away', {}).get('team', {}).get('id'),
                    'home_team_name': teams.get('home', {}).get('team', {}).get('name'),
                    'away_team_name': teams.get('away', {}).get('team', {}).get('name'),
                    'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
                    'partition_date': date
                }
                
                transformed_schedule.append(transformed_game)
        
        return transformed_schedule
        
    except Exception as e:
        logger.error(f"Error transforming schedule data: {e}")
        return []

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
def extract_daily_schedule_cloud_function(request):
    """
    Cloud Function entry point for daily MLB schedule extraction.
    """
    try:
        # Get environment variables
        project_id = os.environ.get('PROJECT_ID')
        dataset_id = os.environ.get('DATASET_ID')
        
        if not project_id or not dataset_id:
            raise ValueError("PROJECT_ID and DATASET_ID environment variables must be set")
        
        logger.info(f"Starting daily schedule extraction for project: {project_id}, dataset: {dataset_id}")
        
        # Extract daily schedule
        logger.info("Fetching daily schedule from MLB API...")
        schedule_data = fetch_daily_schedule()
        
        if not schedule_data:
            logger.warning("No schedule data retrieved")
            return json.dumps({
                'status': 'warning',
                'message': 'No schedule data retrieved',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        
        # Transform data
        logger.info("Transforming schedule data...")
        transformed_schedule = transform_schedule_data(schedule_data)
        
        if not transformed_schedule:
            logger.warning("No transformed schedule data")
            return json.dumps({
                'status': 'warning',
                'message': 'No transformed schedule data',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        
        # Load to BigQuery
        logger.info(f"Loading {len(transformed_schedule)} schedule records to BigQuery...")
        load_to_bigquery(transformed_schedule, project_id, dataset_id)
        
        logger.info("Daily schedule extraction completed successfully")
        
        return json.dumps({
            'status': 'success',
            'message': f'Successfully extracted and loaded {len(transformed_schedule)} schedule records',
            'records_processed': len(transformed_schedule),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in daily schedule extraction: {str(e)}")
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
    
    response = extract_daily_schedule_cloud_function(MockRequest())
    print(response)
