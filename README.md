# Food Inventory and Expiry Management System

A cloud-based web application for food manufacturers to track food inventory batches and monitor expiry dates.

## Features

- Inventory Management (CRUD operations)
- Automatic Expiry Status Updates
- Daily Email Notifications for Expiring Items
- Image Upload Support
- Responsive Design

## Tech Stack

- Django (Backend)
- Tailwind CSS (Frontend)
- AWS Services:
  - S3 (Image Storage)
  - DynamoDB (Database)
  - Lambda (Daily Expiry Check)
  - SES (Email Notifications)
  - API Gateway

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd food-inventory
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file in the project root with the following variables:
```
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=your-aws-region
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-email-password
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## AWS Lambda Setup

1. Create a new Lambda function in AWS Console
2. Set up environment variables:
   - DYNAMODB_TABLE
   - SENDER_EMAIL
   - NOTIFICATION_EMAIL

3. Create an EventBridge (CloudWatch Events) rule to trigger the Lambda function daily

4. Set up necessary IAM roles with permissions for:
   - DynamoDB
   - SES
   - CloudWatch Logs

5. Deploy the Lambda function:
   - Zip the contents of `lambda_functions/`
   - Upload to AWS Lambda

## Usage

1. Access the admin interface at `/admin`
2. Add/Edit/Delete inventory batches
3. View batch status on the dashboard
4. Receive daily email notifications for expiring items

## License

MIT License 