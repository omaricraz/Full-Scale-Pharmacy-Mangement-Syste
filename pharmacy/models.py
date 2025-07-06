from datetime import date, datetime
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from django_countries.fields import CountryField

User = get_user_model()

class Supplier(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ON_HOLD', 'On Hold'),
    ]

    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tax ID")
    credit_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    current_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'

    def save(self, *args, **kwargs):
        # Ensure balance doesn't exceed credit limit
        if self.current_balance > self.credit_limit and self.credit_limit > 0:
            self.status = 'ON_HOLD'
        super().save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

class Product(models.Model):
    TYPE_CHOICES = (
        ('drug', 'Drug'),
        ('non_drug', 'Non-Drug'),
    )
    
    name = models.CharField(max_length=100)
    made_in = CountryField(blank=True, null=True)
    generic_name = models.CharField(max_length=100, blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    product_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='drug')
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=20)
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    min_stock_level = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    sales_count = models.PositiveIntegerField(default=0)  # Default value set here
    
    def __str__(self):
        return f"{self.name} ({self.generic_name})" if self.generic_name else self.name
    
    def get_stock_quantity(self):
        result = self.batches.filter(
            quantity__gt=0,
            expiry_date__gt=date.today()
        ).aggregate(total=Sum('quantity'))
        return result['total'] if result['total'] is not None else 0
    
    def get_stock_info(self):
        stock_qty = self.get_stock_quantity()
        batches = self.batches.filter(
            quantity__gt=0,
            expiry_date__gt=date.today()
        ).order_by('expiry_date')
        
        return {
            'total': stock_qty,
            'batch_count': batches.count(),
            'batches': batches
        }
    
    @property
    def has_stock(self):
        return self.get_stock_quantity() > 0
    
    @property
    def is_low_stock(self):
        return self.get_stock_quantity() <= self.min_stock_level
    
    @property
    def profit_margin(self):
        if not self.cost_price or self.cost_price == 0:
            return 0
        margin = ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return round(margin, 2)
    
    class Meta:
        ordering = ['name']
    
    

class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    manufacture_date = models.DateField()
    expiry_date = models.DateField()
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    date_received = models.DateField(auto_now_add=True) 
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.batch_number} (Exp: {self.expiry_date})"
    
    class Meta:
        verbose_name_plural = "Batches"
        ordering = ['expiry_date']

# models.py
from datetime import date

class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    insurance_provider = models.CharField(max_length=100, blank=True, null=True)
    insurance_number = models.CharField(max_length=50, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = date(2025, 1, 1)  # Using 2025 as the current year as specified
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    
    class Meta:
        ordering = ['last_name', 'first_name']

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()

class Prescription(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('partially_filled', 'Partially Filled'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='prescriptions')
    prescribing_doctor = models.CharField(max_length=100)
    date_prescribed = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Prescription #{self.id} for {self.patient}"
    
    def get_total_items(self):
        return self.items.count()
    
    def get_filled_percentage(self):
        if not self.items.exists():
            return 0
        total = sum(item.quantity for item in self.items.all())
        filled = sum(item.filled_quantity for item in self.items.all())
        return round((filled / total) * 100) if total > 0 else 0
    
    class Meta:
        ordering = ['-date_prescribed']

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    dosage = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True, null=True)
    filled_quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} (Qty: {self.quantity})"
    
    def get_remaining_quantity(self):
        return self.quantity - self.filled_quantity
    
    class Meta:
        ordering = ['prescription', 'product']

        
class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    )
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateField()
    expected_delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PO #{self.id} - {self.supplier}"
    
    def total_amount(self):
        return sum(item.total_price() for item in self.items.all())
    
    class Meta:
        ordering = ['-order_date']

class PurchaseOrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def total_price(self):
        return self.quantity * self.unit_price
    
    class Meta:
        ordering = ['order', 'product']

class Sale(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Payment'),
        ('insurance', 'Insurance'),
        ('credit', 'Credit'),
    )
    
    invoice_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('Patient', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Sale #{self.invoice_number}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    batch = models.ForeignKey('Batch', on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def total_price(self):
        return (self.unit_price - self.discount) * self.quantity

class StockAdjustment(models.Model):
    REASON_CHOICES = (
        ('expired', 'Expired'),
        ('damaged', 'Damaged'),
        ('correction', 'Correction'),
        ('return to Supplier', 'Return to Supplier'),
        ('lost', 'Lost'),
        ('theft', 'Theft'),
        ('other', 'Other'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    notes = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    adjusted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Adjustment of {self.product.name} - {self.quantity} units"
    
    class Meta:
        ordering = ['-date']

class Notification(models.Model):
    TYPE_CHOICES = (
        ('expiry', 'Product Expiry'),
        ('low_stock', 'Low Stock'),
        ('refill', 'Prescription Refill'),
        ('payment', 'Payment Due'),
        ('leave_approval', 'Leave Approval'),
        ('leave_rejection', 'Leave Rejection'),
        ('leave_request', 'Leave Request'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    url = models.URLField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"



from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from pharmacy.models import Patient


class Billing(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='billings')
    date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_billings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Billing'
        verbose_name_plural = 'Billings'
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['date']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Bill #{self.invoice_number} - {self.patient}"
    
    def get_absolute_url(self):
        return reverse('billing_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Calculate total amount if not set
        if not self.total_amount:
            self.total_amount = self.amount + self.tax_amount - self.discount_amount
        
        # Set default due date (30 days from billing date) if not provided
        if not self.due_date:
            self.due_date = self.date + datetime.timedelta(days=30)
        
        # Generate invoice number if not provided
        if not self.invoice_number:
            # Get the current year and month
            current_date = timezone.now()
            year_month = current_date.strftime('%Y%m')
            
            # Get the last invoice number for this month
            last_invoice = Billing.objects.filter(
                invoice_number__startswith=f'INV-{year_month}'
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                # Extract the sequence number and increment
                try:
                    last_seq = int(last_invoice.invoice_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (IndexError, ValueError):
                    new_seq = 1
            else:
                new_seq = 1
                
            # Format the new invoice number with leading zeros
            self.invoice_number = f"INV-{year_month}-{new_seq:04d}"
        
        super().save(*args, **kwargs)
    
    def clean(self):
        # Validate that due date is not before billing date
        if self.due_date and self.due_date < self.date:
            raise ValidationError("Due date cannot be before billing date.")
        
        # Validate that total amount is positive
        if self.total_amount <= 0:
            raise ValidationError("Total amount must be positive.")
    
    def update_payment_status(self):
        total_paid = self.payments.aggregate(total=Sum('amount'))['total'] or 0
        
        if total_paid >= self.total_amount:
            self.payment_status = 'paid'
        elif total_paid > 0:
            self.payment_status = 'partially_paid'
        else:
            self.payment_status = 'pending'
        
        self.save()
    
    def amount_due(self):
        total_paid = self.payments.aggregate(total=Sum('amount'))['total'] or 0
        return max(self.total_amount - total_paid, 0)
    
    def is_overdue(self):
        return self.payment_status != 'paid' and timezone.now().date() > self.due_date
    
    @property
    def days_overdue(self):
        if self.is_overdue():
            return (timezone.now().date() - self.due_date).days
        return 0

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Payment'),
        ('bank', 'Bank Transfer'),
        ('insurance', 'Insurance'),
        ('check', 'Check'),
    )
    
    billing = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['payment_date']),
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        return f"Payment of {self.amount} for Bill #{self.billing.invoice_number}"
    
    def get_absolute_url(self):
        return reverse('billing_detail', kwargs={'pk': self.billing.pk})
    
    def clean(self):
        # Validate that payment amount is positive
        if self.amount <= 0:
            raise ValidationError("Payment amount must be positive.")
        
        # Validate that payment date is not in the future
        if self.payment_date > timezone.now().date():
            raise ValidationError("Payment date cannot be in the future.")
    
    def save(self, *args, **kwargs):
        # Ensure the payment is associated with the billing record
        if not self.billing_id:
            raise ValidationError("Payment must be associated with a billing record.")
        
        super().save(*args, **kwargs)
        
        # Update the billing payment status after saving
        self.billing.update_payment_status()
    
    def delete(self, *args, **kwargs):
        billing = self.billing
        super().delete(*args, **kwargs)
        billing.update_payment_status()

class AlertRule(models.Model):
    ALERT_TYPES = (
        ('low_stock', 'Low Stock'),
        ('expiry', 'Expiry Date'),
        ('refill', 'Prescription Refill'),
        ('custom', 'Custom Alert'),
    )
    
    CONDITION_CHOICES = (
        ('lt', 'Less Than'),
        ('lte', 'Less Than or Equal'),
        ('gt', 'Greater Than'),
        ('gte', 'Greater Than or Equal'),
        ('eq', 'Equal To'),
    )
    
    name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, blank=True, null=True)
    threshold = models.IntegerField(blank=True, null=True)
    days_before = models.IntegerField(blank=True, null=True, help_text="Days before expiry to alert")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    recipients = models.ManyToManyField(User, related_name='alert_rules')
    parameters = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_alert_type_display()})"

    def get_alert_condition(self):
        if self.alert_type == 'low_stock':
            return f"Stock {self.get_condition_display()} {self.threshold}"
        elif self.alert_type == 'expiry':
            return f"Expires within {self.days_before} days"
        return "Custom condition"
    



