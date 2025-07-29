from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Web UI URLs
    path('', views.batch_list, name='batch_list'),
    path('batch/create/', views.batch_create, name='batch_create'),
    path('batch/<str:batch_id>/update/', views.batch_update, name='batch_update'),
    path('batch/<str:batch_id>/delete/', views.batch_delete, name='batch_delete'),
    path('users/', views.user_list, name='user_list'),
    path('dashboard/', views.cloudwatch_dashboard, name='cloudwatch_dashboard'),
    path('supply-requests/', views.supply_request_list, name='supply_request_list'),
    path('supply-requests/create/', views.supply_request_create, name='supply_request_create'),
    path('supply-requests/<int:request_id>/respond/', views.supply_request_respond, name='supply_request_respond'),
    
    # API Endpoints
    path('api/batches/', api_views.api_batch_list, name='api_batch_list'),
    path('api/batches/<str:batch_id>/', api_views.api_batch_detail, name='api_batch_detail'),
    path('api/batches/create/', api_views.api_batch_create, name='api_batch_create'),
    path('api/batches/<str:batch_id>/update/', api_views.api_batch_update, name='api_batch_update'),
    path('api/batches/<str:batch_id>/delete/', api_views.api_batch_delete, name='api_batch_delete'),
    path('api/metrics/', api_views.api_metrics, name='api_metrics'),
] 