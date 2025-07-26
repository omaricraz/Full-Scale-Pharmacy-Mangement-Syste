from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from datetime import date, datetime, time, timedelta

class User(AbstractUser):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    ROLES = (
        ('admin', 'Administrator'),
        ('pharmacist', 'Pharmacist'),
        ('cashier', 'Cashier'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    )
    
    role = models.CharField(max_length=20, choices=ROLES, default='staff')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    @property
    def unread_notification_count(self):
        """Returns the count of unread notifications for the user"""
        return self.account_notifications.filter(is_read=False).count()
    
    def get_role_display(self):
        """Returns the human-readable role name"""
        return dict(self.ROLES).get(self.role, self.role)
    
    @property
    def has_completed_probation(self):
        """Check if employee has completed 3-month probation period"""
        if not self.hire_date:
            return False
        return (date.today() - self.hire_date).days >= 90
    
    def get_remaining_sick_leave_days(self):
        """Calculate remaining sick leave days in current 3-year period"""
        if not self.has_completed_probation:
            return 0
            
        three_years_ago = date.today() - timedelta(days=3*365)
        used_days = Leave.objects.filter(
            employee=self,
            leave_type__startswith='sick_',
            status='approved',
            start_date__gte=three_years_ago
        ).annotate(
            duration=F('end_date') - F('start_date') + 1
        ).aggregate(
            total=Sum('duration')
        )['total'] or 0
        
        return max(0, 180 - used_days)  # 6 months = 180 days


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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('leave', 'Leave'),
    )
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField(blank=True, null=True)
    check_out = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('employee', 'date')
        verbose_name_plural = 'Attendance records'
        ordering = ['-date', 'employee__first_name']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} ({self.get_status_display()})"
    
    def get_working_hours(self):
        if not self.check_in or not self.check_out:
            return None
            
        # Convert times to datetime objects for calculation
        check_in_dt = datetime.combine(self.date, self.check_in)
        check_out_dt = datetime.combine(self.date, self.check_out)
        
        # Handle case where check_out is next day (e.g., night shift)
        if check_out_dt < check_in_dt:
            check_out_dt += timedelta(days=1)
            
        delta = check_out_dt - check_in_dt
        return delta
    
    def get_late_minutes(self, standard_start_time=time(9, 0)):  # Default 9:00 AM
        if self.status != 'late' or not self.check_in:
            return None
            
        standard_start = datetime.combine(self.date, standard_start_time)
        check_in_dt = datetime.combine(self.date, self.check_in)
        
        if check_in_dt > standard_start:
            delta = check_in_dt - standard_start
            return int(delta.total_seconds() / 60)
        return 0


class Payroll(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payrolls')
    month = models.DateField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # New fields for advance
    has_advance = models.BooleanField(default=False)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_date = models.DateField(blank=True, null=True)
    advance_reason = models.TextField(blank=True, null=True)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        """Calculate net salary before saving"""
        total_earnings = self.basic_salary + self.allowances + self.bonus
        total_deductions = self.deductions + self.tax
        
        # Include advance amount in deductions if applicable
        if self.has_advance:
            total_deductions += self.advance_amount
            
        self.net_salary = total_earnings - total_deductions
        super().save(*args, **kwargs)
def calculate_leave_deductions(self):
        """Calculate total deductions from leaves for this payroll period"""
        leaves = Leave.objects.filter(
            employee=self.employee,
            start_date__month=self.month.month,
            start_date__year=self.month.year,
            status='approved'
        )
        
        total_deductions = 0
        for leave in leaves:
            total_deductions += leave.calculate_leave_deduction()
            
            # Mark leave as paid in payroll if applicable
            if leave.payment_status == 'pending' and leave.leave_type not in ['unpaid', 'compensatory']:
                leave.payment_status = 'paid'
                leave.payroll = self
                leave.save()
                
        return total_deductions
    
def save(self, *args, **kwargs):
        """Calculate net salary before saving"""
        total_earnings = self.basic_salary + self.allowances + self.bonus
        total_deductions = self.deductions + self.tax
        
        # Include advance amount in deductions if applicable
        if self.has_advance:
            total_deductions += self.advance_amount
            
        # Add leave deductions
        total_deductions += self.calculate_leave_deductions()
            
        self.net_salary = total_earnings - total_deductions
        super().save(*args, **kwargs)

        


class PerformanceReview(models.Model):
    RATING_CHOICES = (
        (1, 'Poor'),
        (2, 'Needs Improvement'),
        (3, 'Meets Expectations'),
        (4, 'Exceeds Expectations'),
        (5, 'Outstanding'),
    )
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    review_date = models.DateField()
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='conducted_reviews')
    performance_score = models.IntegerField(choices=RATING_CHOICES)
    strengths = models.TextField()
    areas_for_improvement = models.TextField()
    comments = models.TextField(blank=True, null=True)
    next_review_date = models.DateField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-review_date']
        verbose_name_plural = 'Performance reviews'
    
    def __str__(self):
        return f"Performance Review for {self.employee.username} on {self.review_date}"
    
    def get_performance_rating(self):
        """Returns the human-readable performance rating"""
        return dict(self.RATING_CHOICES).get(self.performance_score, 'Not Rated')


class Leave(models.Model):
    LEAVE_TYPES = (
        ('annual', 'Annual Leave (30 days)'),
        ('sick_1', 'Sick Leave (First 3 months - Full Pay)'),
        ('sick_2', 'Sick Leave (Next 3 months - Half Pay)'),
        ('maternity', 'Maternity Leave (4 months)'),
        ('maternity_miscarriage_9', 'Maternity Leave (90 days - 9th month miscarriage)'),
        ('maternity_miscarriage_6_8', 'Maternity Leave (60 days - 6-8 month miscarriage)'),
        ('maternity_miscarriage_3_5', 'Maternity Leave (30 days - 3-5 month miscarriage)'),
        ('family', 'Family Responsibility Leave (3-7 days)'),
        ('unpaid', 'Unpaid Leave'),
        ('compensatory', 'Compensatory Leave'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('not_applicable', 'Not Applicable'),
    )
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=30, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(
        max_length=15, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending'
    )
    medical_certificate = models.FileField(upload_to='medical_certificates/', blank=True, null=True)
    applied_on = models.DateField(auto_now_add=True)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_leaves'
    )
    approved_on = models.DateField(null=True, blank=True)
    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leaves'
    )
    comments = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-applied_on']
        verbose_name_plural = 'Leaves'
    
    def __str__(self):
        return f"{self.employee.username} - {self.leave_type} ({self.status})"
    
    @property
    def duration(self):
        """Calculate the duration of leave in days"""
        return (self.end_date - self.start_date).days + 1
    
def save(self, *args, **kwargs):
    # Set payment status based on leave type
    if self.leave_type in ['unpaid', 'compensatory']:
        self.payment_status = 'not_applicable'
    elif self.status == 'approved' and self.leave_type not in ['unpaid', 'compensatory']:
        self.payment_status = 'pending'
    
    super().save(*args, **kwargs)
    
    def calculate_leave_deduction(self):
        """Calculate the amount to be deducted for this leave"""
        if self.payment_status == 'not_applicable' or not self.employee.payrolls.exists():
            return 0
            
        # Get the employee's daily rate (basic salary / 30 days)
        latest_payroll = self.employee.payrolls.order_by('-month').first()
        daily_rate = latest_payroll.basic_salary / 30
        
        # For unpaid leave, deduct full days
        if self.leave_type == 'unpaid':
            return self.duration * daily_rate
        
        # For sick leave type 2 (second 3 months), deduct half pay
        if self.leave_type == 'sick_2':
            return self.duration * daily_rate * 0.5
            
        return 0