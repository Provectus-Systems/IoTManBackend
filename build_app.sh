#!/bin/bash

# Exit on error
set -e

BACKEND_REPO_URL="https://github.com/Provectus-Systems/IoTManBackend.git"
WEBUI_REPO_URL="https://github.com/Provectus-Systems/IoTManWebUI.git"
BACKEND_APP_DIR="/home/ec2-user/IoTManBackend"
WEBUI_APP_DIR="/home/ec2-user/IoTManWebUI"
BACKEND_ENV_FILE="$BACKEND_APP_DIR/.env"
WEBUI_ENV_FILE="$WEBUI_APP_DIR/.env"

echo "Deploying FastAPI IoT Application..."

# Clone the repository if it doesn't exist
if [ ! -d "$BACKEND_APP_DIR" ]; then
    echo "Cloning repository..."
    git clone $BACKEND_REPO_URL $BACKEND_APP_DIR
else
    echo "Repository exists, pulling latest changes..."
    cd $BACKEND_APP_DIR
    git pull origin main
fi

if [ ! -d "$WEBUI_APP_DIR" ]; then
    echo "Cloning repository..."
    git clone $WEBUI_REPO_URL $WEBUI_APP_DIR
else
    echo "Repository exists, pulling latest changes..."
    cd $WEBUI_APP_DIR
    git pull origin main
fi

# Ensure we're in the application directory
cd $BACKEND_APP_DIR

# Check if .env file exists, error out if it doesn't
if [ ! -f "$BACKEND_ENV_FILE" ]; then
    echo "ERROR: .env file does not exist at $BACKEND_ENV_FILE"
    echo "Please create the .env file with required environment variables before deploying."
    exit 1
else
    echo ".env file found. Continuing deployment..."
fi

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if docker service is running
if ! systemctl is-active --quiet docker; then
    echo "Docker service is not running. Attempting to start..."
    sudo systemctl start docker
    if ! systemctl is-active --quiet docker; then
        echo "ERROR: Failed to start Docker service."
        exit 1
    fi
fi

echo "Starting application with Docker Compose..."
docker-compose up --build -d

echo "Deployment complete!"
