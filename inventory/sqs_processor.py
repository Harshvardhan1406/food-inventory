import boto3
import json
import threading
import time
from django.conf import settings
from datetime import datetime

class SQSProcessor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        
    def setup_sqs(self):
        """Initialize SQS client"""
        return boto3.client('sqs',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_S3_REGION_NAME
        )
    
    def process_expired_items(self, items):
        """Handle expired items"""
        message = "EXPIRED ITEMS:\n\n"
        for item in items:
            message += (
                f"- {item['product_name']} (Batch: {item['batch_id']})\n"
                f"  Expired {abs(item['days_to_expiry'])} days ago\n"
            )
        print(message)
        # You could add email notifications here
    
    def process_expiring_soon_items(self, items):
        """Handle items expiring soon"""
        message = "ITEMS EXPIRING SOON:\n\n"
        for item in items:
            message += (
                f"- {item['product_name']} (Batch: {item['batch_id']})\n"
                f"  Expires in {item['days_to_expiry']} days\n"
            )
        print(message)
    
    def run(self):
        """Main processing loop"""
        print("Starting SQS message processor...")
        sqs = self.setup_sqs()
        
        while self.running:
            try:
                # Get messages from queue
                response = sqs.receive_message(
                    QueueUrl=settings.SQS_QUEUE_URL,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20,
                    MessageAttributeNames=['All']
                )
                
                messages = response.get('Messages', [])
                if not messages:
                    continue
                
                for message in messages:
                    try:
                        # Parse message
                        body = json.loads(message.get('Body', '{}'))
                        
                        # Process expired items
                        expired_items = body.get('expired_items', [])
                        if expired_items:
                            print(f"Found {len(expired_items)} expired items!")
                            self.process_expired_items(expired_items)
                        
                        # Process expiring soon items
                        expiring_soon_items = body.get('expiring_soon_items', [])
                        if expiring_soon_items:
                            print(f"Found {len(expiring_soon_items)} items expiring soon!")
                            self.process_expiring_soon_items(expiring_soon_items)
                        
                        # Delete processed message
                        sqs.delete_message(
                            QueueUrl=settings.SQS_QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        
                        print(f"Successfully processed message from {body.get('timestamp')}")
                        
                    except json.JSONDecodeError:
                        print("Error decoding message JSON")
                    except Exception as e:
                        print(f"Error processing message: {str(e)}")
                
            except Exception as e:
                print(f"Error in SQS processor: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def stop(self):
        """Stop the processor"""
        self.running = False

# Global processor instance
processor = None

def start_processor():
    """Start the SQS processor"""
    global processor
    if processor is None:
        processor = SQSProcessor()
        processor.start()
        print("SQS Processor started successfully")

def stop_processor():
    """Stop the SQS processor"""
    global processor
    if processor is not None:
        processor.stop()
        processor = None
        print("SQS Processor stopped") 
