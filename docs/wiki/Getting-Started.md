# 🚀 Getting Started

Complete setup guide for the MLB Analytics Platform development environment.

## 📋 Prerequisites

### Required Software
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Install Guide](https://docs.docker.com/get-docker/)
- **Git** - [Download](https://git-scm.com/downloads)
- **VS Code** (recommended) - [Download](https://code.visualstudio.com/)

### Optional Tools
- **Google Cloud CLI** - For cloud deployment
- **Postman** - For API testing
- **Redis CLI** - For cache debugging

### System Requirements
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free space
- **OS**: macOS, Linux, or Windows 10/11

## 🛠️ Local Development Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/bennystone/mlb_analytics.git
cd mlb_analytics

# Verify the structure
ls -la
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

**Example `.env` configuration:**

```env
# Development Environment
ENV=development
LOG_LEVEL=INFO

# MLB API Configuration
MLB_API_BASE_URL=https://statsapi.mlb.com/api/v1

# Redis Configuration
REDIS_URL=redis://redis:6379

# Google Cloud Configuration (optional for local dev)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### 3. Docker Setup

#### Start All Services
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

#### Individual Service Management
```bash
# Start specific services
docker-compose up -d api redis

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# Clean up volumes
docker-compose down -v
```

### 4. Verify Installation

#### Test API Health
```bash
# Test the health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "service": "mlb-analytics-api",
  "version": "0.1.0",
  "timestamp": 1703123456.789
}
```

#### Test API Endpoints
```bash
# Get current standings
curl http://localhost:8000/api/v1/standings/

# Get hitting leaders
curl http://localhost:8000/api/v1/leaders/hitting/top

# Get available categories
curl http://localhost:8000/api/v1/leaders/categories
```

#### Access Streamlit Dashboard
```bash
# Open in browser
open http://localhost:8501
```

## 🔧 Development Workflow

### 1. Code Structure

```
mlb_analytics/
├── src/
│   ├── api/                 # FastAPI application
│   │   ├── main.py         # Main application entry point
│   │   └── routers/        # API route modules
│   ├── data/               # Data fetching and processing
│   ├── models/             # Pydantic data models
│   └── utils/              # Shared utilities
├── tests/                  # Test suite
├── streamlit_app/          # Streamlit dashboard
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

### 2. Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run tests in Docker
docker-compose exec api pytest
```

### 3. Code Quality

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

#### Code Formatting
```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Type checking with mypy
mypy src/
```

### 4. Development Commands

```bash
# Start development server with auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run Streamlit in development mode
streamlit run streamlit_app/main.py

# Run specific service
docker-compose up api

# View service logs
docker-compose logs -f api
```

## 🌐 API Development

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing Endpoints

#### Using curl
```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Get standings
curl -X GET "http://localhost:8000/api/v1/standings/?season=2024"

# Get hitting leaders
curl -X GET "http://localhost:8000/api/v1/leaders/hitting/top?limit=5"
```

#### Using Python requests
```python
import requests

# Base URL
base_url = "http://localhost:8000"

# Health check
response = requests.get(f"{base_url}/health")
print(response.json())

# Get standings
response = requests.get(f"{base_url}/api/v1/standings/", params={"season": 2024})
print(response.json())
```

## 🔍 Debugging

### View Logs
```bash
# API logs
docker-compose logs -f api

# Redis logs
docker-compose logs -f redis

# Streamlit logs
docker-compose logs -f streamlit

# All logs
docker-compose logs -f
```

### Debug Mode
```bash
# Start API in debug mode
docker-compose up -d api
docker-compose exec api python -m debugpy --listen 0.0.0.0:5678 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Database Debugging
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Monitor Redis operations
docker-compose exec redis redis-cli monitor
```

## 🚀 Deployment

### Local Production Build
```bash
# Build production image
docker build -t mlb-analytics:latest .

# Run production container
docker run -p 8000:8000 mlb-analytics:latest
```

### Cloud Deployment
```bash
# Deploy to Google Cloud Run
gcloud run deploy mlb-analytics-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### Docker Build Issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x scripts/*.sh

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
```

### Getting Help

1. **Check the logs**: `docker-compose logs -f`
2. **Verify environment**: Check your `.env` file
3. **Test connectivity**: `curl http://localhost:8000/health`
4. **Check Docker status**: `docker-compose ps`

## 📚 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run the tests**: `pytest`
3. **Check the dashboard**: http://localhost:8501
4. **Read the documentation**: Check the other wiki pages
5. **Start developing**: Pick an issue or feature to work on

---

**Need help?** Check the [Troubleshooting](Troubleshooting) page or open an issue on GitHub.
