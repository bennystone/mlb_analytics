#!/bin/bash
set -e

echo "Setting up MLB Analytics Platform development environment..."

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Create environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please update with your credentials."
fi

# Setup Google Cloud authentication
echo "Please run: gcloud auth application-default login"
echo "And set GOOGLE_CLOUD_PROJECT in your .env file"

echo "Setup complete! Run 'docker-compose up' to start the development environment."
