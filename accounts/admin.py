from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Attendance, Payroll, PerformanceReview

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth', 'profile_picture')}),
        ('Employment', {'fields': ('role', 'hire_date', 'is_active')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Attendance)
admin.site.register(Payroll)
admin.site.register(PerformanceReview)