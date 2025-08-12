"""
MLB Data Models for BigQuery

BigQuery data warehouse design with:
- Raw data tables (games, teams, players, standings)
- Partitioned by date for performance
- Clustered on team_id and game_date
- Create views for common analytics queries
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField, Table, Dataset

# BigQuery Schema Definitions
GAMES_SCHEMA = [
    SchemaField("game_id", "INTEGER", mode="REQUIRED"),
    SchemaField("game_date", "DATE", mode="REQUIRED"),
    SchemaField("game_time", "TIMESTAMP", mode="NULLABLE"),
    SchemaField("home_team_id", "INTEGER", mode="REQUIRED"),
    SchemaField("away_team_id", "INTEGER", mode="REQUIRED"),
    SchemaField("home_score", "INTEGER", mode="NULLABLE"),
    SchemaField("away_score", "INTEGER", mode="NULLABLE"),
    SchemaField("status", "STRING", mode="REQUIRED"),
    SchemaField("detailed_status", "STRING", mode="NULLABLE"),
    SchemaField("venue_id", "INTEGER", mode="NULLABLE"),
    SchemaField("venue_name", "STRING", mode="NULLABLE"),
    SchemaField("attendance", "INTEGER", mode="NULLABLE"),
    SchemaField("weather", "STRING", mode="NULLABLE"),
    SchemaField("wind", "STRING", mode="NULLABLE"),
    SchemaField("temperature", "FLOAT", mode="NULLABLE"),
    SchemaField("innings", "INTEGER", mode="NULLABLE"),
    SchemaField("is_final", "BOOLEAN", mode="REQUIRED"),
    SchemaField("is_live", "BOOLEAN", mode="REQUIRED"),
    SchemaField("raw_data", "JSON", mode="NULLABLE"),
    SchemaField("extraction_timestamp", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("partition_date", "DATE", mode="REQUIRED"),
]

TEAMS_SCHEMA = [
    SchemaField("team_id", "INTEGER", mode="REQUIRED"),
    SchemaField("name", "STRING", mode="REQUIRED"),
    SchemaField("abbreviation", "STRING", mode="REQUIRED"),
    SchemaField("city", "STRING", mode="REQUIRED"),
    SchemaField("division_id", "INTEGER", mode="REQUIRED"),
    SchemaField("division_name", "STRING", mode="REQUIRED"),
    SchemaField("league_id", "INTEGER", mode="REQUIRED"),
    SchemaField("league_name", "STRING", mode="REQUIRED"),
    SchemaField("venue_id", "INTEGER", mode="NULLABLE"),
    SchemaField("venue_name", "STRING", mode="NULLABLE"),
    SchemaField("is_active", "BOOLEAN", mode="REQUIRED"),
    SchemaField("season", "INTEGER", mode="REQUIRED"),
    SchemaField("raw_data", "JSON", mode="NULLABLE"),
    SchemaField("extraction_timestamp", "TIMESTAMP", mode="REQUIRED"),
]

PLAYERS_SCHEMA = [
    SchemaField("player_id", "INTEGER", mode="REQUIRED"),
    SchemaField("full_name", "STRING", mode="REQUIRED"),
    SchemaField("first_name", "STRING", mode="REQUIRED"),
    SchemaField("last_name", "STRING", mode="REQUIRED"),
    SchemaField("birth_date", "DATE", mode="NULLABLE"),
    SchemaField("birth_city", "STRING", mode="NULLABLE"),
    SchemaField("birth_state", "STRING", mode="NULLABLE"),
    SchemaField("birth_country", "STRING", mode="NULLABLE"),
    SchemaField("height", "STRING", mode="NULLABLE"),
    SchemaField("weight", "INTEGER", mode="NULLABLE"),
    SchemaField("bats", "STRING", mode="NULLABLE"),
    SchemaField("throws", "STRING", mode="NULLABLE"),
    SchemaField("primary_position", "STRING", mode="NULLABLE"),
    SchemaField("team_id", "INTEGER", mode="NULLABLE"),
    SchemaField("is_active", "BOOLEAN", mode="REQUIRED"),
    SchemaField("is_rookie", "BOOLEAN", mode="REQUIRED"),
    SchemaField("season", "INTEGER", mode="REQUIRED"),
    SchemaField("raw_data", "JSON", mode="NULLABLE"),
    SchemaField("extraction_timestamp", "TIMESTAMP", mode="REQUIRED"),
]

STANDINGS_SCHEMA = [
    SchemaField("team_id", "INTEGER", mode="REQUIRED"),
    SchemaField("season", "INTEGER", mode="REQUIRED"),
    SchemaField("division_id", "INTEGER", mode="REQUIRED"),
    SchemaField("division_name", "STRING", mode="REQUIRED"),
    SchemaField("league_id", "INTEGER", mode="REQUIRED"),
    SchemaField("league_name", "STRING", mode="REQUIRED"),
    SchemaField("wins", "INTEGER", mode="REQUIRED"),
    SchemaField("losses", "INTEGER", mode="REQUIRED"),
    SchemaField("win_percentage", "FLOAT", mode="REQUIRED"),
    SchemaField("games_back", "FLOAT", mode="REQUIRED"),
    SchemaField("runs_scored", "INTEGER", mode="REQUIRED"),
    SchemaField("runs_allowed", "INTEGER", mode="REQUIRED"),
    SchemaField("run_differential", "INTEGER", mode="REQUIRED"),
    SchemaField("games_played", "INTEGER", mode="REQUIRED"),
    SchemaField("streak", "STRING", mode="NULLABLE"),
    SchemaField("last_ten", "STRING", mode="NULLABLE"),
    SchemaField("home_wins", "INTEGER", mode="NULLABLE"),
    SchemaField("home_losses", "INTEGER", mode="NULLABLE"),
    SchemaField("away_wins", "INTEGER", mode="NULLABLE"),
    SchemaField("away_losses", "INTEGER", mode="NULLABLE"),
    SchemaField("standings_date", "DATE", mode="REQUIRED"),
    SchemaField("raw_data", "JSON", mode="NULLABLE"),
    SchemaField("extraction_timestamp", "TIMESTAMP", mode="REQUIRED"),
]

PLAYER_STATS_SCHEMA = [
    SchemaField("player_id", "INTEGER", mode="REQUIRED"),
    SchemaField("team_id", "INTEGER", mode="REQUIRED"),
    SchemaField("season", "INTEGER", mode="REQUIRED"),
    SchemaField("stat_type", "STRING", mode="REQUIRED"),  # hitting, pitching, fielding
    SchemaField("games_played", "INTEGER", mode="NULLABLE"),
    SchemaField("games_started", "INTEGER", mode="NULLABLE"),
    # Hitting stats
    SchemaField("at_bats", "INTEGER", mode="NULLABLE"),
    SchemaField("hits", "INTEGER", mode="NULLABLE"),
    SchemaField("doubles", "INTEGER", mode="NULLABLE"),
    SchemaField("triples", "INTEGER", mode="NULLABLE"),
    SchemaField("home_runs", "INTEGER", mode="NULLABLE"),
    SchemaField("runs_batted_in", "INTEGER", mode="NULLABLE"),
    SchemaField("runs", "INTEGER", mode="NULLABLE"),
    SchemaField("stolen_bases", "INTEGER", mode="NULLABLE"),
    SchemaField("caught_stealing", "INTEGER", mode="NULLABLE"),
    SchemaField("walks", "INTEGER", mode="NULLABLE"),
    SchemaField("strikeouts", "INTEGER", mode="NULLABLE"),
    SchemaField("batting_average", "FLOAT", mode="NULLABLE"),
    SchemaField("on_base_percentage", "FLOAT", mode="NULLABLE"),
    SchemaField("slugging_percentage", "FLOAT", mode="NULLABLE"),
    SchemaField("ops", "FLOAT", mode="NULLABLE"),
    # Pitching stats
    SchemaField("wins", "INTEGER", mode="NULLABLE"),
    SchemaField("losses", "INTEGER", mode="NULLABLE"),
    SchemaField("saves", "INTEGER", mode="NULLABLE"),
    SchemaField("innings_pitched", "FLOAT", mode="NULLABLE"),
    SchemaField("earned_runs", "INTEGER", mode="NULLABLE"),
    SchemaField("era", "FLOAT", mode="NULLABLE"),
    SchemaField("whip", "FLOAT", mode="NULLABLE"),
    SchemaField("quality_starts", "INTEGER", mode="NULLABLE"),
    SchemaField("complete_games", "INTEGER", mode="NULLABLE"),
    SchemaField("shutouts", "INTEGER", mode="NULLABLE"),
    # Fielding stats
    SchemaField("putouts", "INTEGER", mode="NULLABLE"),
    SchemaField("assists", "INTEGER", mode="NULLABLE"),
    SchemaField("errors", "INTEGER", mode="NULLABLE"),
    SchemaField("fielding_percentage", "FLOAT", mode="NULLABLE"),
    SchemaField("double_plays_turned", "INTEGER", mode="NULLABLE"),
    SchemaField("passed_balls", "INTEGER", mode="NULLABLE"),
    SchemaField("outfield_assists", "INTEGER", mode="NULLABLE"),
    SchemaField("raw_data", "JSON", mode="NULLABLE"),
    SchemaField("extraction_timestamp", "TIMESTAMP", mode="REQUIRED"),
]

GAME_EVENTS_SCHEMA = [
    SchemaField("game_id", "INTEGER", mode="REQUIRED"),
    SchemaField("event_id", "STRING", mode="REQUIRED"),
    SchemaField("inning", "INTEGER", mode="REQUIRED"),
    SchemaField("inning_half", "STRING", mode="REQUIRED"),  # top, bottom
    SchemaField("event_type", "STRING", mode="REQUIRED"),
    SchemaField("description", "STRING", mode="NULLABLE"),
    SchemaField("home_score", "INTEGER", mode="REQUIRED"),
    SchemaField("away_score", "INTEGER", mode="REQUIRED"),
    SchemaField("batter_id", "INTEGER", mode="NULLABLE"),
    SchemaField("pitcher_id", "INTEGER", mode="NULLABLE"),
    SchemaField("rbi", "INTEGER", mode="NULLABLE"),
    SchemaField("runs", "INTEGER", mode="NULLABLE"),
    SchemaField("hits", "INTEGER", mode="NULLABLE"),
    SchemaField("errors", "INTEGER", mode="NULLABLE"),
    SchemaField("event_timestamp", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("raw_data", "JSON", mode="NULLABLE"),
    SchemaField("extraction_timestamp", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("partition_date", "DATE", mode="REQUIRED"),
]


class BigQueryDataWarehouse:
    """BigQuery data warehouse manager for MLB analytics."""
    
    def __init__(self, project_id: str, dataset_id: str = "mlb_analytics"):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)
        self.dataset_ref = f"{project_id}.{dataset_id}"
        
    def create_dataset(self) -> Dataset:
        """Create the MLB analytics dataset."""
        dataset = bigquery.Dataset(self.dataset_ref)
        dataset.location = "US"
        dataset.description = "MLB Analytics Data Warehouse"
        
        try:
            dataset = self.client.create_dataset(dataset, exists_ok=True)
            print(f"Dataset {self.dataset_ref} created successfully")
            return dataset
        except Exception as e:
            print(f"Error creating dataset: {e}")
            raise
    
    def create_games_table(self) -> Table:
        """Create the games table with partitioning and clustering."""
        table_id = f"{self.dataset_ref}.games"
        table = bigquery.Table(table_id, schema=GAMES_SCHEMA)
        
        # Configure partitioning and clustering
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="partition_date"
        )
        table.clustering_fields = ["home_team_id", "away_team_id"]
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"Table {table_id} created successfully")
            return table
        except Exception as e:
            print(f"Error creating games table: {e}")
            raise
    
    def create_teams_table(self) -> Table:
        """Create the teams table."""
        table_id = f"{self.dataset_ref}.teams"
        table = bigquery.Table(table_id, schema=TEAMS_SCHEMA)
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"Table {table_id} created successfully")
            return table
        except Exception as e:
            print(f"Error creating teams table: {e}")
            raise
    
    def create_players_table(self) -> Table:
        """Create the players table."""
        table_id = f"{self.dataset_ref}.players"
        table = bigquery.Table(table_id, schema=PLAYERS_SCHEMA)
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"Table {table_id} created successfully")
            return table
        except Exception as e:
            print(f"Error creating players table: {e}")
            raise
    
    def create_standings_table(self) -> Table:
        """Create the standings table."""
        table_id = f"{self.dataset_ref}.standings"
        table = bigquery.Table(table_id, schema=STANDINGS_SCHEMA)
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"Table {table_id} created successfully")
            return table
        except Exception as e:
            print(f"Error creating standings table: {e}")
            raise
    
    def create_player_stats_table(self) -> Table:
        """Create the player stats table."""
        table_id = f"{self.dataset_ref}.player_stats"
        table = bigquery.Table(table_id, schema=PLAYER_STATS_SCHEMA)
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"Table {table_id} created successfully")
            return table
        except Exception as e:
            print(f"Error creating player stats table: {e}")
            raise
    
    def create_game_events_table(self) -> Table:
        """Create the game events table with partitioning."""
        table_id = f"{self.dataset_ref}.game_events"
        table = bigquery.Table(table_id, schema=GAME_EVENTS_SCHEMA)
        
        # Configure partitioning
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="partition_date"
        )
        table.clustering_fields = ["game_id", "inning"]
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"Table {table_id} created successfully")
            return table
        except Exception as e:
            print(f"Error creating game events table: {e}")
            raise
    
    def create_analytics_views(self):
        """Create common analytics views."""
        views = {
            "daily_standings": """
                SELECT 
                    team_id,
                    season,
                    division_name,
                    league_name,
                    wins,
                    losses,
                    win_percentage,
                    games_back,
                    run_differential,
                    standings_date
                FROM `{project_id}.{dataset_id}.standings`
                WHERE standings_date = CURRENT_DATE()
                ORDER BY league_name, division_name, games_back
            """,
            
            "recent_games": """
                SELECT 
                    game_id,
                    game_date,
                    home_team_id,
                    away_team_id,
                    home_score,
                    away_score,
                    status,
                    venue_name
                FROM `{project_id}.{dataset_id}.games`
                WHERE game_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                ORDER BY game_date DESC, game_time DESC
            """,
            
            "player_performance": """
                SELECT 
                    p.player_id,
                    p.full_name,
                    p.team_id,
                    ps.season,
                    ps.stat_type,
                    ps.games_played,
                    ps.batting_average,
                    ps.home_runs,
                    ps.runs_batted_in,
                    ps.ops,
                    ps.wins,
                    ps.losses,
                    ps.era,
                    ps.whip
                FROM `{project_id}.{dataset_id}.players` p
                JOIN `{project_id}.{dataset_id}.player_stats` ps
                    ON p.player_id = ps.player_id
                    AND p.season = ps.season
                WHERE ps.season = EXTRACT(YEAR FROM CURRENT_DATE())
                ORDER BY ps.stat_type, ps.games_played DESC
            """,
            
            "team_performance": """
                SELECT 
                    t.team_id,
                    t.name,
                    t.division_name,
                    t.league_name,
                    s.wins,
                    s.losses,
                    s.win_percentage,
                    s.run_differential,
                    s.standings_date
                FROM `{project_id}.{dataset_id}.teams` t
                JOIN `{project_id}.{dataset_id}.standings` s
                    ON t.team_id = s.team_id
                    AND t.season = s.season
                WHERE s.standings_date = CURRENT_DATE()
                ORDER BY s.win_percentage DESC
            """
        }
        
        for view_name, query in views.items():
            view_id = f"{self.dataset_ref}.{view_name}"
            view = bigquery.Table(view_id)
            view.view_query = query.format(
                project_id=self.project_id,
                dataset_id=self.dataset_id
            )
            
            try:
                view = self.client.create_table(view, exists_ok=True)
                print(f"View {view_id} created successfully")
            except Exception as e:
                print(f"Error creating view {view_name}: {e}")
    
    def setup_data_warehouse(self):
        """Set up the complete data warehouse."""
        print("Setting up MLB Analytics Data Warehouse...")
        
        # Create dataset
        self.create_dataset()
        
        # Create tables
        self.create_games_table()
        self.create_teams_table()
        self.create_players_table()
        self.create_standings_table()
        self.create_player_stats_table()
        self.create_game_events_table()
        
        # Create views
        self.create_analytics_views()
        
        print("Data warehouse setup completed successfully!")


# Data transformation helpers
def transform_game_data(raw_game_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw game data to BigQuery schema."""
    game = raw_game_data.get("gameData", {})
    live_data = raw_game_data.get("liveData", {})
    
    return {
        "game_id": game.get("game", {}).get("pk"),
        "game_date": game.get("datetime", {}).get("officialDate"),
        "game_time": game.get("datetime", {}).get("officialTime"),
        "home_team_id": game.get("teams", {}).get("home", {}).get("id"),
        "away_team_id": game.get("teams", {}).get("away", {}).get("id"),
        "home_score": live_data.get("boxscore", {}).get("teams", {}).get("home", {}).get("teamStats", {}).get("batting", {}).get("runs"),
        "away_score": live_data.get("boxscore", {}).get("teams", {}).get("away", {}).get("teamStats", {}).get("batting", {}).get("runs"),
        "status": game.get("status", {}).get("statusCode"),
        "detailed_status": game.get("status", {}).get("detailedState"),
        "venue_id": game.get("venue", {}).get("id"),
        "venue_name": game.get("venue", {}).get("name"),
        "attendance": game.get("gameInfo", {}).get("attendance"),
        "weather": game.get("gameInfo", {}).get("weather"),
        "wind": game.get("gameInfo", {}).get("wind"),
        "temperature": game.get("gameInfo", {}).get("temperature"),
        "innings": live_data.get("boxscore", {}).get("info", [{}])[0].get("inningState"),
        "is_final": game.get("status", {}).get("statusCode") == "F",
        "is_live": game.get("status", {}).get("detailedState") == "In Progress",
        "raw_data": raw_game_data,
        "extraction_timestamp": datetime.now().isoformat(),
        "partition_date": game.get("datetime", {}).get("officialDate"),
    }


def transform_team_data(raw_team_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw team data to BigQuery schema."""
    team = raw_team_data.get("teams", [{}])[0]
    
    return {
        "team_id": team.get("id"),
        "name": team.get("name"),
        "abbreviation": team.get("abbreviation"),
        "city": team.get("locationName"),
        "division_id": team.get("division", {}).get("id"),
        "division_name": team.get("division", {}).get("name"),
        "league_id": team.get("league", {}).get("id"),
        "league_name": team.get("league", {}).get("name"),
        "venue_id": team.get("venue", {}).get("id"),
        "venue_name": team.get("venue", {}).get("name"),
        "is_active": team.get("active", True),
        "season": datetime.now().year,
        "raw_data": raw_team_data,
        "extraction_timestamp": datetime.now().isoformat(),
    }
