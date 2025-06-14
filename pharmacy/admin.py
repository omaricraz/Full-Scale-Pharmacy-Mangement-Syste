from django.contrib import admin
from .models import (
    Supplier, Category, Product, Batch, Patient, Prescription, PrescriptionItem,
    PurchaseOrder, PurchaseOrderItem, Sale, SaleItem, StockAdjustment, Notification,
    Billing, Payment, AlertRule
)

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'phone', 'email')
    list_filter = ('created_at', 'updated_at')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'category', 'product_type', 'selling_price', 'get_stock_quantity')
    list_filter = ('category', 'product_type', 'is_active')
    search_fields = ('name', 'generic_name', 'barcode')
    
    def get_stock_quantity(self, obj):
        return obj.get_stock_quantity()
    get_stock_quantity.short_description = 'Stock Quantity'

class BatchAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch_number', 'expiry_date', 'quantity', 'supplier')
    list_filter = ('product', 'supplier', 'expiry_date')
    search_fields = ('product__name', 'batch_number')
    date_hierarchy = 'expiry_date'

class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'date_of_birth', 'gender', 'phone')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    list_filter = ('gender', 'city', 'state')

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'prescribing_doctor', 'date_prescribed', 'status')
    list_filter = ('status', 'date_prescribed', 'created_by')
    search_fields = ('patient__first_name', 'patient__last_name', 'prescribing_doctor')
    inlines = [PrescriptionItemInline]

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'status', 'total_amount')
    list_filter = ('status', 'order_date', 'supplier')
    search_fields = ('supplier__name', 'notes')
    inlines = [PurchaseOrderItemInline]
    
    def total_amount(self, obj):
        return obj.total_amount()
    total_amount.short_description = 'Total Amount'

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['product', 'batch', 'quantity', 'unit_price', 'discount']
    can_delete = False

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'date', 'patient', 'total_amount', 'payment_method']
    list_filter = ['date', 'payment_method']
    search_fields = ['invoice_number', 'patient__first_name', 'patient__last_name']
    inlines = [SaleItemInline]
    readonly_fields = ['invoice_number', 'date', 'created_by']

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'unit_price', 'discount']
    list_filter = ['product']
    search_fields = ['sale__invoice_number', 'product__name']

class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch', 'quantity', 'reason', 'date', 'adjusted_by')
    list_filter = ('reason', 'date', 'adjusted_by')
    search_fields = ('product__name', 'batch__batch_number')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'recipient', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'recipient')
    search_fields = ('title', 'message')

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1

class BillingAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'patient', 'date', 'total_amount', 'payment_status')
    list_filter = ('payment_status', 'date')
    search_fields = ('invoice_number', 'patient__first_name', 'patient__last_name')
    inlines = [PaymentInline]

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('billing', 'amount', 'payment_date', 'payment_method')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('billing__invoice_number', 'reference_number')

class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'alert_type', 'is_active')
    list_filter = ('alert_type', 'is_active')
    search_fields = ('name',)
    filter_horizontal = ('recipients',)

# Register all models except Sale and SaleItem which are already registered with decorators
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(StockAdjustment, StockAdjustmentAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Billing, BillingAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AlertRule, AlertRuleAdmin)