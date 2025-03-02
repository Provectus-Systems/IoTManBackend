#!/bin/bash

# Exit on error
set -e

REPO_URL="https://github.com/amloren1/IoTMan.git"
APP_DIR="/home/ec2-user/IoTMan"
ENV_FILE="$APP_DIR/.env"

echo "Deploying FastAPI IoT Application..."

# # Clone the repository if it doesn't exist
# if [ ! -d "$APP_DIR" ]; then
#     echo "Cloning repository..."
#     git clone $REPO_URL $APP_DIR
# else
#     echo "Repository exists, pulling latest changes..."
#     cd $APP_DIR
#     git pull origin main
# fi

# Ensure we're in the application directory
cd $APP_DIR

# Check if .env file exists, error out if it doesn't
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env file does not exist at $ENV_FILE"
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
