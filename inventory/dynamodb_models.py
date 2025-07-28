import boto3
from django.conf import settings
from datetime import datetime

class DynamoDBInventory:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.table = self.dynamodb.Table('InventoryBatches')
        self.s3_client = boto3.client('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_S3_REGION_NAME
        )

    def get_presigned_url(self, image_path):
        """Generate a pre-signed URL for the image"""
        if image_path:
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': f'media/{image_path}'
                    },
                    ExpiresIn=3600  # URL valid for 1 hour
                )
                return url
            except Exception as e:
                print(f"Error generating pre-signed URL: {str(e)}")
                return None
        return None

    def create_batch(self, batch_data):
        """Create a new batch in DynamoDB"""
        item = {
            'batch_id': batch_data['batch_id'],
            'product_name': batch_data['product_name'],
            'production_date': batch_data['production_date'].strftime('%Y-%m-%d'),
            'expiry_date': batch_data['expiry_date'].strftime('%Y-%m-%d'),
            'quantity': batch_data['quantity'],
            'status': batch_data['status'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if batch_data.get('image'):
            item['image_url'] = batch_data['image']
        
        return self.table.put_item(Item=item)

    def get_batch(self, batch_id):
        """Get a batch by ID"""
        response = self.table.get_item(Key={'batch_id': batch_id})
        item = response.get('Item')
        if item and item.get('image_url'):
            item['presigned_url'] = self.get_presigned_url(item['image_url'])
        return item

    def update_batch(self, batch_id, update_data):
        """Update a batch"""
        update_expr = "SET "
        expr_values = {}
        expr_names = {}
        
        # Build update expression
        for key, value in update_data.items():
            if key != 'batch_id':  # Skip primary key
                update_expr += f"#{key} = :{key}, "
                expr_names[f"#{key}"] = key
                expr_values[f":{key}"] = value if not isinstance(value, datetime) else value.isoformat()
        
        # Add updated_at timestamp
        update_expr += "#updated_at = :updated_at"
        expr_names["#updated_at"] = "updated_at"
        expr_values[":updated_at"] = datetime.now().isoformat()

        return self.table.update_item(
            Key={'batch_id': batch_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )

    def delete_batch(self, batch_id):
        """Delete a batch"""
        return self.table.delete_item(Key={'batch_id': batch_id})

    def list_batches(self):
        """List all batches"""
        response = self.table.scan()
        items = response.get('Items', [])
        
        # Add pre-signed URLs for images
        for item in items:
            if item.get('image_url'):
                item['presigned_url'] = self.get_presigned_url(item['image_url'])
        
        return items 