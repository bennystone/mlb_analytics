#!/bin/bash

# MLB Analytics Platform - Data Pipeline Setup Script
# This script sets up the complete data pipeline infrastructure

set -e

echo "🏟️  MLB Analytics Platform - Data Pipeline Setup"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    source .env
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  Warning: .env file not found. Using default values."
fi

# Set default values
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
DATASET_ID=${BIGQUERY_DATASET:-"mlb_analytics"}
BUCKET_NAME=${GCS_BUCKET:-"mlb-analytics-data"}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}

echo "📋 Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Dataset ID: $DATASET_ID"
echo "  Bucket Name: $BUCKET_NAME"
echo "  Region: $REGION"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: Google Cloud CLI (gcloud) is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with Google Cloud"
    echo "Please run: gcloud auth login"
    exit 1
fi

echo "✅ Google Cloud authentication verified"

# Set the project
echo "🔧 Setting Google Cloud project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable \
    bigquery.googleapis.com \
    cloudfunctions.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com \
    compute.googleapis.com \
    composer.googleapis.com

echo "✅ APIs enabled successfully"

# Create GCS bucket for data storage
echo "🪣 Creating Google Cloud Storage bucket..."
if ! gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
    gsutil mb -l $REGION gs://$BUCKET_NAME
    echo "✅ Created bucket: gs://$BUCKET_NAME"
else
    echo "✅ Bucket already exists: gs://$BUCKET_NAME"
fi

# Set up BigQuery dataset and tables
echo "🗄️  Setting up BigQuery data warehouse..."
python3 -c "
from src.data.models import BigQueryDataWarehouse
warehouse = BigQueryDataWarehouse('$PROJECT_ID', '$DATASET_ID')
warehouse.setup_data_warehouse()
print('✅ BigQuery data warehouse setup completed')
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
echo "📝 Updating .env file..."
cat >> .env << EOF

# Data Pipeline Configuration
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
BIGQUERY_DATASET=$DATASET_ID
GCS_BUCKET=$BUCKET_NAME
GOOGLE_CLOUD_REGION=$REGION
MLB_DATA_PIPELINE_SERVICE_ACCOUNT=$SERVICE_ACCOUNT_EMAIL
AIRFLOW_WEB_UI_URL=$AIRFLOW_URL
EOF

echo "✅ Updated .env file"

# Create deployment configuration
echo "📋 Creating deployment configuration..."
cat > data_pipeline_config.yaml << EOF
# MLB Analytics Data Pipeline Configuration
project_id: $PROJECT_ID
dataset_id: $DATASET_ID
bucket_name: $BUCKET_NAME
region: $REGION
service_account: $SERVICE_ACCOUNT_EMAIL
airflow_web_ui: $AIRFLOW_URL

# BigQuery Tables
tables:
  - games
  - teams
  - players
  - standings
  - player_stats
  - game_events

# Cloud Functions
functions:
  - extract-daily-schedule
  - extract-live-game-data

# Airflow DAGs
dags:
  - mlb_daily_data_pipeline
  - mlb_live_data_pipeline
  - mlb_backfill_pipeline
  - mlb_data_quality_monitoring
  - mlb_data_warehouse_maintenance
EOF

echo "✅ Created data_pipeline_config.yaml"

echo ""
echo "🎉 Data Pipeline Setup Complete!"
echo "================================"
echo ""
echo "📋 Next Steps:"
echo "1. Upload DAGs to Airflow:"
echo "   - Copy src/data/airflow_dags/ to your Airflow DAGs folder"
echo "   - Or use: gcloud composer environments storage dags import"
echo ""
echo "2. Configure Airflow connections:"
echo "   - Go to: $AIRFLOW_URL"
echo "   - Set up Google Cloud connection with service account key"
echo ""
echo "3. Test the pipeline:"
echo "   - Trigger the daily pipeline manually"
echo "   - Monitor logs for any issues"
echo ""
echo "4. Set up monitoring:"
echo "   - Configure alerts for pipeline failures"
echo "   - Set up data quality monitoring"
echo ""
echo "🔗 Useful Links:"
echo "  - Airflow Web UI: $AIRFLOW_URL"
echo "  - BigQuery Console: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
echo "  - Cloud Functions: https://console.cloud.google.com/functions?project=$PROJECT_ID"
echo ""
echo "📁 Configuration Files:"
echo "  - data_pipeline_config.yaml: Pipeline configuration"
echo "  - credentials/mlb-data-pipeline-key.json: Service account key"
echo "  - .env: Environment variables"
echo ""
echo "✅ Setup completed successfully!"
