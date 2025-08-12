# 📊 API Documentation

Complete reference for the MLB Analytics Platform API endpoints, authentication, and usage guidelines.

## 🔗 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://mlb-analytics-api-xxxxx-uc.a.run.app`

## 🔐 Authentication

Currently, the API is publicly accessible. For production deployments, consider implementing:

- API key authentication
- OAuth 2.0 with Google Cloud
- Rate limiting per IP/user

## 📋 Response Format

All API responses follow a consistent JSON format:

```json
{
  "data": {...},
  "metadata": {
    "timestamp": 1703123456.789,
    "version": "0.1.0"
  }
}
```

## 🏥 Health Check

### GET `/health`

Check API health and status.

**Response:**
```json
{
  "status": "healthy",
  "service": "mlb-analytics-api",
  "version": "0.1.0",
  "timestamp": 1703123456.789
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/health"
```

## 🏠 Root Endpoint

### GET `/`

Get API information and available endpoints.

**Response:**
```json
{
  "message": "MLB Analytics Platform API",
  "version": "0.1.0",
  "docs": "/docs",
  "endpoints": {
    "health": "/health",
    "standings": "/api/v1/standings",
    "leaderboards": "/api/v1/leaders",
    "teams": "/api/v1/teams/{team_id}"
  }
}
```

## 📈 Standings Endpoints

### GET `/api/v1/standings/`

Get current MLB division standings with playoff probabilities.

**Query Parameters:**
- `season` (int, optional): MLB season year (default: 2024, range: 1900-2030)
- `leagueId` (string, optional): Comma-separated league IDs (default: "103,104")
  - `103`: American League
  - `104`: National League
- `include_probabilities` (boolean, optional): Include playoff probabilities (default: true)

**Response:**
```json
{
  "season": 2024,
  "standings": {
    "records": [
      {
        "division": {
          "id": 201,
          "name": "American League East"
        },
        "teamRecords": [
          {
            "team": {
              "id": 121,
              "name": "New York Yankees"
            },
            "wins": 95,
            "losses": 67,
            "gamesBack": 0,
            "winPercentage": 0.586
          }
        ]
      }
    ]
  },
  "playoff_probabilities": {
    "121": 0.85,
    "139": 0.60
  },
  "last_updated": 1703123456.789
}
```

**Example:**
```bash
# Get current standings
curl -X GET "http://localhost:8000/api/v1/standings/"

# Get 2023 standings
curl -X GET "http://localhost:8000/api/v1/standings/?season=2023"

# Get AL standings only
curl -X GET "http://localhost:8000/api/v1/standings/?leagueId=103"
```

### GET `/api/v1/standings/division/{division_id}`

Get standings for a specific division.

**Path Parameters:**
- `division_id` (int): MLB division ID

**Query Parameters:**
- `season` (int, optional): MLB season year (default: 2024)

**Example:**
```bash
# Get AL East standings (division ID: 201)
curl -X GET "http://localhost:8000/api/v1/standings/division/201"
```

### GET `/api/v1/standings/wildcard`

Get wildcard standings and race.

**Query Parameters:**
- `season` (int, optional): MLB season year (default: 2024)
- `leagueId` (string, optional): League IDs (default: "103,104")

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/standings/wildcard"
```

## 🏆 Leaderboard Endpoints

### GET `/api/v1/leaders/{stat_type}`

Get statistical leaders for specific categories.

**Path Parameters:**
- `stat_type` (string): Statistical type (`hitting`, `pitching`, `fielding`)

**Query Parameters:**
- `category` (string): Specific statistical category
- `season` (int, optional): MLB season year (default: 2024)
- `limit` (int, optional): Number of leaders (default: 10, max: 100)
- `leagueId` (string, optional): League ID filter

**Valid Categories by Type:**

#### Hitting Categories
- `avg` - Batting Average
- `hr` - Home Runs
- `rbi` - Runs Batted In
- `r` - Runs Scored
- `sb` - Stolen Bases
- `obp` - On-Base Percentage
- `slg` - Slugging Percentage
- `ops` - On-Base Plus Slugging
- `hits` - Hits
- `doubles` - Doubles
- `triples` - Triples

#### Pitching Categories
- `era` - Earned Run Average
- `wins` - Wins
- `losses` - Losses
- `saves` - Saves
- `strikeouts` - Strikeouts
- `whip` - Walks Plus Hits Per Inning
- `innings_pitched` - Innings Pitched
- `quality_starts` - Quality Starts

#### Fielding Categories
- `fielding_percentage` - Fielding Percentage
- `assists` - Assists
- `putouts` - Putouts
- `errors` - Errors
- `double_plays_turned` - Double Plays Turned

**Response:**
```json
{
  "stat_type": "hitting",
  "category": "avg",
  "season": 2024,
  "limit": 10,
  "leaders": {
    "leader_hitting_avg": {
      "leaders": [
        {
          "person": {
            "id": 123,
            "fullName": "Player Name"
          },
          "value": 0.350,
          "rank": 1
        }
      ]
    }
  },
  "last_updated": 1703123456.789
}
```

**Example:**
```bash
# Get batting average leaders
curl -X GET "http://localhost:8000/api/v1/leaders/hitting?category=avg&limit=5"

# Get ERA leaders
curl -X GET "http://localhost:8000/api/v1/leaders/pitching?category=era&limit=10"
```

### GET `/api/v1/leaders/hitting/top`

Get top hitting leaders across multiple categories.

**Query Parameters:**
- `season` (int, optional): MLB season year (default: 2024)
- `limit` (int, optional): Number of leaders (default: 10, max: 50)
- `leagueId` (string, optional): League ID filter

**Response:**
```json
{
  "stat_type": "hitting",
  "season": 2024,
  "categories": {
    "avg": {...},
    "hr": {...},
    "rbi": {...},
    "r": {...},
    "sb": {...}
  },
  "last_updated": 1703123456.789
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/leaders/hitting/top?limit=5"
```

### GET `/api/v1/leaders/pitching/top`

Get top pitching leaders across multiple categories.

**Query Parameters:**
- `season` (int, optional): MLB season year (default: 2024)
- `limit` (int, optional): Number of leaders (default: 10, max: 50)
- `leagueId` (string, optional): League ID filter

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/leaders/pitching/top?limit=5"
```

### GET `/api/v1/leaders/categories`

Get list of available statistical categories.

**Response:**
```json
{
  "categories": {
    "hitting": ["avg", "hr", "rbi", "r", "sb", "obp", "slg", "ops", "hits", "doubles", "triples"],
    "pitching": ["era", "wins", "losses", "saves", "strikeouts", "whip", "innings_pitched", "quality_starts"],
    "fielding": ["fielding_percentage", "assists", "putouts", "errors", "double_plays_turned"]
  },
  "description": "Available statistical categories for leaderboards"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/leaders/categories"
```

## ⚾ Team Endpoints

### GET `/api/v1/teams/{team_id}`

Get detailed team information and statistics.

**Path Parameters:**
- `team_id` (int): MLB team ID

**Query Parameters:**
- `season` (int, optional): MLB season year (default: 2024)

**Response:**
```json
{
  "team_id": 121,
  "season": 2024,
  "team_info": {
    "teams": [
      {
        "id": 121,
        "name": "New York Yankees",
        "abbreviation": "NYY",
        "division": {
          "id": 201,
          "name": "American League East"
        }
      }
    ]
  },
  "season_stats": {...},
  "last_updated": 1703123456.789
}
```

**Example:**
```bash
# Get Yankees info (team ID: 121)
curl -X GET "http://localhost:8000/api/v1/teams/121"
```

## 🚨 Error Responses

### Standard Error Format

```json
{
  "error": "error_type",
  "detail": "Detailed error message",
  "timestamp": 1703123456.789
}
```

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (endpoint or resource not found)
- `422` - Validation Error (invalid input data)
- `502` - Bad Gateway (MLB API unavailable)
- `500` - Internal Server Error

### Error Examples

#### Invalid Category
```json
{
  "error": "validation_error",
  "detail": "Invalid category 'invalid_stat' for hitting. Valid categories: avg, hr, rbi, r, sb, obp, slg, ops, hits, doubles, triples",
  "timestamp": 1703123456.789
}
```

#### MLB API Unavailable
```json
{
  "error": "bad_gateway",
  "detail": "MLB API temporarily unavailable. Please try again later.",
  "timestamp": 1703123456.789
}
```

## 📊 Rate Limiting

Currently, no rate limiting is implemented. For production use, consider:

- **Per IP**: 100 requests per minute
- **Per User**: 1000 requests per hour
- **Burst**: Allow short bursts of higher traffic

## 🔧 Usage Guidelines

### Best Practices

1. **Caching**: Cache responses for 5-15 minutes depending on data freshness needs
2. **Error Handling**: Implement exponential backoff for retries
3. **Monitoring**: Log API usage and errors for monitoring
4. **Validation**: Validate all input parameters before making requests

### Example Client Code

#### Python
```python
import requests
import time
from typing import Dict, Any

class MLBAnalyticsClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_standings(self, season: int = 2024) -> Dict[str, Any]:
        """Get current standings."""
        response = self.session.get(
            f"{self.base_url}/api/v1/standings/",
            params={"season": season}
        )
        response.raise_for_status()
        return response.json()
    
    def get_leaders(self, stat_type: str, category: str, limit: int = 10) -> Dict[str, Any]:
        """Get statistical leaders."""
        response = self.session.get(
            f"{self.base_url}/api/v1/leaders/{stat_type}",
            params={"category": category, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = MLBAnalyticsClient()
standings = client.get_standings(2024)
leaders = client.get_leaders("hitting", "avg", 5)
```

#### JavaScript
```javascript
class MLBAnalyticsClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async getStandings(season = 2024) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/standings/?season=${season}`
        );
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }
    
    async getLeaders(statType, category, limit = 10) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/leaders/${statType}?category=${category}&limit=${limit}`
        );
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }
}

// Usage
const client = new MLBAnalyticsClient();
client.getStandings(2024).then(standings => console.log(standings));
```

## 📚 Interactive Documentation

- **Swagger UI**: `/docs` - Interactive API documentation
- **ReDoc**: `/redoc` - Alternative documentation format

## 🔄 Webhooks (Future)

Planned webhook support for real-time updates:

- Game score updates
- Standings changes
- Player milestone achievements
- Playoff clinching events

---

**Need help?** Check the [Troubleshooting](Troubleshooting) page or open an issue on GitHub.
