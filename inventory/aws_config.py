import boto3
import os
from django.conf import settings

# Initialize AWS services
def get_s3_client():
    return boto3.client('s3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

def get_dynamodb_resource():
    return boto3.resource('dynamodb',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

def get_cloudwatch_client():
    return boto3.client('cloudwatch',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

# S3 functions
def upload_file_to_s3(file, filename):
    """Upload a file to S3 bucket"""
    s3_client = get_s3_client()
    try:
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            f'product_images/{filename}',
            ExtraArgs={'ACL': 'public-read'}
        )
        return f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/product_images/{filename}'
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return None

# DynamoDB functions
def sync_to_dynamodb(batch):
    """Sync an inventory batch to DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('InventoryBatches')
    
    try:
        item = {
            'batch_id': batch.batch_id,
            'product_name': batch.product_name,
            'production_date': batch.production_date.isoformat(),
            'expiry_date': batch.expiry_date.isoformat(),
            'quantity': batch.quantity,
            'status': batch.status,
            'image_url': str(batch.image.url) if batch.image else None,
        }
        table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"Error syncing to DynamoDB: {str(e)}")
        return False

# CloudWatch functions
def log_batch_metrics(batch):
    """Log batch metrics to CloudWatch"""
    cloudwatch = get_cloudwatch_client()
    try:
        cloudwatch.put_metric_data(
            Namespace='FoodInventory',
            MetricData=[
                {
                    'MetricName': 'BatchQuantity',
                    'Value': batch.quantity,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'BatchId',
                            'Value': batch.batch_id
                        },
                        {
                            'Name': 'Status',
                            'Value': batch.status
                        }
                    ]
                }
            ]
        )
        return True
    except Exception as e:
        print(f"Error logging to CloudWatch: {str(e)}")
        return False 