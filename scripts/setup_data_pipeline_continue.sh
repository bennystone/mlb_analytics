#!/bin/bash

# MLB Analytics Platform - Data Pipeline Setup (Continuation)
# This script continues the setup after BigQuery dataset creation

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
DATASET_ID=${BIGQUERY_DATASET:-mlb_analytics}
BUCKET_NAME=${GCS_BUCKET:-mlb-analytics-data}
REGION=${GOOGLE_CLOUD_REGION:-us-central1}

echo "🏟️  MLB Analytics Platform - Data Pipeline Setup (Continuation)"
echo "================================================================"
echo "✅ Loaded environment variables from .env"
echo "📋 Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Dataset ID: $DATASET_ID"
echo "  Bucket Name: $BUCKET_NAME"
echo "  Region: $REGION"

# Verify Google Cloud authentication
echo "🔧 Verifying Google Cloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ No active Google Cloud authentication found"
    exit 1
fi
echo "✅ Google Cloud authentication verified"

# Set Google Cloud project
echo "🔧 Setting Google Cloud project..."
gcloud config set project $PROJECT_ID

# Create BigQuery tables (skip dataset creation)
echo "🗄️  Creating BigQuery tables..."
python3 -c "
from src.data.models import BigQueryDataWarehouse
warehouse = BigQueryDataWarehouse('$PROJECT_ID', '$DATASET_ID')
# Skip dataset creation, just create tables
warehouse.create_games_table()
warehouse.create_teams_table()
warehouse.create_players_table()
warehouse.create_standings_table()
warehouse.create_player_stats_table()
warehouse.create_game_events_table()
warehouse.create_analytics_views()
print('✅ BigQuery tables and views created successfully')
"

# Deploy Cloud Functions
echo "☁️  Deploying Cloud Functions..."

# Function 1: Daily data extraction
echo "  Deploying daily data extraction function..."
gcloud functions deploy extract-daily-schedule \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --source src/data/cloud_functions \
    --entry-point extract_daily_schedule_cloud_function \
    --region $REGION \
    --set-env-vars PROJECT_ID=$PROJECT_ID,DATASET_ID=$DATASET_ID

# Function 2: Live game data extraction
echo "  Deploying live game data extraction function..."
gcloud functions deploy extract-live-game-data \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --source src/data/cloud_functions \
    --entry-point extract_live_game_data_cloud_function \
    --region $REGION \
    --set-env-vars PROJECT_ID=$PROJECT_ID,DATASET_ID=$DATASET_ID

echo "✅ Cloud Functions deployed successfully"

# Set up Airflow (if using Cloud Composer)
echo "🌪️  Setting up Airflow environment..."

# Check if Cloud Composer environment exists
COMPOSER_ENV_NAME="mlb-analytics-composer"
if ! gcloud composer environments list --locations=$REGION --filter="name:$COMPOSER_ENV_NAME" --format="value(name)" | grep -q .; then
    echo "  Creating Cloud Composer environment..."
    gcloud composer environments create $COMPOSER_ENV_NAME \
        --location $REGION \
        --python-version 3 \
        --image-version composer-2.0.31-airflow-2.7.3 \
        --machine-type n1-standard-2 \
        --node-count 3 \
        --disk-size 100 \
        --airflow-configs=core-dags_are_paused_at_creation=true
    
    echo "✅ Cloud Composer environment created"
else
    echo "✅ Cloud Composer environment already exists"
fi

# Get Airflow web UI URL
echo "  Getting Airflow web UI URL..."
AIRFLOW_URL=$(gcloud composer environments describe $COMPOSER_ENV_NAME \
    --location $REGION \
    --format="value(config.airflowUri)")

echo "✅ Airflow web UI: $AIRFLOW_URL"

# Create service account for data pipeline
echo "🔐 Creating service account for data pipeline..."
SERVICE_ACCOUNT_NAME="mlb-data-pipeline"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts list --filter="email:$SERVICE_ACCOUNT_EMAIL" --format="value(email)" | grep -q .; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="MLB Data Pipeline Service Account"
    echo "✅ Created service account: $SERVICE_ACCOUNT_EMAIL"
else
    echo "✅ Service account already exists: $SERVICE_ACCOUNT_EMAIL"
fi

# Grant necessary permissions
echo "🔐 Granting permissions to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudfunctions.invoker"

echo "✅ Permissions granted successfully"

# Create key file for service account
echo "🔑 Creating service account key..."
KEY_FILE="credentials/mlb-data-pipeline-key.json"
mkdir -p credentials

if [ ! -f "$KEY_FILE" ]; then
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo "✅ Created service account key: $KEY_FILE"
else
    echo "✅ Service account key already exists: $KEY_FILE"
fi

# Update .env file with new values
echo "📝 Updating .env file with new configuration..."
if [ -f .env ]; then
    # Update Airflow URL
    sed -i.bak "s|AIRFLOW_WEB_UI_URL=.*|AIRFLOW_WEB_UI_URL=$AIRFLOW_URL|" .env
    
    # Update service account
    sed -i.bak "s|MLB_DATA_PIPELINE_SERVICE_ACCOUNT=.*|MLB_DATA_PIPELINE_SERVICE_ACCOUNT=$SERVICE_ACCOUNT_EMAIL|" .env
    
    echo "✅ Updated .env file"
else
    echo "⚠️  .env file not found, skipping updates"
fi

echo ""
echo "🎉 MLB Analytics Data Pipeline Setup Complete!"
echo "=============================================="
echo ""
echo "📋 Deployment Summary:"
echo "  ✅ BigQuery dataset: $PROJECT_ID:$DATASET_ID"
echo "  ✅ BigQuery tables and views created"
echo "  ✅ Cloud Functions deployed"
echo "  ✅ Cloud Composer environment: $COMPOSER_ENV_NAME"
echo "  ✅ Service account: $SERVICE_ACCOUNT_EMAIL"
echo "  ✅ GCS bucket: gs://$BUCKET_NAME"
echo ""
echo "🔗 Access URLs:"
echo "  📊 BigQuery Console: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
echo "  🌪️  Airflow Web UI: $AIRFLOW_URL"
echo "  ☁️  Cloud Functions: https://console.cloud.google.com/functions?project=$PROJECT_ID"
echo ""
echo "📝 Next Steps:"
echo "  1. Upload DAGs to Airflow environment"
echo "  2. Configure Airflow connections"
echo "  3. Test data extraction functions"
echo "  4. Monitor data pipeline performance"
echo ""
echo "🚀 Your MLB analytics data pipeline is ready!"
