import boto3
import os
from datetime import datetime, timedelta
import json

def lambda_handler(event, context):
    try:
        session = boto3.Session(
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            aws_session_token=os.environ['AWS_SESSION_TOKEN'],
            region_name=os.environ['AWS_REGION']
        )
        
        # Initialize DynamoDB and SQS
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table('InventoryBatches')
        sqs = session.client('sqs')
        
        # Get the SQS queue URL from environment variable
        queue_url = os.environ['SQS_QUEUE_URL']
        
        # Scan DynamoDB for all batches
        response = table.scan()
        items = response.get('Items', [])
        updates_made = 0
        notifications = []

        for item in items:
            current_status = item.get('status')
            expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
            days_to_expiry = (expiry_date - datetime.now().date()).days
            
            # Calculate new status
            if days_to_expiry < 0:
                new_status = 'Expired'
            elif days_to_expiry <= 7:
                new_status = 'Expiring Soon'
            else:
                new_status = 'Safe'
            
            # Update status if changed
            if current_status != new_status:
                table.update_item(
                    Key={'batch_id': item['batch_id']},
                    UpdateExpression='SET #status = :status, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': new_status,
                        ':updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                )
                updates_made += 1
                
                # Add to notifications if expired or expiring soon
                if new_status in ['Expired', 'Expiring Soon']:
                    notifications.append({
                        'batch_id': item['batch_id'],
                        'product_name': item['product_name'],
                        'expiry_date': item['expiry_date'],
                        'status': new_status,
                        'days_to_expiry': days_to_expiry
                    })
        
        # Send notifications to SQS if there are any
        if notifications:
            # Group notifications by status
            expired = [n for n in notifications if n['status'] == 'Expired']
            expiring_soon = [n for n in notifications if n['status'] == 'Expiring Soon']
            
            # Create message
            message = {
                'timestamp': datetime.now().isoformat(),
                'total_updates': updates_made,
                'expired_items': expired,
                'expiring_soon_items': expiring_soon
            }
            
            # Send to SQS
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message),
                MessageAttributes={
                    'MessageType': {
                        'DataType': 'String',
                        'StringValue': 'ExpiryUpdate'
                    }
                }
            )
            print(f"Sent notification to SQS for {len(notifications)} items")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully checked {len(items)} batches. Updated {updates_made} items.',
                'notifications_sent': len(notifications)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error processing expiry check: {str(e)}'
            })
        } 