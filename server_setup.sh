#!/bin/bash

# Exit on error
set -e

echo "Updating system..."
sudo yum update -y

echo "Installing Docker..."
# Check Amazon Linux version
if grep -q "Amazon Linux 2" /etc/os-release; then
    # Amazon Linux 2 approach
    sudo amazon-linux-extras install docker -y
else
    # Amazon Linux 2023 approach
    sudo yum install docker -y
fi

# Use full service name for better compatibility
sudo systemctl start docker.service
sudo systemctl enable docker.service

echo "Adding user to Docker group..."
sudo usermod -aG docker ec2-user

echo "Installing Git..."
sudo yum install git -y

echo "Installing Docker Compose..."
# Try package manager first, fall back to manual download if not available
if ! sudo yum install docker-compose -y; then
    echo "Docker Compose not found in repositories, installing manually..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create directory if it doesn't exist
echo "Creating application directory..."
mkdir -p /home/ec2-user/fastapi-iot

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
