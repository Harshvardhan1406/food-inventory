from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from .expiry_tracker import ExpiryTracker
import boto3
import uuid
import os

def get_s3_client():
    return boto3.client('s3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=settings.AWS_SESSION_TOKEN,
        region_name=settings.AWS_S3_REGION_NAME
    )

class User(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)

    # Fix the reverse accessor clash
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set'  # Custom related_name
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set'  # Custom related_name
    )
    
    def is_manager(self):
        return self.role == 'manager'

    class Meta:
        db_table = 'custom_user'  # Custom table name
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class InventoryBatch(models.Model):
    STATUS_CHOICES = [
        ('Safe', 'Safe'),
        ('Expiring Soon', 'Expiring Soon'),
        ('Expired', 'Expired'),
    ]

    batch_id = models.CharField(max_length=50, primary_key=True)
    product_name = models.CharField(max_length=200)
    production_date = models.DateField()
    expiry_date = models.DateField()
    quantity = models.IntegerField()
    image = models.CharField(max_length=255, null=True, blank=True)  # Store S3 path
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Safe')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_batches')
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_batches')

    def update_status(self):
        """Update the status based on expiry date"""
        tracker = ExpiryTracker(self.expiry_date.strftime("%Y-%m-%d"))
        self.status = tracker.get_status()
        self.save()

    @property
    def image_url(self):
        """Get a pre-signed URL for the image"""
        if self.image:
            try:
                s3_client = get_s3_client()
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': f'media/{self.image}'
                    },
                    ExpiresIn=3600  # URL valid for 1 hour
                )
                return url
            except Exception as e:
                print(f"Error generating pre-signed URL: {str(e)}")
                return None
        return None

    def __str__(self):
        return f"{self.batch_id} - {self.product_name} ({self.status})"

    class Meta:
        ordering = ['expiry_date']
