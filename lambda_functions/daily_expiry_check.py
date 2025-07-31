import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

def get_dynamodb_table():
    """Get DynamoDB table resource"""
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def send_email(subject, body, recipient):
    """Send email using SES"""
    ses = boto3.client('ses')
    try:
        response = ses.send_email(
            Source=os.environ['SENDER_EMAIL'],
            Destination={
                'ToAddresses': [recipient]
            },
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        return response
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")
        return None

def check_expiry_status(expiry_date):
    """Check expiry status of a batch"""
    expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
    today = datetime.today()
    days = (expiry - today).days
    
    if days < 0:
        return "Expired"
    elif days <= 7:
        return "Expiring Soon"
    return "Safe"

def lambda_handler(event, context):
    """Main Lambda function handler"""
    try:
        # Get DynamoDB table
        table = get_dynamodb_table()
        
        # Scan all items
        response = table.scan()
        items = response.get('Items', [])
        
        # Track items needing attention
        expiring_soon = []
        expired = []
        
        # Check each batch
        for item in items:
            current_status = item.get('status')
            new_status = check_expiry_status(item['expiry_date'])
            
            # Update status if changed
            if current_status != new_status:
                table.update_item(
                    Key={'batch_id': item['batch_id']},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': new_status}
                )
            
            # Track items needing attention
            if new_status == "Expiring Soon":
                expiring_soon.append(item)
            elif new_status == "Expired":
                expired.append(item)

        if expiring_soon or expired:

            subject = "Food Inventory Alert: Items Requiring Attention"
            body = "The following items require your attention:\n\n"
            
            if expired:
                body += "EXPIRED ITEMS:\n"
                for item in expired:
                    body += f"- Batch {item['batch_id']}: {item['product_name']} (Expired on {item['expiry_date']})\n"
                body += "\n"
            
            if expiring_soon:
                body += "EXPIRING SOON:\n"
                for item in expiring_soon:
                    body += f"- Batch {item['batch_id']}: {item['product_name']} (Expires on {item['expiry_date']})\n"
            

            send_email(subject, body, os.environ['NOTIFICATION_EMAIL'])
        
        return {
            'statusCode': 200,
            'body': f'Successfully checked {len(items)} batches. Found {len(expiring_soon)} expiring soon and {len(expired)} expired.'
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error processing expiry check: {str(e)}'
        } 
