#!/bin/bash

# Stop Script for Django Food Inventory Application

echo "🛑 Stopping Django server..."

PID_FILE="/home/ubuntu/django.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping Django process with PID: $PID"
        kill $PID
        sleep 3
        
        # Check if process is still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Process still running, force killing..."
            kill -9 $PID
        fi
        
        rm -f $PID_FILE
        echo "✅ Django server stopped successfully!"
    else
        echo "⚠️ No running process found with PID: $PID"
        rm -f $PID_FILE
    fi
else
    echo "⚠️ PID file not found. Attempting to kill any running Django processes..."
    pkill -f "manage.py runserver" || echo "No Django processes found"
fi

echo "🏁 Stop process completed!" 