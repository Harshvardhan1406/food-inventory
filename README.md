# Food Inventory Management System

A Django-based web application for managing food inventory with expiration tracking and AWS integration.

## 🚀 EC2 Deployment

This application is configured for simple deployment on Amazon EC2 using GitHub Actions.

### Prerequisites

1. **EC2 Instance**: Amazon Linux 2 or Ubuntu server
2. **Python 3.8+**: Installed on the EC2 instance
3. **Git**: For cloning the repository
4. **Security Group**: Allow inbound traffic on port 8000

### GitHub Secrets Setup

Configure the following secrets in your GitHub repository:

- `EC2_SSH_PRIVATE_KEY`: Your EC2 private key (PEM format)
- `EC2_HOST`: Your EC2 instance public IP or domain
- `EC2_USER`: SSH username (`ubuntu` for Ubuntu, `ec2-user` for Amazon Linux)

### Deployment Process

The deployment is fully automated via GitHub Actions:

1. **Push to main branch** triggers the deployment
2. **Code sync** via rsync to EC2
3. **Dependencies installation** in a Python virtual environment
4. **Database migrations** are applied automatically
5. **Django server startup** using `nohup python manage.py runserver`

### Manual Management Scripts

SSH into your EC2 instance and use these scripts:

```bash
# Deploy/Start the application
cd /home/ec2-user/shivam-assignment
bash scripts/deploy.sh

# Stop the application
bash scripts/stop.sh

# Check application status
bash scripts/status.sh
```

### Server Details

- **Port**: 8000
- **Logs**: `/home/ubuntu/logs/django.log` (Ubuntu) or `/home/ec2-user/logs/django.log` (Amazon Linux)
- **PID File**: `/home/ubuntu/django.pid` (Ubuntu) or `/home/ec2-user/django.pid` (Amazon Linux)
- **Media Files**: `/home/ubuntu/media` (Ubuntu) or `/home/ec2-user/media` (Amazon Linux)

### Accessing the Application

After deployment, access your application at:
```
http://your-ec2-public-ip:8000
```

### Features

- 🍎 Food item management with expiration tracking
- 📸 Image upload to AWS S3
- ⚡ AWS SQS integration for notifications
- 🔔 Automated expiry alerts via Lambda functions
- 👥 User authentication and authorization
- 📱 Responsive web interface

### Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Start development server: `python manage.py runserver`

### Environment Variables

Create a `.env` file on your EC2 instance:

**For Ubuntu:** `/home/ubuntu/.env`
**For Amazon Linux:** `/home/ec2-user/.env`

```env
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
DJANGO_DEBUG=False

# AWS S3 Settings (for file uploads)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=us-east-1

# AWS SQS Settings (for notifications)
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/your-account/your-queue

# Database Settings (optional - uses SQLite by default)
# RDS_HOSTNAME=your-rds-endpoint
# RDS_DB_NAME=your-database-name  
# RDS_USERNAME=your-db-username
# RDS_PASSWORD=your-db-password
# RDS_PORT=5432
```

### Support

For deployment issues, check:
1. EC2 security group settings (port 8000 open)
2. GitHub Actions logs
3. Application logs at `/home/ubuntu/logs/django.log` (Ubuntu) or `/home/ec2-user/logs/django.log` (Amazon Linux)
4. Server status using `bash scripts/status.sh`

### Quick Setup Commands

**For Ubuntu EC2:**
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Setup (one-time)
curl -o setup.sh https://raw.githubusercontent.com/your-repo/shivam-assignment/main/scripts/ec2-setup-ubuntu.sh
chmod +x setup.sh && bash setup.sh
```

**For Amazon Linux EC2:**
```bash
# SSH into instance  
ssh -i your-key.pem ec2-user@your-ec2-ip

# Setup (one-time)
curl -o setup.sh https://raw.githubusercontent.com/your-repo/shivam-assignment/main/scripts/ec2-setup.sh
chmod +x setup.sh && bash setup.sh
``` 