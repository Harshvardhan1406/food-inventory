import boto3
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime
import time

class Command(BaseCommand):
    help = 'Process messages from SQS queue for expiry notifications'

    def handle(self, *args, **options):
        if not hasattr(settings, 'SQS_QUEUE_URL') or not settings.SQS_QUEUE_URL:
            self.stdout.write(self.style.WARNING(
                "SQS_QUEUE_URL not set. SQS processing is disabled."
            ))
            # Sleep to keep the management command running without consuming CPU
            while True:
                time.sleep(60)
            return

        # Initialize SQS client
        sqs = boto3.client('sqs',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        queue_url = settings.SQS_QUEUE_URL
        
        while True:
            try:
                # Receive message from SQS queue
                response = sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20,
                    MessageAttributeNames=['All']
                )
                
                # Check if we received any messages
                messages = response.get('Messages', [])
                if not messages:
                    self.stdout.write("No messages found, continuing...")
                    continue
                
                for message in messages:
                    # Parse message body
                    body = json.loads(message.get('Body', '{}'))
                    
                    # Process expired items
                    expired_items = body.get('expired_items', [])
                    if expired_items:
                        self.stdout.write(self.style.WARNING(
                            f"Found {len(expired_items)} expired items!"
                        ))
                        self._process_expired_items(expired_items)
                    
                    # Process expiring soon items
                    expiring_soon_items = body.get('expiring_soon_items', [])
                    if expiring_soon_items:
                        self.stdout.write(self.style.WARNING(
                            f"Found {len(expiring_soon_items)} items expiring soon!"
                        ))
                        self._process_expiring_soon_items(expiring_soon_items)
                    
                    # Delete processed message
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"Successfully processed message from {body.get('timestamp')}"
                    ))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing messages: {str(e)}"))
                time.sleep(5)  # Wait a bit before retrying on error
    
    def _process_expired_items(self, items):
        """Process expired items - could send emails, update dashboard, etc."""
        message = "EXPIRED ITEMS:\n\n"
        for item in items:
            message += (
                f"- {item['product_name']} (Batch: {item['batch_id']})\n"
                f"  Expired {abs(item['days_to_expiry'])} days ago\n"
            )
        
        self.stdout.write(message)
        # Here you could send emails, Slack notifications, etc.
    
    def _process_expiring_soon_items(self, items):
        """Process items expiring soon"""
        message = "ITEMS EXPIRING SOON:\n\n"
        for item in items:
            message += (
                f"- {item['product_name']} (Batch: {item['batch_id']})\n"
                f"  Expires in {item['days_to_expiry']} days\n"
            )
        
        self.stdout.write(message)
        # Here you could send emails, Slack notifications, etc. 