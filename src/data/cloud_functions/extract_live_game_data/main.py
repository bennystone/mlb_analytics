"""
Cloud Function: Extract Live Game Data

Extracts live MLB game data and loads it into BigQuery.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
import sys
sys.path.append('/workspace')

from src.data.extractors import MLBAPIExtractor
from src.data.loaders import BigQueryDataLoader


def extract_live_game_data_cloud_function(request):
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
        
        # Get environment variables
        project_id = os.getenv('PROJECT_ID', 'your-project-id')
        dataset_id = os.getenv('DATASET_ID', 'mlb_analytics')
        
        # Extract live data
        async def _extract():
            async with MLBAPIExtractor() as extractor:
                game_details = await extractor.fetch_game_details(game_id)
                gumbo_data = await extractor.fetch_gumbo_live_feed(game_id)
                
                return {
                    'game_id': game_id,
                    'game_details': game_details,
                    'gumbo_live_feed': gumbo_data,
                    'timestamp': datetime.now().isoformat()
                }
        
        extraction_data = asyncio.run(_extract())
        
        # Load data to BigQuery
        loader = BigQueryDataLoader(project_id, dataset_id)
        
        # Transform and load game data
        if extraction_data['game_details']:
            game_data = [extraction_data['game_details']]
            load_result = loader.load_games_data(game_data)
        else:
            load_result = {'status': 'skipped', 'reason': 'no_game_data'}
        
        return {
            'status': 'success',
            'game_id': game_id,
            'extraction_data': extraction_data,
            'load_result': load_result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500
