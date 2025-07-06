# pharmacy/templatetags/account_filters.py

from django import template

register = template.Library()

@register.filter
def leave_type_name(leave_type_id):
    from pharmacy.models import LeaveType  # Import inside the function to avoid circular import
    try:
        return LeaveType.objects.get(id=leave_type_id).name
    except LeaveType.DoesNotExist:
        return "Unknown"
 