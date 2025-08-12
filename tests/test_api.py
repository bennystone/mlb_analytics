"""
API Tests for MLB Analytics Platform

Tests for FastAPI endpoints with proper error handling and validation.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_endpoint(self):
        """Test that health endpoint returns proper response."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "mlb-analytics-api"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self):
        """Test that root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "MLB Analytics Platform API"
        assert data["version"] == "0.1.0"
        assert "endpoints" in data


class TestStandingsEndpoints:
    """Test standings endpoints."""
    
    @patch('src.api.routers.standings.fetch_mlb_data')
    def test_get_standings_success(self, mock_fetch):
        """Test successful standings retrieval."""
        mock_data = {
            "records": [
                {
                    "division": {"id": 201},
                    "teamRecords": [
                        {
                            "team": {"id": 121},
                            "gamesBack": 0,
                            "wins": 95,
                            "losses": 67
                        }
                    ]
                }
            ]
        }
        mock_fetch.return_value = mock_data
        
        response = client.get("/api/v1/standings/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["season"] == 2024
        assert "standings" in data
        assert "playoff_probabilities" in data
    
    @patch('src.api.routers.standings.fetch_mlb_data')
    def test_get_standings_with_custom_season(self, mock_fetch):
        """Test standings with custom season parameter."""
        mock_fetch.return_value = {"records": []}
        
        response = client.get("/api/v1/standings/?season=2023")
        assert response.status_code == 200
        
        data = response.json()
        assert data["season"] == 2023
    
    @patch('src.api.routers.standings.fetch_mlb_data')
    def test_get_standings_api_error(self, mock_fetch):
        """Test standings endpoint with MLB API error."""
        mock_fetch.side_effect = Exception("MLB API Error")
        
        response = client.get("/api/v1/standings/")
        assert response.status_code == 500


class TestLeaderboardEndpoints:
    """Test leaderboard endpoints."""
    
    @patch('src.api.routers.leaderboards.fetch_mlb_data')
    def test_get_hitting_leaders_success(self, mock_fetch):
        """Test successful hitting leaders retrieval."""
        mock_data = {
            "leader_hitting_avg": {
                "leaders": [
                    {
                        "person": {"id": 123, "fullName": "Test Player"},
                        "value": 0.350
                    }
                ]
            }
        }
        mock_fetch.return_value = mock_data
        
        response = client.get("/api/v1/leaders/hitting/top")
        assert response.status_code == 200
        
        data = response.json()
        assert data["stat_type"] == "hitting"
        assert "categories" in data
    
    def test_get_leaders_invalid_category(self):
        """Test leaderboard endpoint with invalid category."""
        response = client.get("/api/v1/leaders/invalid/avg?category=avg")
        assert response.status_code == 400
        
        data = response.json()
        assert "Invalid stat_type" in data["detail"]
    
    def test_get_leaders_invalid_stat_type(self):
        """Test leaderboard endpoint with invalid stat type."""
        response = client.get("/api/v1/leaders/hitting/invalid_stat?category=invalid_stat")
        assert response.status_code == 400
        
        data = response.json()
        assert "Invalid category" in data["detail"]
    
    def test_get_available_categories(self):
        """Test categories endpoint."""
        response = client.get("/api/v1/leaders/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert "hitting" in data["categories"]
        assert "pitching" in data["categories"]
        assert "fielding" in data["categories"]


class TestParameterValidation:
    """Test parameter validation."""
    
    def test_invalid_season_parameter(self):
        """Test with invalid season parameter."""
        response = client.get("/api/v1/standings/?season=1800")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_limit_parameter(self):
        """Test with invalid limit parameter."""
        response = client.get("/api/v1/leaders/hitting/top?limit=200")
        assert response.status_code == 422  # Validation error
    
    def test_negative_limit_parameter(self):
        """Test with negative limit parameter."""
        response = client.get("/api/v1/leaders/hitting/top?limit=-1")
        assert response.status_code == 422  # Validation error


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_endpoint(self):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    @patch('src.api.routers.standings.fetch_mlb_data')
    def test_mlb_api_timeout(self, mock_fetch):
        """Test handling of MLB API timeout."""
        import httpx
        mock_fetch.side_effect = httpx.TimeoutException("Request timeout")
        
        response = client.get("/api/v1/standings/")
        assert response.status_code == 500
        
        data = response.json()
        assert "Failed to fetch standings data" in data["detail"]


if __name__ == "__main__":
    pytest.main([__file__])
