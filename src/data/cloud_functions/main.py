"""
MLB Analytics Cloud Functions - Main Entry Point

This file serves as the main entry point for Cloud Functions deployment.
It imports and exposes the cloud function entry points for data extraction.
"""

from .extract_daily_schedule import extract_daily_schedule_cloud_function
from .extract_live_game_data import extract_live_game_data_cloud_function

# Export the cloud functions for deployment
__all__ = [
    'extract_daily_schedule_cloud_function',
    'extract_live_game_data_cloud_function'
]
