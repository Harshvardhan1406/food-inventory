#!/bin/bash


echo "🔧 Setting up Ubuntu EC2 instance for Django deployment..."

# Update system packages
echo "Updating system packages."
sudo apt update && sudo apt upgrade -y

echo "Installing Python 3 and pip.."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install Git
echo "Installing Git..."
sudo apt install -y git

# Install build essentials (needed for some Python packages)
echo "Installing build essentials.."
sudo apt install -y build-essential libpq-dev

# Install additional dependencies
echo "Installing additional dependencies.."
sudo apt install -y curl wget unzip

# Create application directory
echo "Creating application directories..."
mkdir -p /home/ubuntu/logs
mkdir -p /home/ubuntu/media

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv /home/ubuntu/venv

# Activate virtual environment and upgrade pip
echo "Upgrading pip..."
source /home/ubuntu/venv/bin/activate
pip install --upgrade pip

# Configure Git (optional - for manual updates)
echo " Configuring Git..."
git config --global user.name "EC2 Deployment"
git config --global user.email "deployment@ec2.local"

# Set proper permissions
echo "Setting permissions..."
chmod 755 /home/ubuntu/logs
chmod 755 /home/ubuntu/media

# Create .bashrc alias for convenience
echo "Setting up convenience aliases..."
cat >> /home/ubuntu/.bashrc << 'EOF'

# Django Application Aliases
alias django-start='cd /home/ubuntu/shivam-assignment && bash scripts/deploy.sh'
alias django-stop='cd /home/ubuntu/shivam-assignment && bash scripts/stop.sh'
alias django-status='cd /home/ubuntu/shivam-assignment && bash scripts/status.sh'
alias django-logs='tail -f /home/ubuntu/logs/django.log'
alias django-app='cd /home/ubuntu/shivam-assignment'
EOF

