#!/bin/bash

# Fix Environment Variables Script
echo "Fixing environment variables..."

# Create a clean .env file
cat > /home/ubuntu/.env << 'EOF'
DJANGO_SECRET_KEY=django-insecure-temp-key-please-change-this-asap-123456789
DJANGO_DEBUG=True
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1
SQS_QUEUE_URL=
EOF

echo "Created clean .env file"

# Load environment variables properly
set -o allexport
source /home/ubuntu/.env
set +o allexport

echo "Environment variables loaded"

# Show what's loaded
echo "Current environment:"
echo "DJANGO_SECRET_KEY: $(if [ -n "$DJANGO_SECRET_KEY" ]; then echo "SET"; else echo "NOT SET"; fi)"
echo "DJANGO_DEBUG: $DJANGO_DEBUG"

echo "Now you can run: bash scripts/deploy.sh" 
