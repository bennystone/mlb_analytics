#!/bin/bash

# MLB Analytics Platform - Deployment Configuration Verification
# This script verifies all required configuration before deployment

set -e

echo "🔍 MLB Analytics Platform - Deployment Configuration Verification"
echo "================================================================"

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
    echo "❌ Error: .env file not found"
    echo "Please copy env.template to .env and configure it"
    exit 1
fi

echo ""
echo "📋 Configuration Verification:"
echo "=============================="

# Check required variables
REQUIRED_VARS=(
    "GOOGLE_CLOUD_PROJECT"
    "GOOGLE_APPLICATION_CREDENTIALS"
    "BIGQUERY_DATASET"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
        echo "❌ Missing: $var"
    else
        echo "✅ Found: $var=${!var}"
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing required environment variables:"
    printf '%s\n' "${MISSING_VARS[@]}"
    echo ""
    echo "Please update your .env file with these variables"
    exit 1
fi

# Check if gcloud is installed and authenticated
echo ""
echo "🔧 Google Cloud CLI Verification:"
echo "================================="

if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: Google Cloud CLI (gcloud) is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
else
    echo "✅ Google Cloud CLI is installed"
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with Google Cloud"
    echo "Please run: gcloud auth login"
    exit 1
else
    echo "✅ Google Cloud authentication verified"
fi

# Check if project exists and user has access
echo ""
echo "🏗️  Google Cloud Project Verification:"
echo "======================================"

if ! gcloud projects describe "$GOOGLE_CLOUD_PROJECT" &> /dev/null; then
    echo "❌ Error: Cannot access project '$GOOGLE_CLOUD_PROJECT'"
    echo "Please verify:"
    echo "1. Project ID is correct"
    echo "2. You have access to the project"
    echo "3. You're authenticated with the right account"
    exit 1
else
    echo "✅ Project '$GOOGLE_CLOUD_PROJECT' is accessible"
fi

# Check service account key file
echo ""
echo "🔑 Service Account Key Verification:"
echo "===================================="

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ Error: Service account key file not found: $GOOGLE_APPLICATION_CREDENTIALS"
    echo "Please ensure the file exists and the path is correct"
    exit 1
else
    echo "✅ Service account key file found: $GOOGLE_APPLICATION_CREDENTIALS"
fi

# Test service account authentication
export GOOGLE_APPLICATION_CREDENTIALS
if ! gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS" &> /dev/null; then
    echo "❌ Error: Cannot activate service account"
    echo "Please verify the key file is valid and has proper permissions"
    exit 1
else
    echo "✅ Service account authentication successful"
fi

# Check if required APIs are enabled
echo ""
echo "🔌 Google Cloud APIs Verification:"
echo "=================================="

REQUIRED_APIS=(
    "bigquery.googleapis.com"
    "cloudfunctions.googleapis.com"
    "cloudbuild.googleapis.com"
    "storage.googleapis.com"
    "compute.googleapis.com"
    "composer.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "✅ $api is enabled"
    else
        echo "⚠️  $api is not enabled (will be enabled during setup)"
    fi
done

# Check Python dependencies
echo ""
echo "🐍 Python Dependencies Verification:"
echo "===================================="

if ! python3 -c "import google.cloud.bigquery" 2>/dev/null; then
    echo "⚠️  Google Cloud BigQuery library not installed"
    echo "Please run: pip install google-cloud-bigquery"
else
    echo "✅ Google Cloud BigQuery library is installed"
fi

if ! python3 -c "import httpx" 2>/dev/null; then
    echo "⚠️  httpx library not installed"
    echo "Please run: pip install httpx"
else
    echo "✅ httpx library is installed"
fi

# Check optional configurations
echo ""
echo "📝 Optional Configuration:"
echo "=========================="

if [ -n "$GOOGLE_CLOUD_REGION" ]; then
    echo "✅ Google Cloud Region: $GOOGLE_CLOUD_REGION"
else
    echo "⚠️  Google Cloud Region not set (will use default: us-central1)"
fi

if [ -n "$GCS_BUCKET" ]; then
    echo "✅ GCS Bucket: $GCS_BUCKET"
else
    echo "⚠️  GCS Bucket not set (will use default: mlb-analytics-data)"
fi

if [ -n "$ALERT_EMAIL" ]; then
    echo "✅ Alert Email: $ALERT_EMAIL"
else
    echo "⚠️  Alert Email not set (alerts will be logged only)"
fi

echo ""
echo "🎉 Configuration Verification Complete!"
echo "======================================="
echo ""
echo "✅ All required configuration is present"
echo "✅ Google Cloud authentication is working"
echo "✅ Project access is verified"
echo "✅ Service account is configured"
echo ""
echo "🚀 Ready to run: ./scripts/setup_data_pipeline.sh"
echo ""
echo "📋 Summary of what will be deployed:"
echo "  - BigQuery dataset and tables"
echo "  - Cloud Functions for data extraction"
echo "  - Cloud Composer (Airflow) environment"
echo "  - Service account with proper permissions"
echo "  - GCS bucket for data storage"
echo ""
echo "⏱️  Estimated deployment time: 10-15 minutes"
