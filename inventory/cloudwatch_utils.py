import boto3
import json
from datetime import datetime, timedelta
from django.conf import settings

class CloudWatchManager:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        self.logs_client = boto3.client('logs',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_S3_REGION_NAME
        )

    def put_metric(self, metric_name, value, unit='Count', namespace='FoodInventory', dimensions=None):
        """Put a custom metric to CloudWatch"""
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = dimensions

            response = self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[metric_data]
            )
            return True
        except Exception as e:
            print(f"Error putting metric {metric_name}: {str(e)}")
            return False

    def update_batch_status_metrics(self, batches):
        """Update batch status metrics with current counts"""
        try:
            # Calculate current counts
            status_counts = {'Safe': 0, 'Expiring Soon': 0, 'Expired': 0}
            for batch in batches:
                status = batch.get('status', 'Unknown')
                if status in status_counts:
                    status_counts[status] += 1

            # Update metrics with current counts
            timestamp = datetime.utcnow()
            for status, count in status_counts.items():
                self.put_metric(
                    f'Total{status.replace(" ", "")}Batches',
                    count,
                    dimensions=[{
                        'Name': 'Type',
                        'Value': 'CurrentCount'
                    }]
                )

            return True
        except Exception as e:
            print(f"Error updating batch status metrics: {str(e)}")
            return False

    def put_batch_metrics(self, batch_data, action='created'):
        """Put batch-related metrics"""
        try:
            # Put action metric (created, updated, deleted)
            self.put_metric(f'Batch{action.capitalize()}', 1)
            
            # Put quantity metric if provided
            if 'quantity' in batch_data:
                self.put_metric('TotalQuantity', batch_data['quantity'], 'Count')
            
            return True
        except Exception as e:
            print(f"Error putting batch metrics: {str(e)}")
            return False

    def log_event(self, log_group_name, log_stream_name, message, level='INFO'):
        """Send log event to CloudWatch Logs"""
        try:
            # Create log group if it doesn't exist
            try:
                self.logs_client.create_log_group(logGroupName=log_group_name)
            except self.logs_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Create log stream if it doesn't exist
            try:
                self.logs_client.create_log_stream(
                    logGroupName=log_group_name,
                    logStreamName=log_stream_name
                )
            except self.logs_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Get sequence token
            response = self.logs_client.describe_log_streams(
                logGroupName=log_group_name,
                logStreamNamePrefix=log_stream_name
            )
            
            sequence_token = None
            if response['logStreams']:
                sequence_token = response['logStreams'][0].get('uploadSequenceToken')
            
            # Prepare log event
            log_event = {
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                'message': f"[{level}] {datetime.utcnow().isoformat()} - {message}"
            }
            
            # Put log event
            put_log_params = {
                'logGroupName': log_group_name,
                'logStreamName': log_stream_name,
                'logEvents': [log_event]
            }
            
            if sequence_token:
                put_log_params['sequenceToken'] = sequence_token
            
            self.logs_client.put_log_events(**put_log_params)
            return True
            
        except Exception as e:
            print(f"Error logging to CloudWatch: {str(e)}")
            return False

    def create_alarm(self, alarm_name, metric_name, threshold, comparison_operator='GreaterThanThreshold'):
        """Create a CloudWatch alarm"""
        try:
            response = self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator=comparison_operator,
                EvaluationPeriods=1,
                MetricName=metric_name,
                Namespace='FoodInventory',
                Period=300,  # 5 minutes
                Statistic='Sum',
                Threshold=threshold,
                ActionsEnabled=True,
                AlarmDescription=f'Alarm for {metric_name} in Food Inventory System',
                Unit='Count'
            )
            return True
        except Exception as e:
            print(f"Error creating alarm {alarm_name}: {str(e)}")
            return False

    def get_current_metrics(self, metric_name):
        """Get the most recent metric value"""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='FoodInventory',
                MetricName=metric_name,
                StartTime=datetime.utcnow() - timedelta(minutes=5),  # Last 5 minutes
                EndTime=datetime.utcnow(),
                Period=300,  # 5 minutes
                Statistics=['Maximum'],
                Dimensions=[{
                    'Name': 'Type',
                    'Value': 'CurrentCount'
                }]
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                return sorted(datapoints, key=lambda x: x['Timestamp'])[-1]['Maximum']
            return 0
        except Exception as e:
            print(f"Error getting current metric for {metric_name}: {str(e)}")
            return 0

    def get_metrics(self, metric_name, start_time, end_time, namespace='FoodInventory'):
        """Get metric statistics from CloudWatch"""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Maximum'],
                Dimensions=[{
                    'Name': 'Type',
                    'Value': 'CurrentCount'
                }]
            )
            return response.get('Datapoints', [])
        except Exception as e:
            print(f"Error getting metrics for {metric_name}: {str(e)}")
            return []

# Initialize CloudWatch manager
cloudwatch_manager = CloudWatchManager() 