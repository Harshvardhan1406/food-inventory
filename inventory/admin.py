from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import InventoryBatch, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'department', 'phone')}),
        ('Roles', {'fields': ('role', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'department'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'department')
    ordering = ('username',)

@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_id', 'product_name', 'expiry_date', 'quantity', 'status')
    list_filter = ('status',)
    search_fields = ('batch_id', 'product_name')
    ordering = ('expiry_date',)
