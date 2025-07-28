#!/bin/bash

# Make script executable
chmod +x /var/app/staging/manage.py

# Create directories if they don't exist
mkdir -p /var/app/staging/static
mkdir -p /var/app/staging/media

# Set permissions
chmod 755 /var/app/staging/static
chmod 755 /var/app/staging/media 