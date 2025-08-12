"""
BigQuery Data Loader

Loads extracted data into BigQuery data warehouse with:
- Batch loading for performance
- Error handling and retry logic
- Data validation before loading
- Monitoring and alerting
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from google.api_core import retry
import structlog

logger = structlog.get_logger()


class BigQueryDataLoader:
    """BigQuery data loader with error handling and monitoring."""
    
    def __init__(self, project_id: str, dataset_id: str = "mlb_analytics"):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)
        self.dataset_ref = f"{project_id}.{dataset_id}"
        
    def _get_table_ref(self, table_name: str) -> str:
        """Get full table reference."""
        return f"{self.dataset_ref}.{table_name}"
    
    def _validate_data_before_load(
        self, 
        data: List[Dict[str, Any]], 
        table_name: str
    ) -> List[Dict[str, Any]]:
        """
        Validate data before loading into BigQuery.
        
        Args:
            data: Data to validate
            table_name: Target table name
            
        Returns:
            Validated data
        """
        if not data:
            logger.warning("No data to load", table_name=table_name)
            return []
        
        validated_data = []
        errors = []
        
        for i, row in enumerate(data):
            try:
                # Basic validation - ensure required fields exist
                if table_name == "games" and not row.get("game_id"):
                    errors.append(f"Row {i}: Missing game_id")
                    continue
                elif table_name == "teams" and not row.get("team_id"):
                    errors.append(f"Row {i}: Missing team_id")
                    continue
                elif table_name == "players" and not row.get("player_id"):
                    errors.append(f"Row {i}: Missing player_id")
                    continue
                elif table_name == "standings" and not row.get("team_id"):
                    errors.append(f"Row {i}: Missing team_id")
                    continue
                
                # Ensure extraction_timestamp exists
                if "extraction_timestamp" not in row:
                    row["extraction_timestamp"] = datetime.now().isoformat()
                
                validated_data.append(row)
                
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")
        
        if errors:
            logger.warning(
                "Data validation errors found",
                table_name=table_name,
                total_rows=len(data),
                valid_rows=len(validated_data),
                error_count=len(errors),
                errors=errors[:10]  # Log first 10 errors
            )
        
        logger.info(
            "Data validation completed",
            table_name=table_name,
            total_rows=len(data),
            valid_rows=len(validated_data),
            error_count=len(errors)
        )
        
        return validated_data
    
    @retry.Retry(predicate=retry.if_transient_error)
    def load_data_to_table(
        self,
        data: List[Dict[str, Any]],
        table_name: str,
        write_disposition: str = "WRITE_APPEND",
        create_disposition: str = "CREATE_IF_NEEDED"
    ) -> Dict[str, Any]:
        """
        Load data to BigQuery table with retry logic.
        
        Args:
            data: Data to load
            table_name: Target table name
            write_disposition: Write disposition (WRITE_APPEND, WRITE_TRUNCATE, WRITE_EMPTY)
            create_disposition: Create disposition (CREATE_IF_NEEDED, CREATE_NEVER)
            
        Returns:
            Load job result
        """
        if not data:
            logger.warning("No data to load", table_name=table_name)
            return {"status": "skipped", "reason": "no_data"}
        
        # Validate data
        validated_data = self._validate_data_before_load(data, table_name)
        
        if not validated_data:
            logger.warning("No valid data to load after validation", table_name=table_name)
            return {"status": "skipped", "reason": "no_valid_data"}
        
        table_ref = self._get_table_ref(table_name)
        
        try:
            # Configure job
            job_config = bigquery.LoadJobConfig(
                write_disposition=write_disposition,
                create_disposition=create_disposition,
                autodetect=False,  # We have defined schemas
                ignore_unknown_values=True,
                max_bad_records=10
            )
            
            # Convert data to JSON strings for loading
            json_data = [json.dumps(row) for row in validated_data]
            
            # Create load job
            job = self.client.load_table_from_json(
                json_data,
                table_ref,
                job_config=job_config
            )
            
            logger.info(
                "Starting BigQuery load job",
                table_name=table_name,
                row_count=len(validated_data),
                job_id=job.job_id
            )
            
            # Wait for job to complete
            job.result()  # Waits for job to complete
            
            # Get job statistics
            destination_table = self.client.get_table(table_ref)
            
            result = {
                "status": "success",
                "table_name": table_name,
                "rows_loaded": len(validated_data),
                "total_rows": destination_table.num_rows,
                "job_id": job.job_id,
                "load_timestamp": datetime.now().isoformat()
            }
            
            logger.info(
                "BigQuery load job completed successfully",
                **result
            )
            
            return result
            
        except GoogleCloudError as e:
            logger.error(
                "BigQuery load job failed",
                table_name=table_name,
                error=str(e),
                job_id=getattr(job, 'job_id', None)
            )
            raise
    
    def load_games_data(self, games_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load games data to BigQuery."""
        logger.info("Loading games data", count=len(games_data))
        return self.load_data_to_table(games_data, "games")
    
    def load_teams_data(self, teams_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load teams data to BigQuery."""
        logger.info("Loading teams data", count=len(teams_data))
        return self.load_data_to_table(teams_data, "teams")
    
    def load_players_data(self, players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load players data to BigQuery."""
        logger.info("Loading players data", count=len(players_data))
        return self.load_data_to_table(players_data, "players")
    
    def load_standings_data(self, standings_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load standings data to BigQuery."""
        logger.info("Loading standings data", count=len(standings_data))
        return self.load_data_to_table(standings_data, "standings")
    
    def load_player_stats_data(self, player_stats_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load player stats data to BigQuery."""
        logger.info("Loading player stats data", count=len(player_stats_data))
        return self.load_data_to_table(player_stats_data, "player_stats")
    
    def load_game_events_data(self, game_events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load game events data to BigQuery."""
        logger.info("Loading game events data", count=len(game_events_data))
        return self.load_data_to_table(game_events_data, "game_events")
    
    def load_daily_extraction_data(self, extraction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load complete daily extraction data to BigQuery.
        
        Args:
            extraction_data: Complete daily extraction data
            
        Returns:
            Summary of all load operations
        """
        logger.info("Loading daily extraction data")
        
        results = {}
        
        try:
            # Load games data
            if "games" in extraction_data and extraction_data["games"]:
                games_data = []
                for game in extraction_data["games"]:
                    # Transform game data if needed
                    if isinstance(game, dict):
                        games_data.append(game)
                
                if games_data:
                    results["games"] = self.load_games_data(games_data)
            
            # Load standings data
            if "standings" in extraction_data and extraction_data["standings"]:
                standings_data = []
                for record in extraction_data["standings"].get("records", []):
                    for team_record in record.get("teamRecords", []):
                        standings_data.append(team_record)
                
                if standings_data:
                    results["standings"] = self.load_standings_data(standings_data)
            
            # Load schedule data (if needed)
            if "schedule" in extraction_data and extraction_data["schedule"]:
                schedule_data = []
                for date_data in extraction_data["schedule"].get("dates", []):
                    for game in date_data.get("games", []):
                        schedule_data.append(game)
                
                if schedule_data:
                    results["schedule"] = self.load_data_to_table(schedule_data, "games")
            
            logger.info(
                "Daily extraction data loading completed",
                results=results
            )
            
            return {
                "status": "success",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "Daily extraction data loading failed",
                error=str(e)
            )
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a BigQuery table."""
        try:
            table_ref = self._get_table_ref(table_name)
            table = self.client.get_table(table_ref)
            
            return {
                "table_name": table_name,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None,
                "schema": [field.name for field in table.schema]
            }
        except Exception as e:
            logger.error("Failed to get table info", table_name=table_name, error=str(e))
            raise
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Get information about the dataset."""
        try:
            dataset = self.client.get_dataset(self.dataset_ref)
            tables = list(self.client.list_tables(dataset))
            
            return {
                "dataset_id": self.dataset_id,
                "project_id": self.project_id,
                "location": dataset.location,
                "created": dataset.created.isoformat() if dataset.created else None,
                "modified": dataset.modified.isoformat() if dataset.modified else None,
                "tables": [table.table_id for table in tables],
                "table_count": len(tables)
            }
        except Exception as e:
            logger.error("Failed to get dataset info", error=str(e))
            raise
    
    def cleanup_old_data(self, table_name: str, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old data from partitioned tables.
        
        Args:
            table_name: Table to clean up
            days_to_keep: Number of days of data to keep
            
        Returns:
            Cleanup result
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")
        
        try:
            table_ref = self._get_table_ref(table_name)
            
            # Delete old partitions
            query = f"""
            DELETE FROM `{table_ref}`
            WHERE _partition_date < '{cutoff_date_str}'
            """
            
            job = self.client.query(query)
            job.result()
            
            result = {
                "status": "success",
                "table_name": table_name,
                "cutoff_date": cutoff_date_str,
                "rows_deleted": job.num_dml_affected_rows if hasattr(job, 'num_dml_affected_rows') else 0
            }
            
            logger.info("Data cleanup completed", **result)
            return result
            
        except Exception as e:
            logger.error("Data cleanup failed", table_name=table_name, error=str(e))
            raise
