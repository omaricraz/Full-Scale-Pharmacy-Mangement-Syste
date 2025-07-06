from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Leave, User, Attendance, Payroll, PerformanceReview

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone', 'password1', 'password2']

class UserUpdateForm(UserChangeForm):
    password = None
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone', 'address', 'date_of_birth', 'hire_date', 'profile_picture', 'is_active']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in': forms.TimeInput(attrs={'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'type': 'time'}),
        }

# forms.py - Update the PayrollForm
class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = [
            'employee', 'month', 'basic_salary', 'allowances', 'deductions', 
            'bonus', 'tax', 'has_advance', 'advance_amount', 'advance_date',
            'advance_reason', 'net_salary', 'payment_date', 'is_paid', 'notes'
        ]
        widgets = {
            'month': forms.DateInput(attrs={'type': 'date'}),
            'advance_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make advance fields optional and conditionally required
        self.fields['advance_amount'].required = False
        self.fields['advance_date'].required = False
        self.fields['advance_reason'].required = False

class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = ['employee', 'review_date', 'reviewer', 'performance_score', 'strengths', 'areas_for_improvement', 'comments', 'next_review_date']
        widgets = {
            'review_date': forms.DateInput(attrs={'type': 'date'}),
            'next_review_date': forms.DateInput(attrs={'type': 'date'}),
        }


# Add to forms.py after the PerformanceReviewForm

from datetime import date, timedelta
from django.db.models import DurationField, ExpressionWrapper
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from .models import Leave, User

class LeaveForm(forms.ModelForm):
    LEAVE_TYPE_DURATIONS = {
        'annual': 30,
        'sick_1': 90,  # First 3 months
        'sick_2': 90,  # Next 3 months
        'maternity': 120,  # 4 months
        'maternity_miscarriage_9': 90,
        'maternity_miscarriage_6_8': 60,
        'maternity_miscarriage_3_5': 30,
        'family': 7,
        'unpaid': 60,
        'compensatory': 30
    }

    LEAVE_TYPE_DESCRIPTIONS = {
        'annual': "30 days paid leave per year",
        'sick_1': "First 90 days of sick leave (full pay)",
        'sick_2': "Next 90 days of sick leave (half pay)",
        'maternity': "120 days paid maternity leave",
        'maternity_miscarriage_9': "90 days for miscarriage after 9 months",
        'maternity_miscarriage_6_8': "60 days for miscarriage between 6-8 months",
        'maternity_miscarriage_3_5': "30 days for miscarriage between 3-5 months",
        'family': "7 days family responsibility leave",
        'unpaid': "Up to 60 days unpaid leave",
        'compensatory': "Compensatory leave for overtime work"
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        today = date.today().isoformat()
        
        # Set employee field based on user role
        if self.user and not (self.user.is_superuser or self.user.role == 'admin'):
            self.fields['employee'].initial = self.user
            self.fields['employee'].disabled = True
            self.fields['employee'].widget = forms.HiddenInput()
        
        # Add help text with leave balances
        if self.user and hasattr(self.user, 'employee'):
            remaining_annual = 30 - self._get_used_leave_days('annual')
            remaining_sick = self.user.get_remaining_sick_leave_days()
            
            self.fields['leave_type'].help_text = (
                f"Available leave balances: Annual ({remaining_annual}/30 days), "
                f"Sick ({remaining_sick}/180 days in 3 years)"
            )
        
        # Customize leave type choices with descriptions
        self.fields['leave_type'].choices = [
            (value, f"{label} - {self.LEAVE_TYPE_DESCRIPTIONS.get(value, '')}") 
            for value, label in self.fields['leave_type'].choices
            if value != 'paternity' or (self.user and self.user.gender == 'M')
        ]
        
        # Date field configurations
        self.fields['start_date'].widget.attrs.update({
            'min': today,
            'onchange': 'updateEndDate()',
            'class': 'datepicker'
        })
        self.fields['end_date'].widget.attrs.update({
            'min': today,
            'class': 'datepicker'
        })
        
        # Medical certificate field
        self.fields['medical_certificate'].required = False
        self.fields['medical_certificate'].widget.attrs.update({
            'accept': 'image/*,.pdf,.doc,.docx',
            'class': 'file-upload'
        })
        
        # Reason field
        self.fields['reason'].widget.attrs.update({
            'placeholder': 'Provide detailed reason for leave...',
            'rows': 3
        })
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'

    class Meta:
        model = Leave
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason', 'medical_certificate']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(),
        }
        labels = {
            'medical_certificate': 'Supporting Document',
        }
    
def _get_used_leave_days(self, leave_type):
    """Helper method to get used leave days of a specific type"""
    current_year = date.today().year
    return Leave.objects.filter(
        employee=self.user,
        leave_type=leave_type,
        status='approved',
        start_date__year=current_year
    ).annotate(
        duration=ExpressionWrapper(
            F('end_date') - F('start_date') + timedelta(days=1),
            output_field=DurationField()
        )
    ).aggregate(
        total=Sum('duration')
    )['total'] or 0


def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        medical_certificate = cleaned_data.get('medical_certificate')
        
        # Check if medical certificate is required but not provided
        if (leave_type and 
            (leave_type.startswith('sick_') or leave_type.startswith('maternity')) and 
            not medical_certificate and 
            not (self.instance and self.instance.medical_certificate)):
            
            # If this is an update and the leave already has a certificate, it's okay
            if not (self.instance and self.instance.medical_certificate):
                self.add_error(
                    'medical_certificate', 
                    "Medical certificate is required for this leave type"
                )
        
        return cleaned_data

def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee = cleaned_data.get('employee') or self.user
        leave_type = cleaned_data.get('leave_type')
        medical_certificate = cleaned_data.get('medical_certificate')
        
        if not all([start_date, end_date, employee, leave_type]):
            return cleaned_data
        
        # Date validation
        if start_date > end_date:
            raise forms.ValidationError("End date must be after start date")
        
        if start_date < date.today():
            raise forms.ValidationError("Cannot apply for leave in the past")
        
        duration = (end_date - start_date).days + 1
        
        # Duration validation
        max_duration = self.LEAVE_TYPE_DURATIONS.get(leave_type, 30)
        if duration > max_duration:
            raise forms.ValidationError(
                f"Maximum duration for {leave_type} leave is {max_duration} days. "
                f"You requested {duration} days."
            )
        
        # Annual leave balance check
        if leave_type == 'annual':
            used_days = self._get_used_leave_days('annual')
            if used_days + duration > 30:
                remaining = 30 - used_days
                raise forms.ValidationError(
                    f"You only have {remaining} days of annual leave remaining. "
                    f"You cannot take {duration} days."
                )
        
        # Sick leave validation
        if leave_type.startswith('sick_'):
            # Check probation period
            if not employee.has_completed_probation:
                raise forms.ValidationError(
                    "You must complete your 3-month probation period before taking sick leave"
                )
            
            # Check 6-month limit in 3 years
            remaining_sick = employee.get_remaining_sick_leave_days()
            if duration > remaining_sick:
                raise forms.ValidationError(
                    f"You only have {remaining_sick} days of sick leave remaining "
                    f"in the current 3-year period. You cannot take {duration} days."
                )
            
            # Medical certificate required
            if not medical_certificate:
                raise forms.ValidationError(
                    "Medical certificate is required for sick leave applications"
                )
        
        # Maternity leave validation
        if leave_type.startswith('maternity'):
            if employee.gender != 'F':
                raise forms.ValidationError(
                    "Maternity leave is only applicable for female employees"
                )
            if not medical_certificate:
                raise forms.ValidationError(
                    "Medical certificate is required for maternity leave"
                )
        
        # Family responsibility leave validation
        if leave_type == 'family':
            if duration > 7:
                raise forms.ValidationError(
                    "Family responsibility leave cannot exceed 7 days"
                )
        
        # Check for overlapping leaves
        overlapping_leaves = Leave.objects.filter(
            employee=employee,
            status__in=['approved', 'pending'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if self.instance.pk:
            overlapping_leaves = overlapping_leaves.exclude(pk=self.instance.pk)
            
        if overlapping_leaves.exists():
            conflicts = []
            for leave in overlapping_leaves:
                conflict_dates = f"{leave.start_date} to {leave.end_date}"
                conflicts.append(f"{leave.get_leave_type_display()} ({conflict_dates})")
            
            raise forms.ValidationError(
                "You have conflicting leave periods: " + ", ".join(conflicts)
            )
        
        return cleaned_data


class LeaveApprovalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        # Customize form based on leave type
        if instance and instance.leave_type in ['unpaid', 'compensatory']:
            self.fields['payment_status'].disabled = True
            self.fields['payment_status'].initial = 'not_applicable'
        
        # Add custom styling classes
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        # Customize comments field
        self.fields['comments'].widget.attrs.update({
            'placeholder': 'Enter approval comments or reason for rejection...',
            'rows': 3
        })

    class Meta:
        model = Leave
        fields = ['status', 'payment_status', 'comments']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(),
        }
        labels = {
            'comments': 'Approver Notes'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        payment_status = cleaned_data.get('payment_status')
        instance = getattr(self, 'instance', None)
        
        # Validate payment status based on leave type
        if (status == 'approved' and instance and 
            instance.leave_type not in ['unpaid', 'compensatory']):
            if not payment_status:
                raise forms.ValidationError(
                    "Payment status is required for paid leave types"
                )
        
        # Require comments for rejections
        if status == 'rejected' and not cleaned_data.get('comments'):
            raise forms.ValidationError(
                "Please provide a reason for rejecting this leave application"
            )
        
        return cleaned_data