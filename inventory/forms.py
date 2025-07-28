from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import InventoryBatch, User

class InventoryBatchForm(forms.ModelForm):
    production_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = InventoryBatch
        fields = ['batch_id', 'product_name', 'production_date', 'expiry_date', 'quantity', 'image']
        widgets = {
            'batch_id': forms.TextInput(attrs={'class': 'form-input'}),
            'product_name': forms.TextInput(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input'}),
        }

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'department', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'role': forms.Select(attrs={'class': 'form-input'}),
            'department': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'department', 'phone')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'department': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
        } 