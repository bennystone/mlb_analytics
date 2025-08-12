# MLB Analytics Platform (MVP)

Production-grade MVP for MLB analytics, featuring a FastAPI backend, Streamlit demo, Dockerized deployment, and CI/CD to Google Cloud Run.

## Quickstart

- Copy `.env.example` to `.env` and fill values.
- Start local stack:
  - Build: `docker compose build`
  - Run: `docker compose up`
  - API: <http://localhost:8000/docs>
  - Streamlit: <http://localhost:8501>

## Project Structure

- `src/api`: FastAPI endpoints
- `src/data`: data fetching/processing
- `src/models`: analytics and ML models
- `src/utils`: shared utilities
- `streamlit_app`: demo UI
- `scripts`: setup/deploy scripts
- `tests`: unit tests

## Deployment

- Configure GCP secrets in GitHub: `GCP_PROJECT_ID`, `GCP_SA_KEY`.
- Push to `main` to trigger CI/CD and deploy to Cloud Run.
