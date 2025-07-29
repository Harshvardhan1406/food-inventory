#!/bin/bash

# EC2 Deployment Script for Django Food Inventory Application - UBUNTU VERSION
# This script handles the complete deployment process

set -e  # Exit on any error

echo "🚀 Starting deployment process..."

# Variables
APP_DIR="/home/ubuntu/shivam-assignment"
PYTHON_ENV="/home/ubuntu/venv"
LOG_FILE="/home/ubuntu/logs/django.log"
PID_FILE="/home/ubuntu/django.pid"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p /home/ubuntu/logs
mkdir -p /home/ubuntu/media

# Check if virtual environment exists, create if not
if [ ! -d "$PYTHON_ENV" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv $PYTHON_ENV
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source $PYTHON_ENV/bin/activate

# Navigate to application directory
cd $APP_DIR

# Install/update dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Stop existing Django process if running
echo "🛑 Stopping existing Django process..."
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping Django process with PID: $PID"
        kill $PID
        sleep 3
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID
        fi
    fi
    rm -f $PID_FILE
fi

# Kill any remaining Django processes
pkill -f "manage.py runserver" || true

# Run Django migrations
echo "🗃️ Running database migrations..."
python manage.py migrate --noinput

# Start Django development server with nohup
echo "🌟 Starting Django server..."
nohup python manage.py runserver 0.0.0.0:8000 > $LOG_FILE 2>&1 &

# Save PID
echo $! > $PID_FILE

echo "✅ Deployment completed successfully!"
echo "📊 Server is running on port 8000"
echo "📝 Logs are available at: $LOG_FILE"
echo "🆔 Process ID saved to: $PID_FILE"

# Wait a moment and check if server started successfully
sleep 3
if ps -p $(cat $PID_FILE) > /dev/null 2>&1; then
    echo "✅ Django server is running successfully!"
else
    echo "❌ Failed to start Django server. Check logs at $LOG_FILE"
    exit 1
fi 