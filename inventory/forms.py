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
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    department = forms.CharField(required=False)
    phone = forms.CharField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'department', 'phone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input rounded-md'}),
            'email': forms.EmailInput(attrs={'class': 'form-input rounded-md'}),
            'role': forms.Select(attrs={'class': 'form-select rounded-md'}),
            'department': forms.TextInput(attrs={'class': 'form-input rounded-md'}),
            'phone': forms.TextInput(attrs={'class': 'form-input rounded-md'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input rounded-md'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input rounded-md'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists')
        return email

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'department', 'phone')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'department': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
        } 