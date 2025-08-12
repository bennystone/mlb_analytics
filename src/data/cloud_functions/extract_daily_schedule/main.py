"""
Cloud Function: Extract Daily Schedule

Extracts daily MLB schedule data and loads it into BigQuery.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
import sys
sys.path.append('/workspace')

from src.data.extractors import MLBAPIExtractor, DataExtractionOrchestrator
from src.data.loaders import BigQueryDataLoader


def extract_daily_schedule_cloud_function(request):
    """Cloud Function to extract daily schedule data."""
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        date_str = request_json.get('date') if request_json else None
        
        if date_str:
            date = datetime.fromisoformat(date_str)
        else:
            date = datetime.now()
        
        # Get environment variables
        project_id = os.getenv('PROJECT_ID', 'your-project-id')
        dataset_id = os.getenv('DATASET_ID', 'mlb_analytics')
        
        # Extract data
        async def _extract():
            async with MLBAPIExtractor() as extractor:
                orchestrator = DataExtractionOrchestrator(extractor)
                result = await orchestrator.extract_daily_data(date)
                return result
        
        extraction_data = asyncio.run(_extract())
        
        # Load data to BigQuery
        loader = BigQueryDataLoader(project_id, dataset_id)
        load_result = loader.load_daily_extraction_data(extraction_data)
        
        return {
            'status': 'success',
            'date': date.isoformat(),
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
