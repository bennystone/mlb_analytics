#!/bin/bash
set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
REGION="us-central1"
SERVICE="mlb-analytics-api"

echo "Deploying MLB Analytics API to Cloud Run..."

# Build and submit to Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE

# Deploy to Cloud Run
gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID

echo "Deployment complete!"
echo "API URL: $(gcloud run services describe $SERVICE --region=$REGION --format='value(status.url)')"
