from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from pharmacy.models import Notification, Payment, Prescription, Product, Sale
from django.db.models import Sum, F
from .models import User, Attendance, Payroll, PerformanceReview
from .forms import UserRegistrationForm, UserUpdateForm, AttendanceForm, PayrollForm, PerformanceReviewForm

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