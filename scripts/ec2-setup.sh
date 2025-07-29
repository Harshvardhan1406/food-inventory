#!/bin/bash

# EC2 Initial Setup Script for Django Food Inventory Application - UBUNTU VERSION
# Run this script once on a fresh Ubuntu EC2 instance to prepare it for deployment

echo "🔧 Setting up Ubuntu EC2 instance for Django deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+ and pip
echo "🐍 Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install Git
echo "📥 Installing Git..."
sudo apt install -y git

# Install build essentials (needed for some Python packages)
echo "🔨 Installing build essentials..."
sudo apt install -y build-essential libpq-dev

# Install additional dependencies
echo "📚 Installing additional dependencies..."
sudo apt install -y curl wget unzip

# Create application directory
echo "📁 Creating application directories..."
mkdir -p /home/ubuntu/logs
mkdir -p /home/ubuntu/media

# Create Python virtual environment
echo "🔄 Creating Python virtual environment..."
python3 -m venv /home/ubuntu/venv

# Activate virtual environment and upgrade pip
echo "⬆️ Upgrading pip..."
source /home/ubuntu/venv/bin/activate
pip install --upgrade pip

# Configure Git (optional - for manual updates)
echo "⚙️ Configuring Git..."
git config --global user.name "EC2 Deployment"
git config --global user.email "deployment@ec2.local"

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 /home/ubuntu/logs
chmod 755 /home/ubuntu/media

# Create .bashrc alias for convenience
echo "🔗 Setting up convenience aliases..."
cat >> /home/ubuntu/.bashrc << 'EOF'

# Django Application Aliases
alias django-start='cd /home/ubuntu/shivam-assignment && bash scripts/deploy.sh'
alias django-stop='cd /home/ubuntu/shivam-assignment && bash scripts/stop.sh'
alias django-status='cd /home/ubuntu/shivam-assignment && bash scripts/status.sh'
alias django-logs='tail -f /home/ubuntu/logs/django.log'
alias django-app='cd /home/ubuntu/shivam-assignment'
EOF

echo "✅ Ubuntu EC2 setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Configure your GitHub repository secrets:"
echo "   - EC2_SSH_PRIVATE_KEY: Your EC2 private key"
echo "   - EC2_HOST: This instance's public IP"
echo "   - EC2_USER: ubuntu"
echo ""
echo "2. Configure security group to allow inbound traffic on port 8000"
echo ""
echo "3. Push code to your main branch to trigger deployment"
echo ""
echo "🔗 Useful aliases added to ~/.bashrc:"
echo "   django-start   - Deploy and start the application"
echo "   django-stop    - Stop the application"
echo "   django-status  - Check application status"
echo "   django-logs    - View live logs"
echo "   django-app     - Navigate to app directory"
echo ""
echo "💡 Reload your shell or run 'source ~/.bashrc' to use aliases" 