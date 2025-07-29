from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.conf import settings
from .models import InventoryBatch, User
from .forms import InventoryBatchForm, CustomUserCreationForm, UserProfileForm
import boto3
import uuid
import os
from .dynamodb_models import DynamoDBInventory
from datetime import datetime
from .cloudwatch_utils import cloudwatch_manager
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import SupplyRequest

def get_s3_client():
    return boto3.client('s3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=settings.AWS_SESSION_TOKEN,
        region_name=settings.AWS_S3_REGION_NAME
    )

def upload_to_s3(file, filename):
    s3_client = get_s3_client()
    try:
        # Reset file pointer
        file.seek(0)
        
        # Upload to S3
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            f'media/product_images/{filename}',
            ExtraArgs={
                'ContentType': file.content_type
            }
        )
        print(f"File uploaded to S3: media/product_images/{filename}")
        
        # Log to CloudWatch
        cloudwatch_manager.log_event(
            'FoodInventory/S3', 
            'uploads', 
            f"Image uploaded: {filename}"
        )
        
        return f'product_images/{filename}'
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        
        # Log error to CloudWatch
        cloudwatch_manager.log_event(
            'FoodInventory/S3', 
            'errors', 
            f"S3 upload failed: {str(e)}", 
            'ERROR'
        )
        
        return None

def delete_from_s3(file_path):
    if not file_path:
        return
    
    s3_client = get_s3_client()
    try:
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=f'media/{file_path}'
        )
        
        # Log to CloudWatch
        cloudwatch_manager.log_event(
            'FoodInventory/S3', 
            'deletes', 
            f"Image deleted: {file_path}"
        )
        
    except Exception as e:
        print(f"Error deleting from S3: {str(e)}")
        
        # Log error to CloudWatch
        cloudwatch_manager.log_event(
            'FoodInventory/S3', 
            'errors', 
            f"S3 delete failed: {str(e)}", 
            'ERROR'
        )

def is_manufacturer(user):
    return user.is_authenticated and user.is_manufacturer()

@ensure_csrf_cookie
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Registration successful!',
                        'redirect_url': '/batch_list/'
                    })
                messages.success(request, 'Registration successful!')
                return redirect('batch_list')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': str(e)
                    }, status=500)
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = CustomUserCreationForm()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        }, status=405)
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'registration/profile.html', {'form': form})

# Initialize DynamoDB
db = DynamoDBInventory()

@login_required
def batch_list(request):
    # Get all batches from DynamoDB
    batches = db.list_batches()
    
    # Log page view
    cloudwatch_manager.log_event(
        'FoodInventory/Views', 
        'page_views', 
        'Batch list viewed'
    )
    
    # Put metric for page views
    cloudwatch_manager.put_metric('PageViews', 1)
    
    # Filter by status if specified
    status_filter = request.GET.get('status', '')
    if status_filter and status_filter != 'All':
        batches = [b for b in batches if b['status'] == status_filter]
    
    # Convert date strings to datetime objects for template
    for batch in batches:
        batch['expiry_date'] = datetime.strptime(batch['expiry_date'], '%Y-%m-%d').date()
        batch['production_date'] = datetime.strptime(batch['production_date'], '%Y-%m-%d').date()
        # Add edit permission flag
        batch['can_edit'] = request.user.is_manufacturer()
    
    # Update batch status metrics
    cloudwatch_manager.update_batch_status_metrics(batches)
    
    context = {
        'batches': batches,
        'status_filter': status_filter,
        'status_choices': ['All', 'Safe', 'Expiring Soon', 'Expired'],
        'AWS_STORAGE_BUCKET_NAME': settings.AWS_STORAGE_BUCKET_NAME,
        'AWS_S3_REGION_NAME': settings.AWS_S3_REGION_NAME,
        'debug': settings.DEBUG,
        'is_manufacturer': request.user.is_manufacturer(),
    }
    return render(request, 'inventory/batch_list.html', context)

@login_required
@user_passes_test(is_manufacturer)
def batch_create(request):
    if request.method == 'POST':
        # Get form data
        batch_data = {
            'batch_id': request.POST['batch_id'],
            'product_name': request.POST['product_name'],
            'production_date': datetime.strptime(request.POST['production_date'], '%Y-%m-%d').date(),
            'expiry_date': datetime.strptime(request.POST['expiry_date'], '%Y-%m-%d').date(),
            'quantity': int(request.POST['quantity']),
        }
        
        # Calculate status based on expiry date
        days_to_expiry = (batch_data['expiry_date'] - datetime.now().date()).days
        if days_to_expiry < 0:
            batch_data['status'] = 'Expired'
        elif days_to_expiry <= 7:
            batch_data['status'] = 'Expiring Soon'
        else:
            batch_data['status'] = 'Safe'
        
        # Handle image upload
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            filename = f"{batch_data['batch_id']}{os.path.splitext(image_file.name)[1]}"
            s3_path = upload_to_s3(image_file, filename)
            if s3_path:
                batch_data['image'] = s3_path
                print(f"Image uploaded successfully. Path: {s3_path}")
            else:
                print("Failed to upload image to S3")
        
        # Save to DynamoDB
        try:
            db.create_batch(batch_data)
            
            # Log successful batch creation
            cloudwatch_manager.log_event(
                'FoodInventory/Batches', 
                'operations', 
                f"Batch created: {batch_data['batch_id']} - {batch_data['product_name']}"
            )
            
            # Put batch metrics
            cloudwatch_manager.put_batch_metrics(batch_data, 'created')
            
            messages.success(request, 'Batch created successfully!')
            return redirect('batch_list')
        except Exception as e:
            # Log error
            cloudwatch_manager.log_event(
                'FoodInventory/Batches', 
                'errors', 
                f"Batch creation failed: {str(e)}", 
                'ERROR'
            )
            
            messages.error(request, f'Error creating batch: {str(e)}')
            print(f"Error creating batch: {str(e)}")
    
    return render(request, 'inventory/batch_form.html', {
        'title': 'Create Batch',
        'AWS_STORAGE_BUCKET_NAME': settings.AWS_STORAGE_BUCKET_NAME,
        'AWS_S3_REGION_NAME': settings.AWS_S3_REGION_NAME,
        'debug': settings.DEBUG,
    })

@login_required
@user_passes_test(is_manufacturer)
def batch_update(request, batch_id):
    # Get existing batch
    batch = db.get_batch(batch_id)
    if not batch:
        messages.error(request, 'Batch not found!')
        return redirect('batch_list')
    
    if request.method == 'POST':
        # Update batch data
        update_data = {
            'product_name': request.POST['product_name'],
            'production_date': datetime.strptime(request.POST['production_date'], '%Y-%m-%d').date(),  # Convert to date
            'expiry_date': datetime.strptime(request.POST['expiry_date'], '%Y-%m-%d').date(),  # Convert to date
            'quantity': int(request.POST['quantity']),
        }
        
        # Calculate status
        days_to_expiry = (update_data['expiry_date'] - datetime.now().date()).days
        if days_to_expiry < 0:
            update_data['status'] = 'Expired'
        elif days_to_expiry <= 7:
            update_data['status'] = 'Expiring Soon'
        else:
            update_data['status'] = 'Safe'
        
        # Handle image upload
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            s3_path = upload_to_s3(image_file, f"{batch_id}{os.path.splitext(image_file.name)[1]}")
            if s3_path:
                update_data['image'] = s3_path
        
        # Update in DynamoDB
        try:
            db.update_batch(batch_id, update_data)
            messages.success(request, 'Batch updated successfully!')
            return redirect('batch_list')
        except Exception as e:
            messages.error(request, f'Error updating batch: {str(e)}')
    
    # Convert date strings to date objects for form
    batch['expiry_date'] = datetime.strptime(batch['expiry_date'], '%Y-%m-%d').date()
    batch['production_date'] = datetime.strptime(batch['production_date'], '%Y-%m-%d').date()
    
    return render(request, 'inventory/batch_form.html', {
        'title': 'Update Batch',
        'batch': batch
    })

@login_required
@user_passes_test(is_manufacturer)
def batch_delete(request, batch_id):
    batch = db.get_batch(batch_id)
    if not batch:
        messages.error(request, 'Batch not found!')
        return redirect('batch_list')
    
    if request.method == 'POST':
        try:
            # Delete from DynamoDB
            db.delete_batch(batch_id)
            
            # Delete image from S3 if exists
            if batch.get('image'):
                delete_from_s3(batch['image'])
            
            messages.success(request, 'Batch deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting batch: {str(e)}')
        
        return redirect('batch_list')
    
    return render(request, 'inventory/batch_confirm_delete.html', {'batch': batch})

@login_required
@user_passes_test(is_manufacturer)
def user_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'inventory/user_list.html', {'users': users})

@login_required
def cloudwatch_dashboard(request):
    """Display CloudWatch metrics dashboard"""
    try:
        from datetime import timedelta
        
        # Get current metrics
        metrics_data = {
            'total_expired_batches': [{
                'Maximum': cloudwatch_manager.get_current_metrics('TotalExpiredBatches')
            }],
            'total_expiring_soon_batches': [{
                'Maximum': cloudwatch_manager.get_current_metrics('TotalExpiringSoonBatches')
            }],
            'total_safe_batches': [{
                'Maximum': cloudwatch_manager.get_current_metrics('TotalSafeBatches')
            }],
        }
        
        # Get historical metrics for trends (last 24 hours)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        metrics_data.update({
            'page_views': cloudwatch_manager.get_metrics('PageViews', start_time, end_time),
            'batch_created': cloudwatch_manager.get_metrics('BatchCreated', start_time, end_time),
        })
        
        # Calculate summary statistics
        total_batches = len(db.list_batches())
        
        context = {
            'metrics_data': metrics_data,
            'total_batches': total_batches,
            'start_time': start_time,
            'end_time': end_time,
        }
        
        return render(request, 'inventory/cloudwatch_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('batch_list')

@login_required
def supply_request_list(request):
    """View supply requests based on user role"""
    if request.user.is_manufacturer():
        # Manufacturers see all requests
        requests = SupplyRequest.objects.all()
    else:
        # Suppliers see only their requests
        requests = request.user.supply_requests.all()
    
    return render(request, 'inventory/supply_request_list.html', {
        'requests': requests,
        'is_manufacturer': request.user.is_manufacturer()
    })

@login_required
def supply_request_create(request):
    """Create a new supply request (suppliers only)"""
    if request.user.is_manufacturer():
        messages.error(request, 'Only suppliers can create supply requests.')
        return redirect('supply_request_list')
    
    if request.method == 'POST':
        try:
            request_data = {
                'supplier': request.user,
                'product_name': request.POST['product_name'],
                'quantity': int(request.POST['quantity']),
                'description': request.POST.get('description', ''),
            }
            supply_request = SupplyRequest.objects.create(**request_data)
            messages.success(request, 'Supply request created successfully!')
            return redirect('supply_request_list')
        except Exception as e:
            messages.error(request, f'Error creating supply request: {str(e)}')
    
    return render(request, 'inventory/supply_request_form.html', {
        'title': 'Create Supply Request'
    })

@login_required
@user_passes_test(is_manufacturer)
def supply_request_respond(request, request_id):
    """Respond to a supply request (manufacturers only)"""
    supply_request = get_object_or_404(SupplyRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ['approve', 'reject']:
            supply_request.status = 'approved' if action == 'approve' else 'rejected'
            supply_request.save()
            messages.success(request, f'Supply request {supply_request.status}.')
        return redirect('supply_request_list')
    
    return render(request, 'inventory/supply_request_respond.html', {
        'supply_request': supply_request
    })
