from django import forms
from django.core.validators import EmailValidator
from .models import (
    Supplier, Category, Product, Batch, Patient, Prescription, PrescriptionItem,
    PurchaseOrder, PurchaseOrderItem, Sale, SaleItem, StockAdjustment, 
    Notification, Billing, Payment, AlertRule, User
    
)

class SupplierForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        validators=[EmailValidator(message="Enter a valid email address.")],
        widget=forms.EmailInput(attrs={
            'placeholder': 'supplier@example.com'
        })
    )
    
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Supplier Company Name'}),
            'contact_person': forms.TextInput(attrs={'placeholder': 'Primary Contact'}),
            'phone': forms.TextInput(attrs={'placeholder': '+1234567890'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Full physical address'}),
            'tax_id': forms.TextInput(attrs={'placeholder': 'Tax Identification Number'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional notes'}),
            'credit_limit': forms.NumberInput(attrs={'step': '0.01'}),
            'current_balance': forms.NumberInput(attrs={'step': '0.01', 'readonly': 'readonly'}),
        }
        labels = {
            'tax_id': 'Tax Identification Number',
            'credit_limit': 'Credit Limit ($)',
            'current_balance': 'Current Balance ($)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['name'].required = True
        self.fields['contact_person'].required = True
        self.fields['phone'].required = True
        self.fields['address'].required = True
        
        # Add form-control class to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'sales_count': forms.HiddenInput(),  # Hide from form since we have default
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sales_count'].required = False  # Make it not required
        self.fields['sales_count'].initial = 0  # Set default value
    
    def clean(self):
        cleaned_data = super().clean()
        cost_price = cleaned_data.get('cost_price')
        selling_price = cleaned_data.get('selling_price')
        
        if cost_price and selling_price and selling_price < cost_price:
            self.add_error('selling_price', 
                         'Selling price cannot be less than cost price')
        return cleaned_data
    
    
class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = '__all__'
        widgets = {
            'manufacture_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_history': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 3}),
        }

from django import forms
from .models import Prescription, PrescriptionItem
from django.contrib.admin.widgets import AdminDateWidget

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient', 'prescribing_doctor', 'date_prescribed', 'status', 'notes']
        widgets = {
            'date_prescribed': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ['product', 'quantity', 'dosage', 'duration', 'instructions']
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Make product field required
        self.fields['product'].required = True
        

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = '__all__'

class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        fields = '__all__'
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = '__all__'
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }

class BillingForm(forms.ModelForm):
    class Meta:
        model = Billing
        fields = ['patient', 'date', 'due_date', 'amount', 'tax_amount', 
                 'discount_amount', 'total_amount', 'payment_status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['amount', 'tax_amount', 'discount_amount', 'total_amount']:
            self.fields[field].widget.attrs.update({'step': '0.01'})

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs.update({'step': '0.01'})


class AlertRuleForm(forms.ModelForm):
    class Meta:
        model = AlertRule
        fields = '__all__'
        widgets = {
            'parameters': forms.Textarea(attrs={'rows': 3}),
            'recipients': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['recipients'].queryset = User.objects.filter(is_active=True)
        
        # Add CSS classes for conditional fields
        self.fields['threshold'].widget.attrs['class'] = 'conditional-field'
        self.fields['days_before'].widget.attrs['class'] = 'conditional-field'
        self.fields['product'].widget.attrs['class'] = 'conditional-field'

class POSForm(forms.Form):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'select2'})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'select2'})
    )
    quantity = forms.IntegerField(min_value=1, initial=1)
    discount = forms.DecimalField(
        min_value=0,
        max_value=100,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['patient', 'payment_method', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

        
class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )


