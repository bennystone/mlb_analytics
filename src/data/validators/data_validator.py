"""
Data Validation Framework

Data validation framework for:
- Check for missing games/scores
- Validate statistical calculations
- Monitor data freshness
- Alert on anomalies
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from google.cloud import bigquery
import structlog

logger = structlog.get_logger()


class DataValidator:
    """Data validation framework for MLB analytics data."""
    
    def __init__(self, project_id: str, dataset_id: str = "mlb_analytics"):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)
        self.dataset_ref = f"{project_id}.{dataset_id}"
        
    def _get_table_ref(self, table_name: str) -> str:
        """Get full table reference."""
        return f"{self.dataset_ref}.{table_name}"
    
    def validate_games_data(self, date: datetime) -> Dict[str, Any]:
        """
        Validate games data for a specific date.
        
        Args:
            date: Date to validate
            
        Returns:
            Validation results
        """
        date_str = date.strftime("%Y-%m-%d")
        
        try:
            # Query for games on the specified date
            query = f"""
            SELECT 
                game_id,
                home_team_id,
                away_team_id,
                home_score,
                away_score,
                status,
                detailed_status,
                is_final,
                is_live
            FROM `{self.dataset_ref}.games`
            WHERE game_date = '{date_str}'
            ORDER BY game_time
            """
            
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            validation_results = {
                "date": date_str,
                "total_games": len(results),
                "final_games": len([r for r in results if r.is_final]),
                "live_games": len([r for r in results if r.is_live]),
                "scheduled_games": len([r for r in results if not r.is_final and not r.is_live]),
                "missing_scores": [],
                "anomalies": [],
                "validation_passed": True
            }
            
            # Check for missing scores in final games
            for row in results:
                if row.is_final and (row.home_score is None or row.away_score is None):
                    validation_results["missing_scores"].append({
                        "game_id": row.game_id,
                        "home_team_id": row.home_team_id,
                        "away_team_id": row.away_team_id,
                        "home_score": row.home_score,
                        "away_score": row.away_score
                    })
                    validation_results["validation_passed"] = False
            
            # Check for anomalies (negative scores, impossible game states)
            for row in results:
                if row.home_score is not None and row.home_score < 0:
                    validation_results["anomalies"].append({
                        "game_id": row.game_id,
                        "type": "negative_home_score",
                        "value": row.home_score
                    })
                    validation_results["validation_passed"] = False
                
                if row.away_score is not None and row.away_score < 0:
                    validation_results["anomalies"].append({
                        "game_id": row.game_id,
                        "type": "negative_away_score",
                        "value": row.away_score
                    })
                    validation_results["validation_passed"] = False
                
                # Check for impossible game states
                if row.is_final and row.is_live:
                    validation_results["anomalies"].append({
                        "game_id": row.game_id,
                        "type": "impossible_game_state",
                        "is_final": row.is_final,
                        "is_live": row.is_live
                    })
                    validation_results["validation_passed"] = False
            
            logger.info(
                "Games data validation completed",
                date=date_str,
                total_games=validation_results["total_games"],
                validation_passed=validation_results["validation_passed"]
            )
            
            return validation_results
            
        except Exception as e:
            logger.error("Games data validation failed", date=date_str, error=str(e))
            raise
    
    def validate_standings_data(self, date: datetime) -> Dict[str, Any]:
        """
        Validate standings data for a specific date.
        
        Args:
            date: Date to validate
            
        Returns:
            Validation results
        """
        date_str = date.strftime("%Y-%m-%d")
        
        try:
            # Query for standings on the specified date
            query = f"""
            SELECT 
                team_id,
                division_id,
                league_id,
                wins,
                losses,
                win_percentage,
                games_back,
                runs_scored,
                runs_allowed,
                run_differential,
                games_played
            FROM `{self.dataset_ref}.standings`
            WHERE standings_date = '{date_str}'
            ORDER BY league_id, division_id, games_back
            """
            
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            validation_results = {
                "date": date_str,
                "total_teams": len(results),
                "anomalies": [],
                "validation_passed": True
            }
            
            # Validate win percentages
            for row in results:
                if row.wins is not None and row.losses is not None:
                    expected_win_pct = row.wins / (row.wins + row.losses) if (row.wins + row.losses) > 0 else 0
                    if abs(row.win_percentage - expected_win_pct) > 0.001:  # Allow small floating point differences
                        validation_results["anomalies"].append({
                            "team_id": row.team_id,
                            "type": "incorrect_win_percentage",
                            "expected": expected_win_pct,
                            "actual": row.win_percentage
                        })
                        validation_results["validation_passed"] = False
                
                # Validate run differential
                if row.runs_scored is not None and row.runs_allowed is not None:
                    expected_run_diff = row.runs_scored - row.runs_allowed
                    if row.run_differential != expected_run_diff:
                        validation_results["anomalies"].append({
                            "team_id": row.team_id,
                            "type": "incorrect_run_differential",
                            "expected": expected_run_diff,
                            "actual": row.run_differential
                        })
                        validation_results["validation_passed"] = False
                
                # Check for negative values
                if row.wins is not None and row.wins < 0:
                    validation_results["anomalies"].append({
                        "team_id": row.team_id,
                        "type": "negative_wins",
                        "value": row.wins
                    })
                    validation_results["validation_passed"] = False
                
                if row.losses is not None and row.losses < 0:
                    validation_results["anomalies"].append({
                        "team_id": row.team_id,
                        "type": "negative_losses",
                        "value": row.losses
                    })
                    validation_results["validation_passed"] = False
            
            logger.info(
                "Standings data validation completed",
                date=date_str,
                total_teams=validation_results["total_teams"],
                validation_passed=validation_results["validation_passed"]
            )
            
            return validation_results
            
        except Exception as e:
            logger.error("Standings data validation failed", date=date_str, error=str(e))
            raise
    
    def validate_player_stats(self, season: int = None) -> Dict[str, Any]:
        """
        Validate player statistics.
        
        Args:
            season: Season to validate (defaults to current year)
            
        Returns:
            Validation results
        """
        if season is None:
            season = datetime.now().year
        
        try:
            # Query for player stats
            query = f"""
            SELECT 
                player_id,
                team_id,
                stat_type,
                games_played,
                at_bats,
                hits,
                home_runs,
                rbi,
                batting_average,
                wins,
                losses,
                era,
                whip
            FROM `{self.dataset_ref}.player_stats`
            WHERE season = {season}
            """
            
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            validation_results = {
                "season": season,
                "total_players": len(results),
                "anomalies": [],
                "validation_passed": True
            }
            
            # Validate batting averages
            for row in results:
                if row.stat_type == "hitting" and row.at_bats is not None and row.hits is not None:
                    if row.at_bats > 0:
                        expected_avg = row.hits / row.at_bats
                        if row.batting_average is not None and abs(row.batting_average - expected_avg) > 0.001:
                            validation_results["anomalies"].append({
                                "player_id": row.player_id,
                                "type": "incorrect_batting_average",
                                "expected": expected_avg,
                                "actual": row.batting_average
                            })
                            validation_results["validation_passed"] = False
                
                # Validate batting average range
                if row.batting_average is not None and (row.batting_average < 0 or row.batting_average > 1):
                    validation_results["anomalies"].append({
                        "player_id": row.player_id,
                        "type": "invalid_batting_average_range",
                        "value": row.batting_average
                    })
                    validation_results["validation_passed"] = False
                
                # Validate ERA range
                if row.era is not None and (row.era < 0 or row.era > 20):
                    validation_results["anomalies"].append({
                        "player_id": row.player_id,
                        "type": "invalid_era_range",
                        "value": row.era
                    })
                    validation_results["validation_passed"] = False
                
                # Validate WHIP range
                if row.whip is not None and (row.whip < 0 or row.whip > 5):
                    validation_results["anomalies"].append({
                        "player_id": row.player_id,
                        "type": "invalid_whip_range",
                        "value": row.whip
                    })
                    validation_results["validation_passed"] = False
            
            logger.info(
                "Player stats validation completed",
                season=season,
                total_players=validation_results["total_players"],
                validation_passed=validation_results["validation_passed"]
            )
            
            return validation_results
            
        except Exception as e:
            logger.error("Player stats validation failed", season=season, error=str(e))
            raise
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """
        Check data freshness across all tables.
        
        Returns:
            Data freshness results
        """
        try:
            freshness_results = {
                "timestamp": datetime.now().isoformat(),
                "tables": {},
                "overall_freshness": "good"
            }
            
            # Check games table freshness
            games_query = f"""
            SELECT 
                MAX(extraction_timestamp) as latest_extraction,
                COUNT(*) as total_games_today
            FROM `{self.dataset_ref}.games`
            WHERE game_date = CURRENT_DATE()
            """
            
            games_job = self.client.query(games_query)
            games_result = list(games_job.result())[0]
            
            if games_result.latest_extraction:
                games_age = datetime.now() - games_result.latest_extraction.replace(tzinfo=None)
                freshness_results["tables"]["games"] = {
                    "latest_extraction": games_result.latest_extraction.isoformat(),
                    "age_minutes": games_age.total_seconds() / 60,
                    "total_games_today": games_result.total_games_today,
                    "freshness": "stale" if games_age.total_seconds() > 3600 else "fresh"  # 1 hour threshold
                }
            else:
                freshness_results["tables"]["games"] = {
                    "latest_extraction": None,
                    "age_minutes": None,
                    "total_games_today": 0,
                    "freshness": "no_data"
                }
            
            # Check standings table freshness
            standings_query = f"""
            SELECT 
                MAX(extraction_timestamp) as latest_extraction,
                COUNT(*) as total_standings_records
            FROM `{self.dataset_ref}.standings`
            WHERE standings_date = CURRENT_DATE()
            """
            
            standings_job = self.client.query(standings_query)
            standings_result = list(standings_job.result())[0]
            
            if standings_result.latest_extraction:
                standings_age = datetime.now() - standings_result.latest_extraction.replace(tzinfo=None)
                freshness_results["tables"]["standings"] = {
                    "latest_extraction": standings_result.latest_extraction.isoformat(),
                    "age_minutes": standings_age.total_seconds() / 60,
                    "total_records": standings_result.total_standings_records,
                    "freshness": "stale" if standings_age.total_seconds() > 7200 else "fresh"  # 2 hour threshold
                }
            else:
                freshness_results["tables"]["standings"] = {
                    "latest_extraction": None,
                    "age_minutes": None,
                    "total_records": 0,
                    "freshness": "no_data"
                }
            
            # Determine overall freshness
            stale_tables = [table for table in freshness_results["tables"].values() 
                          if table["freshness"] == "stale"]
            no_data_tables = [table for table in freshness_results["tables"].values() 
                            if table["freshness"] == "no_data"]
            
            if stale_tables:
                freshness_results["overall_freshness"] = "stale"
            elif no_data_tables:
                freshness_results["overall_freshness"] = "no_data"
            else:
                freshness_results["overall_freshness"] = "fresh"
            
            logger.info(
                "Data freshness check completed",
                overall_freshness=freshness_results["overall_freshness"],
                tables=freshness_results["tables"]
            )
            
            return freshness_results
            
        except Exception as e:
            logger.error("Data freshness check failed", error=str(e))
            raise
    
    def generate_validation_report(self, date: datetime = None) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Args:
            date: Date to validate (defaults to today)
            
        Returns:
            Comprehensive validation report
        """
        if date is None:
            date = datetime.now()
        
        try:
            report = {
                "validation_date": date.isoformat(),
                "timestamp": datetime.now().isoformat(),
                "games_validation": self.validate_games_data(date),
                "standings_validation": self.validate_standings_data(date),
                "player_stats_validation": self.validate_player_stats(date.year),
                "data_freshness": self.check_data_freshness(),
                "overall_status": "passed"
            }
            
            # Determine overall status
            failed_validations = []
            
            if not report["games_validation"]["validation_passed"]:
                failed_validations.append("games")
            
            if not report["standings_validation"]["validation_passed"]:
                failed_validations.append("standings")
            
            if not report["player_stats_validation"]["validation_passed"]:
                failed_validations.append("player_stats")
            
            if report["data_freshness"]["overall_freshness"] in ["stale", "no_data"]:
                failed_validations.append("data_freshness")
            
            if failed_validations:
                report["overall_status"] = "failed"
                report["failed_validations"] = failed_validations
            
            logger.info(
                "Validation report generated",
                overall_status=report["overall_status"],
                failed_validations=failed_validations
            )
            
            return report
            
        except Exception as e:
            logger.error("Validation report generation failed", error=str(e))
            raise
    
    def alert_on_anomalies(self, validation_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate alerts for anomalies found in validation.
        
        Args:
            validation_report: Validation report from generate_validation_report
            
        Returns:
            List of alerts
        """
        alerts = []
        
        # Check for validation failures
        if validation_report["overall_status"] == "failed":
            alerts.append({
                "level": "error",
                "type": "validation_failure",
                "message": f"Data validation failed for {', '.join(validation_report.get('failed_validations', []))}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check for missing scores
        missing_scores = validation_report["games_validation"].get("missing_scores", [])
        if missing_scores:
            alerts.append({
                "level": "warning",
                "type": "missing_scores",
                "message": f"Found {len(missing_scores)} games with missing scores",
                "details": missing_scores,
                "timestamp": datetime.now().isoformat()
            })
        
        # Check for data freshness issues
        if validation_report["data_freshness"]["overall_freshness"] == "stale":
            alerts.append({
                "level": "warning",
                "type": "data_stale",
                "message": "Data is stale and may need refresh",
                "details": validation_report["data_freshness"]["tables"],
                "timestamp": datetime.now().isoformat()
            })
        
        # Check for anomalies
        all_anomalies = []
        all_anomalies.extend(validation_report["games_validation"].get("anomalies", []))
        all_anomalies.extend(validation_report["standings_validation"].get("anomalies", []))
        all_anomalies.extend(validation_report["player_stats_validation"].get("anomalies", []))
        
        if all_anomalies:
            alerts.append({
                "level": "error",
                "type": "data_anomalies",
                "message": f"Found {len(all_anomalies)} data anomalies",
                "details": all_anomalies,
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(
            "Alerts generated",
            alert_count=len(alerts),
            alert_types=[alert["type"] for alert in alerts]
        )
        
        return alerts
