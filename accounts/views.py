from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse

from django.core.exceptions import PermissionDenied


from pharmacy.models import Notification, Payment, Prescription, Product, Sale
from django.db.models import Sum, F
from .models import Leave, User, Attendance, Payroll, PerformanceReview
from .forms import LeaveApprovalForm, LeaveForm, UserRegistrationForm, UserUpdateForm, AttendanceForm, PayrollForm, PerformanceReviewForm

def is_admin(user):
    return user.role == 'admin'


def home_view(request):
    return render(request, 'home.html')


@login_required
def dashboard(request):
    # Get current year
    current_year = date.today().year
    last_year = current_year - 1

    # Get counts for dashboard cards
    product_count = Product.objects.filter(is_active=True).count()
    total_sales_count = Sale.objects.count()
    total_payments_count = Payment.objects.count()
    pending_prescriptions_count = Prescription.objects.filter(status='pending').count()

    # Get recent payments (last 10)
    recent_payments = Payment.objects.select_related('billing').order_by('-payment_date')[:10]

    # Get recent notifications (last 5)
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:5]

    # Calculate monthly payments for current year
    current_year_payments = Payment.objects.filter(payment_date__year=current_year).values(
        'payment_date__month'
    ).annotate(
        total=Sum('amount')
    ).order_by('payment_date__month')

    # Calculate monthly payments for last year
    last_year_payments = Payment.objects.filter(payment_date__year=last_year).values(
        'payment_date__month'
    ).annotate(
        total=Sum('amount')
    ).order_by('payment_date__month')

    # Initialize monthly payments data with zeros
    monthly_payments_current = [0] * 12
    monthly_payments_last = [0] * 12

    # Fill in the actual payments data
    for payment in current_year_payments:
        month_index = payment['payment_date__month'] - 1  # Convert to 0-based index
        monthly_payments_current[month_index] = float(payment['total'] or 0)

    for payment in last_year_payments:
        month_index = payment['payment_date__month'] - 1  # Convert to 0-based index
        monthly_payments_last[month_index] = float(payment['total'] or 0)

    context = {
        'user': request.user.get_full_name() or request.user.username,
        'current_year': current_year,
        'product_count': product_count,
        'total_sales_count': total_sales_count,
        'total_payments_count': total_payments_count,
        'pending_prescriptions_count': pending_prescriptions_count,
        'recent_payments': recent_payments,
        'notifications': notifications,
        'monthly_payments_current': monthly_payments_current,
        'monthly_payments_last': monthly_payments_last,
    }

    return render(request, 'accounts/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create User'})

@login_required
@user_passes_test(is_admin)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Update User'})

@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully!')
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

@login_required
def attendance_list(request):
    if request.user.role == 'admin':
        attendances = Attendance.objects.all()
    else:
        attendances = Attendance.objects.filter(employee=request.user)
    return render(request, 'accounts/attendance_list.html', {'attendances': attendances})

@login_required
def attendance_create(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save()
            messages.success(request, 'Attendance record created successfully!')
            return redirect('attendance_list')
    else:
        form = AttendanceForm(initial={'employee': request.user})
    return render(request, 'accounts/attendance_form.html', {'form': form, 'title': 'Create Attendance'})

@login_required
def attendance_update(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance record updated successfully!')
            return redirect('attendance_list')
    else:
        form = AttendanceForm(instance=attendance)
    return render(request, 'accounts/attendance_form.html', {'form': form, 'title': 'Update Attendance'})

@login_required
def attendance_delete(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        attendance.delete()
        messages.success(request, 'Attendance record deleted successfully!')
        return redirect('attendance_list')
    return render(request, 'accounts/attendance_confirm_delete.html', {'attendance': attendance})

@login_required
def payroll_list(request):
    if request.user.role == 'admin':
        payrolls = Payroll.objects.all()
    else:
        payrolls = Payroll.objects.filter(employee=request.user)
    return render(request, 'accounts/payroll_list.html', {'payrolls': payrolls})

@login_required
@user_passes_test(is_admin)
def payroll_create(request):
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            payroll = form.save()
            messages.success(request, 'Payroll record created successfully!')
            return redirect('payroll_list')
    else:
        form = PayrollForm()
    return render(request, 'accounts/payroll_form.html', {'form': form, 'title': 'Create Payroll'})

@login_required
def payroll_detail(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    
    if request.user != payroll.employee and request.user.role != 'admin':
        raise PermissionDenied

    return render(request, 'accounts/payroll_detail.html', {'payroll': payroll})


@login_required
@user_passes_test(is_admin)
def payroll_update(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll record updated successfully!')
            return redirect('payroll_list')
    else:
        form = PayrollForm(instance=payroll)
    return render(request, 'accounts/payroll_form.html', {'form': form, 'title': 'Update Payroll'})

@login_required
@user_passes_test(is_admin)
def payroll_delete(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == 'POST':
        payroll.delete()
        messages.success(request, 'Payroll record deleted successfully!')
        return redirect('payroll_list')
    return render(request, 'accounts/payroll_confirm_delete.html', {'payroll': payroll})

@login_required
def performance_review_list(request):
    if request.user.role == 'admin':
        reviews = PerformanceReview.objects.all()
    else:
        reviews = PerformanceReview.objects.filter(employee=request.user)
    return render(request, 'accounts/performance_review_list.html', {'reviews': reviews})

@login_required
@user_passes_test(is_admin)
def performance_review_create(request):
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.save()
            messages.success(request, 'Performance review created successfully!')
            return redirect('performance_review_list')
    else:
        form = PerformanceReviewForm()
    return render(request, 'accounts/performance_review_form.html', {'form': form, 'title': 'Create Performance Review'})

@login_required
@user_passes_test(is_admin)
def performance_review_update(request, pk):
    review = get_object_or_404(PerformanceReview, pk=pk)
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Performance review updated successfully!')
            return redirect('performance_review_list')
    else:
        form = PerformanceReviewForm(instance=review)
    return render(request, 'accounts/performance_review_form.html', {'form': form, 'title': 'Update Performance Review'})

@login_required
@user_passes_test(is_admin)
def performance_review_delete(request, pk):
    review = get_object_or_404(PerformanceReview, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Performance review deleted successfully!')
        return redirect('performance_review_list')
    return render(request, 'accounts/performance_review_confirm_delete.html', {'review': review})


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def profile_update(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')  # Make sure 'profile' is a valid URL name
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile_update.html', {'form': form})


# Add to views.py after the performance_review_delete view

@login_required
def leave_list(request):
    if request.user.role == 'admin':
        leaves = Leave.objects.all()
    else:
        leaves = Leave.objects.filter(employee=request.user)
    return render(request, 'accounts/leave_list.html', {'leaves': leaves})


@login_required
def leave_create(request):
    if request.method == 'POST':
        form = LeaveForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            leave = form.save(commit=False)
            if request.user.role != 'admin':
                leave.employee = request.user
            leave.save()

            if request.user.role != 'admin':
                admin_users = User.objects.filter(role='admin')
                for admin in admin_users:
                    Notification.objects.create(
                        recipient=admin,
                        title="New Leave Application",
                        message=f"{request.user.get_full_name()} has applied for {leave.leave_type} leave from {leave.start_date} to {leave.end_date}.",
                        url=reverse('leave_detail', args=[leave.id])
                    )
            messages.success(request, 'Leave application submitted successfully!')
            return redirect('leave_list')
    else:
        form = LeaveForm(user=request.user)
    return render(request, 'accounts/leave_form.html', {'form': form, 'title': 'Apply for Leave'})


@login_required
def leave_detail(request, pk):
    leave = get_object_or_404(Leave, pk=pk)

    if request.user != leave.employee and request.user.role != 'admin':
        raise PermissionDenied

    if request.method == 'POST' and request.user.role == 'admin':
        form = LeaveApprovalForm(request.POST, instance=leave)
        if form.is_valid():
            leave = form.save(commit=False)
            if leave.status == 'approved' and not leave.approved_by:
                leave.approved_by = request.user
                leave.approved_on = date.today()
            leave.save()

            Notification.objects.create(
                recipient=leave.employee,
                title=f"Leave Application {leave.get_status_display()}",
                message=f"Your {leave.leave_type} leave from {leave.start_date} to {leave.end_date} has been {leave.status}.",
                url=reverse('leave_detail', args=[leave.id])
            )

            messages.success(request, 'Leave application updated successfully!')
            return redirect('leave_detail', pk=leave.id)
    else:
        form = LeaveApprovalForm(instance=leave) if request.user.role == 'admin' else None

    return render(request, 'accounts/leave_detail.html', {
        'leave': leave,
        'form': form,
    })


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def leave_approve(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approved_on = date.today()

        if leave.leave_type in ['paid', 'sick', 'maternity', 'paternity', 'bereavement']:
            leave.payment_status = 'pending'
        else:
            leave.payment_status = 'not_applicable'

        leave.save()

        Notification.objects.create(
            recipient=leave.employee,
            title="Leave Approved",
            message=f"Your {leave.get_leave_type_display()} leave has been approved.",
            url=reverse('leave_detail', args=[leave.id])
        )

        messages.success(request, 'Leave has been approved!')
        return redirect('leave_detail', pk=leave.id)

    return render(request, 'accounts/leave_confirm_approve.html', {'leave': leave})


@login_required
def leave_update(request, pk):
    leave = get_object_or_404(Leave, pk=pk)

    if request.user != leave.employee and request.user.role != 'admin':
        raise PermissionDenied

    if leave.status != 'pending' and request.user.role != 'admin':
        messages.error(request, 'You can only edit pending leave applications.')
        return redirect('leave_detail', pk=leave.id)

    if request.method == 'POST':
        form = LeaveForm(request.POST, instance=leave, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave application updated successfully!')
            return redirect('leave_detail', pk=leave.id)
    else:
        form = LeaveForm(instance=leave, user=request.user)

    return render(request, 'accounts/leave_form.html', {
        'form': form,
        'title': 'Update Leave Application',
        'leave': leave
    })


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def leave_reject(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        leave.status = 'rejected'
        leave.approved_by = request.user
        leave.approved_on = date.today()
        leave.comments = request.POST.get('comments', '')
        leave.save()

        Notification.objects.create(
            recipient=leave.employee,
            title="Leave Rejected",
            message=f"Your leave from {leave.start_date} to {leave.end_date} has been rejected.",
            url=reverse('leave_detail', args=[leave.id])
        )

        messages.success(request, 'Leave application rejected!')
        return redirect('leave_detail', pk=leave.id)

    return render(request, 'accounts/leave_reject.html', {'leave': leave})


@login_required
def leave_delete(request, pk):
    leave = get_object_or_404(Leave, pk=pk)

    if leave.status != 'pending' and request.user.role != 'admin':
        messages.error(request, 'You can only delete pending leave applications.')
        return redirect('leave_list')

    if request.method == 'POST':
        leave.delete()
        messages.success(request, 'Leave application deleted successfully!')
        return redirect('leave_list')

    return render(request, 'accounts/leave_confirm_delete.html', {'leave': leave})




from django.shortcuts import render, redirect
from django.db.models import Count, Q
from datetime import datetime, time, timedelta
from .models import Attendance, User
from django.http import HttpResponse
import csv
import json
from django.contrib import messages
from django.db.models.functions import TruncDate

def attendance_report(request):
    employees = User.objects.filter(is_active=True).order_by('first_name')
    attendances = Attendance.objects.none()
    summary = {}
    trend_data = []
    late_employees = []
    top_performers = []
    
    if 'start_date' in request.GET and 'end_date' in request.GET:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Validate date range (max 6 months)
            if (end_date - start_date).days > 180:
                messages.error(request, "Date range cannot exceed 6 months")
                return redirect('attendance_report')
            
            # Base query
            attendances = Attendance.objects.filter(
                date__range=[start_date, end_date]
            ).select_related('employee').order_by('-date', 'employee__first_name')
            
            # Apply filters
            if 'employee' in request.GET and request.GET['employee']:
                attendances = attendances.filter(employee_id=request.GET['employee'])
                
            if 'status' in request.GET and request.GET['status']:
                attendances = attendances.filter(status=request.GET['status'])
            
            # Calculate summary statistics
            total_records = attendances.count()
            present_count = attendances.filter(status='present').count()
            absent_count = attendances.filter(status='absent').count()
            late_count = attendances.filter(status='late').count()
            leave_count = attendances.filter(status='leave').count()
            half_day_count = attendances.filter(status='half_day').count()
            
            # Calculate average working hours
            working_hours_list = []
            for att in attendances.filter(status__in=['present', 'late', 'half_day']):
                working_hours = att.get_working_hours()
                if working_hours:
                    working_hours_list.append(working_hours.total_seconds())
            
            if working_hours_list:
                avg_seconds = sum(working_hours_list) / len(working_hours_list)
                hours = int(avg_seconds // 3600)
                minutes = int((avg_seconds % 3600) // 60)
                avg_working_hours_str = f"{hours}h {minutes}m"
            else:
                avg_working_hours_str = "-"
            
            summary = {
                'total_records': total_records,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'leave_count': leave_count,
                'half_day_count': half_day_count,
                'present_percentage': round((present_count / total_records * 100), 2) if total_records else 0,
                'absent_percentage': round((absent_count / total_records * 100), 2) if total_records else 0,
                'late_percentage': round((late_count / total_records * 100), 2) if total_records else 0,
                'avg_hours': avg_working_hours_str
            }
            
            # Prepare data for attendance trend chart
            date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
            
            trend_dates = []
            trend_present = []
            trend_absent = []
            
            for single_date in date_range:
                date_str = single_date.strftime('%Y-%m-%d')
                trend_dates.append(date_str)
                
                day_attendances = attendances.filter(date=single_date)
                present = day_attendances.filter(status__in=['present', 'late', 'half_day']).count()
                absent = day_attendances.filter(status='absent').count()
                
                trend_present.append(present)
                trend_absent.append(absent)
            
            # Prepare data for late arrivals chart
            late_employees = list(attendances.filter(status='late').values(
                'employee__first_name', 'employee__last_name'
            ).annotate(
                late_count=Count('id')
            ).order_by('-late_count')[:5])
            
            # Prepare data for top performers
            active_employees = User.objects.filter(is_active=True)
            top_performers = []
            
            for employee in active_employees:
                emp_attendances = attendances.filter(employee=employee)
                total_days = emp_attendances.count()
                if total_days > 0:
                    present_days = emp_attendances.filter(
                        status__in=['present', 'late', 'half_day']
                    ).count()
                    attendance_rate = round((present_days / total_days) * 100, 1)
                    
                    if attendance_rate >= 90:
                        top_performers.append({
                            'name': employee.get_full_name(),
                            'initials': f"{employee.first_name[0]}{employee.last_name[0]}",
                            'attendance_rate': attendance_rate,
                            'total_days': total_days,
                            'present_days': present_days
                        })
            
            # Sort by attendance rate (descending) and limit to top 5
            top_performers = sorted(top_performers, key=lambda x: x['attendance_rate'], reverse=True)[:5]
            
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
            return redirect('attendance_report')
    
    # Prepare data for charts
    late_employees_names = [
        f"{emp['employee__first_name']} {emp['employee__last_name']}" 
        for emp in late_employees
    ] if late_employees else []
    late_employees_counts = [emp['late_count'] for emp in late_employees] if late_employees else []
    
    context = {
        'employees': employees,
        'attendances': attendances,
        'summary': summary,
        'trend_dates': json.dumps(trend_dates) if 'trend_dates' in locals() else json.dumps([]),
        'trend_present': json.dumps(trend_present) if 'trend_present' in locals() else json.dumps([]),
        'trend_absent': json.dumps(trend_absent) if 'trend_absent' in locals() else json.dumps([]),
        'late_employees_names': json.dumps(late_employees_names),
        'late_employees_counts': json.dumps(late_employees_counts),
        'top_performers': top_performers,
    }
    
    return render(request, 'accounts/attendance_report.html', context)

def export_attendance_report(request):
    # Get the same filters from the request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        messages.error(request, "Please select date range first")
        return redirect('attendance_report')
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Invalid date format")
        return redirect('attendance_report')
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Write CSV header
    writer.writerow([
        'Employee Name', 'Date', 'Day', 'Status', 
        'Check In', 'Check Out', 'Working Hours', 'Late Minutes'
    ])
    
    # Get filtered data
    attendances = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('employee').order_by('-date', 'employee__first_name')
    
    if 'employee' in request.GET and request.GET['employee']:
        attendances = attendances.filter(employee_id=request.GET['employee'])
        
    if 'status' in request.GET and request.GET['status']:
        attendances = attendances.filter(status=request.GET['status'])
    
    # Write data rows
    for attendance in attendances:
        # Calculate working hours
        working_hours = ''
        working_hours_delta = attendance.get_working_hours()
        if working_hours_delta:
            total_seconds = working_hours_delta.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            working_hours = f"{hours:02d}:{minutes:02d}"
        
        # Calculate late minutes
        late_minutes = ''
        late_min = attendance.get_late_minutes()
        if late_min is not None:
            late_minutes = f"{late_min} mins"
        
        writer.writerow([
            attendance.employee.get_full_name(),
            attendance.date.strftime('%Y-%m-%d'),
            attendance.date.strftime('%A'),
            attendance.get_status_display(),
            attendance.check_in.strftime('%H:%M') if attendance.check_in else '-',
            attendance.check_out.strftime('%H:%M') if attendance.check_out else '-',
            working_hours,
            late_minutes
        ])
    
    return response