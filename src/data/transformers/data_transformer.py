"""
Data Transformers for MLB Analytics Pipeline

This module contains data transformation logic for converting raw MLB API data
into structured formats suitable for BigQuery storage and analytics.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class MLBDataTransformer:
    """Transforms raw MLB API data into structured formats."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def transform_game_data(self, raw_game_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw game data from MLB API into BigQuery format.
        
        Args:
            raw_game_data: Raw game data from MLB API
            
        Returns:
            Transformed game data ready for BigQuery
        """
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
                'raw_data': raw_game_data
            }
            
            return transformed_data
            
        except Exception as e:
            self.logger.error(f"Error transforming game data: {e}")
            return {}
    
    def transform_standings_data(self, raw_standings_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform raw standings data from MLB API into BigQuery format.
        
        Args:
            raw_standings_data: Raw standings data from MLB API
            
        Returns:
            List of transformed team standings ready for BigQuery
        """
        try:
            records = raw_standings_data.get('records', [])
            transformed_standings = []
            
            for record in records:
                division = record.get('division', {})
                teams = record.get('teamRecords', [])
                
                for team in teams:
                    team_info = team.get('team', {})
                    stats = team.get('leagueRecord', {})
                    
                    transformed_team = {
                        'team_id': team_info.get('id'),
                        'team_name': team_info.get('name'),
                        'division_id': division.get('id'),
                        'division_name': division.get('name'),
                        'league_id': team.get('league', {}).get('id'),
                        'league_name': team.get('league', {}).get('name'),
                        'wins': stats.get('wins', 0),
                        'losses': stats.get('losses', 0),
                        'win_percentage': team.get('winPercentage', 0.0),
                        'games_back': team.get('gamesBack', 0.0),
                        'wild_card_games_back': team.get('wildCardGamesBack', 0.0),
                        'season': raw_standings_data.get('season', datetime.now().year),
                        'extraction_timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    
                    transformed_standings.append(transformed_team)
            
            return transformed_standings
            
        except Exception as e:
            self.logger.error(f"Error transforming standings data: {e}")
            return []
    
    def transform_player_stats(self, raw_player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw player statistics from MLB API into BigQuery format.
        
        Args:
            raw_player_data: Raw player data from MLB API
            
        Returns:
            Transformed player statistics ready for BigQuery
        """
        try:
            player = raw_player_data.get('people', [{}])[0]
            stats = player.get('stats', [])
            
            # Extract current season stats
            current_stats = {}
            for stat in stats:
                if stat.get('type', {}).get('displayName') == 'hitting':
                    splits = stat.get('splits', [])
                    for split in splits:
                        if split.get('season') == str(datetime.now().year):
                            current_stats = split.get('stat', {})
                            break
            
            transformed_data = {
                'player_id': player.get('id'),
                'player_name': f"{player.get('firstName', '')} {player.get('lastName', '')}".strip(),
                'team_id': player.get('currentTeam', {}).get('id'),
                'position': player.get('primaryPosition', {}).get('abbreviation'),
                'season': datetime.now().year,
                'games_played': current_stats.get('gamesPlayed', 0),
                'at_bats': current_stats.get('atBats', 0),
                'hits': current_stats.get('hits', 0),
                'home_runs': current_stats.get('homeRuns', 0),
                'runs_batted_in': current_stats.get('rbi', 0),
                'stolen_bases': current_stats.get('stolenBases', 0),
                'batting_average': current_stats.get('avg', 0.0),
                'on_base_percentage': current_stats.get('obp', 0.0),
                'slugging_percentage': current_stats.get('slg', 0.0),
                'ops': current_stats.get('ops', 0.0),
                'extraction_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            return transformed_data
            
        except Exception as e:
            self.logger.error(f"Error transforming player stats: {e}")
            return {}
    
    def transform_schedule_data(self, raw_schedule_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform raw schedule data from MLB API into BigQuery format.
        
        Args:
            raw_schedule_data: Raw schedule data from MLB API
            
        Returns:
            List of transformed schedule entries ready for BigQuery
        """
        try:
            dates = raw_schedule_data.get('dates', [])
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
                        'extraction_timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    
                    transformed_schedule.append(transformed_game)
            
            return transformed_schedule
            
        except Exception as e:
            self.logger.error(f"Error transforming schedule data: {e}")
            return []


# Create a global instance for easy import
data_transformer = MLBDataTransformer()
