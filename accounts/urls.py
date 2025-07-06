from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
# Authentication
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    
    
    
    # Attendance
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/create/', views.attendance_create, name='attendance_create'),
    path('attendance/<int:pk>/update/', views.attendance_update, name='attendance_update'),
    path('attendance/<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),

    path('attendance/report/', views.attendance_report, name='attendance_report'),
    path('attendance/export/', views.export_attendance_report, name='export_attendance_report'),
    
    
    # Payroll
    path('payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/create/', views.payroll_create, name='payroll_create'),
    path('payroll/<int:pk>/update/', views.payroll_update, name='payroll_update'),
    path('payroll/<int:pk>/delete/', views.payroll_delete, name='payroll_delete'),
    path('payroll/<int:pk>/', views.payroll_detail, name='payroll_detail'),




    # Leave Management
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/create/', views.leave_create, name='leave_create'),
    path('leaves/<int:pk>/', views.leave_detail, name='leave_detail'),
    path('leaves/<int:pk>/update/', views.leave_update, name='leave_update'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leaves/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    path('leaves/<int:pk>/delete/', views.leave_delete, name='leave_delete'),
    
    # Performance Review
    path('performance-reviews/', views.performance_review_list, name='performance_review_list'),
    path('performance-reviews/create/', views.performance_review_create, name='performance_review_create'),
    path('performance-reviews/<int:pk>/update/', views.performance_review_update, name='performance_review_update'),
    path('performance-reviews/<int:pk>/delete/', views.performance_review_delete, name='performance_review_delete'),
]