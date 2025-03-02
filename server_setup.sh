#!/bin/bash

# Exit on error
set -e

echo "Updating system..."
sudo yum update -y

echo "Installing Docker..."
sudo amazon-linux-extras enable docker
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker

echo "Adding user to Docker group..."
sudo usermod -aG docker ec2-user

echo "Installing Git..."
sudo yum install git -y

echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "Setting up Docker Compose to run on startup..."
sudo tee /etc/systemd/system/docker-compose-app.service > /dev/null <<EOL
[Unit]
Description=Docker Compose FastAPI IoT App
After=network.target docker.service
Requires=docker.service

[Service]
Restart=always
WorkingDirectory=/home/ec2-user/fastapi-iot
ExecStart=/usr/local/bin/docker-compose up --build -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOL

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
sudo systemctl enable docker-compose-app

echo "Setup completed! Please log out and log back in for Docker permissions to take effect."
