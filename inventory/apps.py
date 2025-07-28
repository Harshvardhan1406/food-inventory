from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    
    def ready(self):
        """Start background tasks when Django starts"""
        # Import and start SQS processor
        from .sqs_processor import start_processor
        start_processor()
