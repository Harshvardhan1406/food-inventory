#!/bin/bash

# Status Script for Django Food Inventory Application

echo " Checking Django server status..."

PID_FILE="/home/ubuntu/django.pid"
LOG_FILE="/home/ubuntu/logs/django.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo " Django server is running!"
        echo " Process ID: $PID"
        echo " Server should be accessible on port 8000"
        echo "Log file: $LOG_FILE"
        
        # Show last few lines of log
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "📋 Last 10 lines from log file:"
            tail -n 10 $LOG_FILE
        fi
    else
        echo " Django server is not running (stale PID file found)"
        rm -f $PID_FILE
    fi
else
    echo "Django server is not running (no PID file found)"
fi

# Check for any Django processes
DJANGO_PROCESSES=$(pgrep -f "manage.py runserver" || true)
if [ -n "$DJANGO_PROCESSES" ]; then
    echo ""
    echo "🔍 Found Django processes:"
    ps aux | grep "manage.py runserver" | grep -v grep
fi 
