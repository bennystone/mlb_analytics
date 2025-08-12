"""
MLB Data Models

Pydantic models for MLB data validation with baseball-specific constraints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class Player(BaseModel):
    """MLB Player model with baseball-specific validations."""
    player_id: int = Field(..., ge=1, description="MLB player ID")
    full_name: str = Field(..., min_length=1, max_length=100, description="Player's full name")
    position: str = Field(..., description="Player's primary position")
    team_id: int = Field(..., ge=1, description="MLB team ID")
    is_active: bool = Field(default=True, description="Whether player is currently active")
    is_rookie_eligible: bool = Field(default=False, description="Rookie eligibility status")
    
    @validator('position')
    def validate_position(cls, v):
        valid_positions = [
            'P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH',
            'SP', 'RP', 'CL', 'UTIL', 'OF', 'IF'
        ]
        if v not in valid_positions:
            raise ValueError(f'Position must be one of: {", ".join(valid_positions)}')
        return v


class Team(BaseModel):
    """MLB Team model."""
    team_id: int = Field(..., ge=1, description="MLB team ID")
    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    abbreviation: str = Field(..., min_length=2, max_length=3, description="Team abbreviation")
    division_id: int = Field(..., ge=1, description="MLB division ID")
    league_id: int = Field(..., ge=1, description="MLB league ID")
    city: str = Field(..., description="Team city")
    venue_name: Optional[str] = Field(None, description="Home venue name")


class BattingStats(BaseModel):
    """Batting statistics with proper validation ranges."""
    games_played: int = Field(..., ge=0, le=162, description="Games played")
    at_bats: int = Field(..., ge=0, description="At bats")
    hits: int = Field(..., ge=0, description="Hits")
    home_runs: int = Field(..., ge=0, description="Home runs")
    runs_batted_in: int = Field(..., ge=0, description="Runs batted in")
    runs: int = Field(..., ge=0, description="Runs scored")
    stolen_bases: int = Field(..., ge=0, description="Stolen bases")
    batting_average: float = Field(..., ge=0.0, le=1.0, description="Batting average")
    on_base_percentage: float = Field(..., ge=0.0, le=1.0, description="On-base percentage")
    slugging_percentage: float = Field(..., ge=0.0, description="Slugging percentage")
    ops: float = Field(..., ge=0.0, description="On-base plus slugging")
    
    @validator('batting_average', 'on_base_percentage')
    def validate_percentage(cls, v):
        if v > 1.0:
            raise ValueError('Percentage cannot exceed 1.0')
        return round(v, 3) if v is not None else v


class PitchingStats(BaseModel):
    """Pitching statistics with proper validation ranges."""
    games_played: int = Field(..., ge=0, le=162, description="Games played")
    games_started: int = Field(..., ge=0, le=162, description="Games started")
    wins: int = Field(..., ge=0, le=30, description="Wins")
    losses: int = Field(..., ge=0, le=30, description="Losses")
    saves: int = Field(..., ge=0, description="Saves")
    innings_pitched: float = Field(..., ge=0.0, le=300.0, description="Innings pitched")
    strikeouts: int = Field(..., ge=0, description="Strikeouts")
    walks: int = Field(..., ge=0, description="Walks")
    earned_runs: int = Field(..., ge=0, description="Earned runs")
    era: float = Field(..., ge=0.0, le=20.0, description="Earned run average")
    whip: float = Field(..., ge=0.0, le=5.0, description="Walks plus hits per inning pitched")
    
    @validator('era', 'whip')
    def validate_pitching_stats(cls, v):
        return round(v, 2) if v is not None else v


class TeamStanding(BaseModel):
    """Team standing information."""
    team_id: int = Field(..., ge=1, description="MLB team ID")
    team_name: str = Field(..., description="Team name")
    wins: int = Field(..., ge=0, le=162, description="Wins")
    losses: int = Field(..., ge=0, le=162, description="Losses")
    games_back: float = Field(..., ge=0.0, description="Games back from division leader")
    win_percentage: float = Field(..., ge=0.0, le=1.0, description="Win percentage")
    runs_scored: int = Field(..., ge=0, description="Runs scored")
    runs_allowed: int = Field(..., ge=0, description="Runs allowed")
    run_differential: int = Field(..., description="Run differential")
    
    @validator('win_percentage')
    def validate_win_percentage(cls, v):
        if v > 1.0:
            raise ValueError('Win percentage cannot exceed 1.0')
        return round(v, 3) if v is not None else v


class StandingsResponse(BaseModel):
    """API response for standings data."""
    season: int = Field(..., ge=1900, le=2030, description="MLB season year")
    standings: Dict = Field(..., description="MLB standings data")
    playoff_probabilities: Optional[Dict[int, float]] = Field(None, description="Playoff probabilities by team ID")
    last_updated: float = Field(..., description="Timestamp of last update")


class LeaderboardResponse(BaseModel):
    """API response for leaderboard data."""
    stat_type: str = Field(..., description="Statistical type (hitting, pitching, fielding)")
    category: str = Field(..., description="Statistical category")
    season: int = Field(..., ge=1900, le=2030, description="MLB season year")
    limit: int = Field(..., ge=1, le=100, description="Number of leaders returned")
    leaders: Dict = Field(..., description="Leaderboard data")
    last_updated: float = Field(..., description="Timestamp of last update")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")
    timestamp: float = Field(..., description="Current timestamp")


class APIError(BaseModel):
    """Standard API error response."""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class Game(BaseModel):
    """MLB Game model."""
    game_id: int = Field(..., ge=1, description="MLB game ID")
    game_date: datetime = Field(..., description="Game date and time")
    home_team_id: int = Field(..., ge=1, description="Home team ID")
    away_team_id: int = Field(..., ge=1, description="Away team ID")
    home_score: Optional[int] = Field(None, ge=0, description="Home team score")
    away_score: Optional[int] = Field(None, ge=0, description="Away team score")
    status: str = Field(..., description="Game status")
    venue_name: Optional[str] = Field(None, description="Venue name")
    
    @validator('status')
    def validate_game_status(cls, v):
        valid_statuses = [
            'Scheduled', 'Live', 'Final', 'Postponed', 'Cancelled', 'Suspended'
        ]
        if v not in valid_statuses:
            raise ValueError(f'Game status must be one of: {", ".join(valid_statuses)}')
        return v


class SeasonProjection(BaseModel):
    """Season-end projection for a player."""
    player_id: int = Field(..., ge=1, description="MLB player ID")
    season: int = Field(..., ge=1900, le=2030, description="MLB season year")
    projection_type: str = Field(..., description="Type of projection")
    projected_stats: Union[BattingStats, PitchingStats] = Field(..., description="Projected statistics")
    confidence_interval: Optional[Dict[str, float]] = Field(None, description="Confidence intervals")
    last_updated: float = Field(..., description="Timestamp of last update")
    
    @validator('projection_type')
    def validate_projection_type(cls, v):
        valid_types = ['batting', 'pitching', 'fielding']
        if v not in valid_types:
            raise ValueError(f'Projection type must be one of: {", ".join(valid_types)}')
        return v
