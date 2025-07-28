from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .dynamodb_models import DynamoDBInventory
from datetime import datetime
import boto3
from django.conf import settings
import uuid

# Initialize DynamoDB
db = DynamoDBInventory()

def get_s3_client():
    return boto3.client('s3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=settings.AWS_SESSION_TOKEN,
        region_name=settings.AWS_S3_REGION_NAME
    )

@csrf_exempt
@require_http_methods(["GET"])
def api_batch_list(request):
    """API endpoint to list all batches"""
    try:
        batches = db.list_batches()
        return JsonResponse({
            'status': 'success',
            'data': batches
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_batch_detail(request, batch_id):
    """API endpoint to get a single batch"""
    try:
        batch = db.get_batch(batch_id)
        if batch:
            return JsonResponse({
                'status': 'success',
                'data': batch
            })
        return JsonResponse({
            'status': 'error',
            'message': 'Batch not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_batch_create(request):
    """API endpoint to create a new batch"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['batch_id', 'product_name', 'production_date', 'expiry_date', 'quantity']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }, status=400)
        
        # Convert date strings to date objects
        production_date = datetime.strptime(data['production_date'], '%Y-%m-%d').date()
        expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
        
        # Calculate status
        days_to_expiry = (expiry_date - datetime.now().date()).days
        if days_to_expiry < 0:
            status = 'Expired'
        elif days_to_expiry <= 7:
            status = 'Expiring Soon'
        else:
            status = 'Safe'
        
        # Prepare batch data
        batch_data = {
            'batch_id': data['batch_id'],
            'product_name': data['product_name'],
            'production_date': data['production_date'],
            'expiry_date': data['expiry_date'],
            'quantity': int(data['quantity']),
            'status': status
        }
        
        # Create batch
        db.create_batch(batch_data)
        
        return JsonResponse({
            'status': 'success',
            'data': batch_data
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def api_batch_update(request, batch_id):
    """API endpoint to update a batch"""
    try:
        # Check if batch exists
        existing_batch = db.get_batch(batch_id)
        if not existing_batch:
            return JsonResponse({
                'status': 'error',
                'message': 'Batch not found'
            }, status=404)
        
        # Get update data
        data = json.loads(request.body)
        
        # Update only provided fields
        update_data = existing_batch.copy()
        update_data.update(data)
        
        # Recalculate status if expiry_date is updated
        if 'expiry_date' in data:
            expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            days_to_expiry = (expiry_date - datetime.now().date()).days
            if days_to_expiry < 0:
                update_data['status'] = 'Expired'
            elif days_to_expiry <= 7:
                update_data['status'] = 'Expiring Soon'
            else:
                update_data['status'] = 'Safe'
        
        # Update batch
        db.update_batch(batch_id, update_data)
        
        return JsonResponse({
            'status': 'success',
            'data': update_data
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def api_batch_delete(request, batch_id):
    """API endpoint to delete a batch"""
    try:
        # Check if batch exists
        batch = db.get_batch(batch_id)
        if not batch:
            return JsonResponse({
                'status': 'error',
                'message': 'Batch not found'
            }, status=404)
        
        # Delete associated image if exists
        if 'image_url' in batch:
            try:
                s3_client = get_s3_client()
                s3_client.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f"media/{batch['image_url']}"
                )
            except Exception as e:
                print(f"Error deleting S3 image: {str(e)}")
        
        # Delete batch
        db.delete_batch(batch_id)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Batch deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_metrics(request):
    """API endpoint to get batch metrics"""
    try:
        batches = db.list_batches()
        
        # Calculate metrics
        total_batches = len(batches)
        status_counts = {'Safe': 0, 'Expiring Soon': 0, 'Expired': 0}
        total_quantity = 0
        
        for batch in batches:
            status = batch.get('status', 'Unknown')
            if status in status_counts:
                status_counts[status] += 1
            total_quantity += int(batch.get('quantity', 0))
        
        metrics = {
            'total_batches': total_batches,
            'status_distribution': status_counts,
            'total_quantity': total_quantity,
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse({
            'status': 'success',
            'data': metrics
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 