from django.urls import path
from . import views

urlpatterns = [
    # Supplier URLs
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Product URLs
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/update/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    path('reports/countries/', views.country_performance_report, name='country_performance_report'),
    
    
    
    # Batch URLs
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),
    path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:pk>/update/', views.batch_update, name='batch_update'),
    path('batches/<int:pk>/delete/', views.batch_delete, name='batch_delete'),
    
    # Patient URLs
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/create/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/update/', views.patient_update, name='patient_update'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient_delete'),

    
    
    
    # Prescription URLs
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/create/', views.prescription_create, name='prescription_create'),
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('prescriptions/<int:pk>/update/', views.prescription_update, name='prescription_update'),
    path('prescriptions/<int:pk>/delete/', views.prescription_delete, name='prescription_delete'),
    path('prescriptions/<int:prescription_pk>/items/add/', views.prescription_item_add, name='prescription_item_add'),
    path('prescription-items/<int:pk>/edit/', views.prescription_item_edit, name='prescription_item_edit'),
    path('prescription-items/<int:pk>/delete/', views.prescription_item_delete, name='prescription_item_delete'),
    
    # Purchase Order URLs
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/update/', views.purchase_order_update, name='purchase_order_update'),
    path('purchase-orders/<int:pk>/delete/', views.purchase_order_delete, name='purchase_order_delete'),
    path('purchase-orders/<int:pk>/receive/', views.purchase_order_receive, name='purchase_order_receive'),
    path('purchase-orders/<int:order_pk>/items/add/', views.purchase_order_item_add, name='purchase_order_item_add'),
    path('purchase-order-items/<int:pk>/edit/', views.purchase_order_item_edit, name='purchase_order_item_edit'),
    path('purchase-order-items/<int:pk>/delete/', views.purchase_order_item_delete, name='purchase_order_item_delete'),
    
    # Sales URLs
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/delete/', views.sale_delete, name='sale_delete'),
    
    # POS URLs
    path('pos/', views.pos, name='pos'),
    path('pos/remove-item/<int:item_id>/', views.pos_remove_item, name='pos_remove_item'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),
    


    # Stock Adjustment URLs
    path('stock-adjustments/', views.stock_adjustment_list, name='stock_adjustment_list'),
    path('stock-adjustments/create/', views.stock_adjustment_create, name='stock_adjustment_create'),
    
    # Reports
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    path('reports/expiry/', views.expiry_report, name='expiry_report'),
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/financial-summary/', views.financial_summary, name='financial_summary'),
    

    
 # Billing & Payment URLs
    path('billings/', views.billing_list, name='billing_list'),
    path('billings/create/', views.billing_create, name='billing_create'),
    path('billings/<int:pk>/', views.billing_detail, name='billing_detail'),
    path('billings/<int:pk>/update/', views.billing_update, name='billing_update'),
    path('billings/<int:pk>/delete/', views.billing_delete, name='billing_delete'),
    
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/select-billing/', views.payment_select_billing, name='payment_select_billing'),
    path('payments/create/<int:billing_pk>/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/update/', views.payment_update, name='payment_update'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/mark-read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),

    
    # Alert Rules
    path('alerts/rules/', views.alert_rules, name='alert_rules'),
    path('alerts/rules/create/', views.alert_rule_create, name='alert_rule_create'),
    path('alerts/rules/<int:pk>/', views.alert_rule_detail, name='alert_rule_detail'),
    path('alerts/rules/<int:pk>/update/', views.alert_rule_update, name='alert_rule_update'),
    path('alerts/rules/<int:pk>/delete/', views.alert_rule_delete, name='alert_rule_delete'),
    
    # AJAX URLs
    path('ajax/product-batches/<int:product_id>/', views.ajax_product_batches, name='ajax_product_batches'),
    path('ajax/product-by-barcode/', views.ajax_product_by_barcode, name='ajax_product_by_barcode'),
    path('ajax/product-stock/<int:product_id>/', views.ajax_product_stock, name='ajax_product_stock'),
]