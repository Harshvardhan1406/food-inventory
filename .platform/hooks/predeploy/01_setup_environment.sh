#!/bin/bash

# Exit on error
set -e

# Setup logging
exec 1> >(logger -s -t $(basename $0)) 2>&1

echo "Starting environment setup..."

# Create log directory
mkdir -p /var/log/app-logs
touch /var/log/app-logs/django.log
touch /var/log/app-logs/django.err
chmod 777 /var/log/app-logs/django.log
chmod 777 /var/log/app-logs/django.err

# Make script executable
echo "Making manage.py executable..."
chmod +x /var/app/staging/manage.py

# Create directories if they don't exist
echo "Creating static and media directories..."
mkdir -p /var/app/staging/static
mkdir -p /var/app/staging/media

# Set permissions
echo "Setting directory permissions..."
chmod 755 /var/app/staging/static
chmod 755 /var/app/staging/media

echo "Environment setup completed successfully" 