from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Count, Avg
from django.views.decorators.http import require_POST
from django.db import transaction
from django.http import JsonResponse
from datetime import date, timedelta, datetime
from django.db.models.functions import TruncDay
from .models import (
    Supplier, Category, Product, Batch, Patient, Prescription, PrescriptionItem,
    PurchaseOrder, PurchaseOrderItem, Sale, SaleItem, StockAdjustment, Notification,
    Billing, Payment, AlertRule
)
from .forms import (
    SupplierForm, CategoryForm, ProductForm, BatchForm, PatientForm, PrescriptionForm,
    PrescriptionItemForm, PurchaseOrderForm, PurchaseOrderItemForm, SaleForm,
    SaleItemForm, StockAdjustmentForm, NotificationForm, BillingForm, PaymentForm,
    AlertRuleForm, POSForm, DateRangeForm
)

# Supplier Views
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'pharmacy/supplier/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    # Get related purchase orders
    purchase_orders = PurchaseOrder.objects.filter(supplier=supplier).order_by('-order_date')
    # Get related products
    products = Product.objects.filter(batches__supplier=supplier).distinct()
    
    context = {
        'supplier': supplier,
        'purchase_orders': purchase_orders,
        'products': products,
    }
    return render(request, 'pharmacy/supplier/supplier_detail.html', context)

@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier created successfully!')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'pharmacy/supplier/supplier_form.html', {'form': form, 'title': 'Create Supplier'})

@login_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully!')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'pharmacy/supplier/supplier_form.html', {'form': form, 'title': 'Update Supplier'})

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Supplier deleted successfully!')
        return redirect('supplier_list')
    return render(request, 'pharmacy/supplier/supplier_confirm_delete.html', {'supplier': supplier})

# Category Views
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'pharmacy/category/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'pharmacy/category/category_form.html', {'form': form, 'title': 'Create Category'})

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'pharmacy/category/category_form.html', {'form': form, 'title': 'Update Category'})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('category_list')
    return render(request, 'pharmacy/category/category_confirm_delete.html', {'category': category})

# Product Views
@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'pharmacy/product/product_list.html', {'products': products})
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.shortcuts import render
from django_countries import countries

from .models import Product  # Adjust import based on your app structure

@login_required
def most_popular_by_country(request):
    selected_country = request.GET.get('country')
    selected_country_name = None
    top_products = []

    if selected_country:
        # Get the readable country name from the code
        selected_country_name = dict(countries).get(selected_country, selected_country)

        # Get top 10 most sold products from the selected country
        top_products = Product.objects.filter(
            made_in=selected_country
        ).annotate(
            total_sold=Sum('saleitem__quantity'),
            total_revenue=Sum(
                F('saleitem__quantity') * (F('saleitem__unit_price') - F('saleitem__discount'))
            )
        ).filter(
            total_sold__gt=0
        ).order_by('-total_sold')[:10]

        # Add readable country name to each product (optional for UI)
        for product in top_products:
            product.made_in_name = dict(countries).get(product.made_in, product.made_in)

    # List all distinct countries that have at least one product
    product_countries = Product.objects.exclude(made_in__isnull=True).values_list('made_in', flat=True).distinct()
    available_countries = [(code, name) for code, name in countries if code in product_countries]

    context = {
        'selected_country': selected_country,
        'selected_country_name': selected_country_name,
        'top_products': top_products,
        'countries': available_countries,
    }

    return render(request, 'pharmacy/product/most_country.html', context)


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related('batches'), pk=pk)
    batches = product.batches.filter(expiry_date__gt=date.today()).order_by('expiry_date')
    
    # Get sales data for the product
    sales_data = SaleItem.objects.filter(product=product).annotate(
        day=TruncDay('sale__date')
    ).values('day').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * (F('unit_price') - F('discount')))
    ).order_by('day')[:30]  # Last 30 days
    
    context = {
        'product': product,
        'batches': batches,
        'sales_data': sales_data,
        'stock_info': product.get_stock_info(),
    }
    return render(request, 'pharmacy/product/product_detail.html', context)

def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'pharmacy/product/product_form.html', {
        'form': form,
        'title': 'Create Product'
    })

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'pharmacy/product/product_form.html', {
        'form': form,
        'title': 'Update Product'
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('product_list')
    return render(request, 'pharmacy/product/product_confirm_delete.html', {'product': product})

# Batch Views
@login_required
def batch_list(request):
    batches = Batch.objects.all()
    return render(request, 'pharmacy/batch/batch_list.html', {'batches': batches})

@login_required
def batch_create(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Batch created successfully!')
            return redirect('batch_list')
    else:
        form = BatchForm()
    return render(request, 'pharmacy/batch/batch_form.html', {'form': form, 'title': 'Create Batch'})


@login_required
def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    return render(request, 'pharmacy/batch/batch_detail.html', {'batch': batch})

@login_required
def batch_update(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, 'Batch updated successfully!')
            return redirect('batch_list')
    else:
        form = BatchForm(instance=batch)
    return render(request, 'pharmacy/batch/batch_form.html', {'form': form, 'title': 'Update Batch'})

@login_required
def batch_delete(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        batch.delete()
        messages.success(request, 'Batch deleted successfully!')
        return redirect('batch_list')
    return render(request, 'pharmacy/batch/batch_confirm_delete.html', {'batch': batch})

# Patient Views
@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'pharmacy/patient/patient_list.html', {'patients': patients})

def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-date_prescribed')
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
    }
    return render(request, 'pharmacy/patient/patient_detail.html', context)


@login_required
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient created successfully!')
            return redirect('patient_list')
    else:
        form = PatientForm()
    return render(request, 'pharmacy/patient/patient_form.html', {'form': form, 'title': 'Create Patient'})

@login_required
def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient updated successfully!')
            return redirect('patient_list')
    else:
        form = PatientForm(instance=patient)
    return render(request, 'pharmacy/patient/patient_form.html', {'form': form, 'title': 'Update Patient'})

@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient.delete()
        messages.success(request, 'Patient deleted successfully!')
        return redirect('patient_list')
    return render(request, 'pharmacy/patient/patient_confirm_delete.html', {'patient': patient})

@login_required
def prescription_list(request):
    prescriptions = Prescription.objects.select_related('patient', 'created_by').all()
    return render(request, 'pharmacy/prescription/prescription_list.html', {
        'prescriptions': prescriptions
    })

@login_required
def prescription_create(request):
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.created_by = request.user
            prescription.save()
            messages.success(request, 'Prescription created successfully!')
            return redirect('prescription_detail', pk=prescription.pk)
    else:
        form = PrescriptionForm()
    
    return render(request, 'pharmacy/prescription/prescription_form.html', {
        'form': form,
        'title': 'Create Prescription'
    })

@login_required
def prescription_detail(request, pk):
    prescription = get_object_or_404(Prescription.objects.prefetch_related('items__product'), pk=pk)
    return render(request, 'pharmacy/prescription/prescription_detail.html', {
        'prescription': prescription,
        'items': prescription.items.all()
    })

@login_required
def prescription_update(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prescription updated successfully!')
            return redirect('prescription_detail', pk=prescription.pk)
    else:
        form = PrescriptionForm(instance=prescription)
    
    return render(request, 'pharmacy/prescription/prescription_form.html', {
        'form': form,
        'title': 'Update Prescription'
    })

@login_required
def prescription_delete(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.method == 'POST':
        prescription.delete()
        messages.success(request, 'Prescription deleted successfully!')
        return redirect('prescription_list')
    return render(request, 'pharmacy/prescription/prescription_confirm_delete.html', {
        'prescription': prescription
    })

@login_required
def prescription_item_add(request, prescription_pk):
    prescription = get_object_or_404(Prescription, pk=prescription_pk)
    if request.method == 'POST':
        form = PrescriptionItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.prescription = prescription
            item.save()
            messages.success(request, 'Item added to prescription!')
            return redirect('prescription_detail', pk=prescription.pk)
    else:
        form = PrescriptionItemForm(initial={'prescription': prescription})
    
    return render(request, 'pharmacy/prescription/prescription_item_form.html', {
        'form': form,
        'prescription': prescription,
        'title': 'Add Item to Prescription'
    })

@login_required
def prescription_item_edit(request, pk):
    item = get_object_or_404(PrescriptionItem, pk=pk)
    if request.method == 'POST':
        form = PrescriptionItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prescription item updated!')
            return redirect('prescription_detail', pk=item.prescription.pk)
    else:
        form = PrescriptionItemForm(instance=item)
    
    return render(request, 'pharmacy/prescription/prescription_item_form.html', {
        'form': form,
        'prescription': item.prescription,
        'title': 'Edit Prescription Item'
    })

@login_required
def prescription_item_delete(request, pk):
    item = get_object_or_404(PrescriptionItem, pk=pk)
    prescription_pk = item.prescription.pk
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item removed from prescription!')
        return redirect('prescription_detail', pk=prescription_pk)
    
    return render(request, 'pharmacy/prescription/prescription_item_confirm_delete.html', {
        'item': item
    })

# Purchase Order Views
@login_required
def purchase_order_list(request):
    orders = PurchaseOrder.objects.all()
    return render(request, 'pharmacy/purchase/purchase_order_list.html', {'orders': orders})

@login_required
def purchase_order_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            messages.success(request, 'Purchase order created! Add items now.')
            return redirect('purchase_order_detail', pk=order.pk)
    else:
        form = PurchaseOrderForm()
    return render(request, 'pharmacy/purchase/purchase_order_form.html', {'form': form, 'title': 'Create Purchase Order'})

@login_required
def purchase_order_detail(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    items = order.items.all()
    return render(request, 'pharmacy/purchase/purchase_order_detail.html', {
        'order': order,
        'items': items
    })

@login_required
def purchase_order_update(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Purchase order updated!')
            return redirect('purchase_order_detail', pk=order.pk)
    else:
        form = PurchaseOrderForm(instance=order)
    return render(request, 'pharmacy/purchase/purchase_order_form.html', {'form': form, 'title': 'Update Purchase Order'})

@login_required
def purchase_order_delete(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Purchase order deleted!')
        return redirect('purchase_order_list')
    return render(request, 'pharmacy/purchase/purchase_order_confirm_delete.html', {'order': order})

@login_required
def purchase_order_item_add(request, order_pk):
    order = get_object_or_404(PurchaseOrder, pk=order_pk)
    if request.method == 'POST':
        form = PurchaseOrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.order = order
            item.save()
            messages.success(request, 'Item added to purchase order!')
            return redirect('purchase_order_detail', pk=order.pk)
    else:
        form = PurchaseOrderItemForm(initial={'order': order})
    return render(request, 'pharmacy/purchase/purchase_order_item_form.html', {
        'form': form,
        'order': order,
        'title': 'Add Item to Purchase Order'
    })

@login_required
def purchase_order_item_edit(request, pk):
    item = get_object_or_404(PurchaseOrderItem, pk=pk)
    if request.method == 'POST':
        form = PurchaseOrderItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Purchase order item updated!')
            return redirect('purchase_order_detail', pk=item.order.pk)
    else:
        form = PurchaseOrderItemForm(instance=item)
    return render(request, 'pharmacy/purchase/purchase_order_item_form.html', {
        'form': form,
        'order': item.order,
        'title': 'Edit Purchase Order Item'
    })

@login_required
def purchase_order_item_delete(request, pk):
    item = get_object_or_404(PurchaseOrderItem, pk=pk)
    order_pk = item.order.pk
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item removed from purchase order!')
        return redirect('purchase_order_detail', pk=order_pk)
    return render(request, 'pharmacy/purchase/purchase_order_item_confirm_delete.html', {'item': item})

@login_required
def purchase_order_receive(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    
    # Calculate pending quantities for each item
    items_with_pending = []
    for item in order.items.all():
        pending = item.quantity - item.received_quantity
        items_with_pending.append({
            'item': item,
            'pending': pending
        })
    
    if request.method == 'POST':
        with transaction.atomic():
            for item in order.items.all():
                if item.received_quantity < item.quantity:
                    batch = Batch.objects.create(
                        product=item.product,
                        batch_number=f"PO-{order.id}-{item.id}",
                        manufacture_date=date.today() - timedelta(days=30),
                        expiry_date=date.today() + timedelta(days=365),
                        quantity=item.quantity - item.received_quantity,
                        supplier=order.supplier
                    )
                    item.received_quantity = item.quantity
                    item.save()
            
            order.status = 'received'
            order.save()
            messages.success(request, 'Purchase order marked as received and stock updated!')
            return redirect('purchase_order_detail', pk=order.pk)
    
    return render(request, 'pharmacy/purchase/purchase_order_receive.html', {
        'order': order,
        'items_with_pending': items_with_pending
    })

# Sale Views
@login_required
def sale_list(request):
    sales = Sale.objects.all()
    return render(request, 'pharmacy/sales/sale_list.html', {'sales': sales})

@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    return render(request, 'pharmacy/sales/sale_detail.html', {
        'sale': sale,
        'items': items
    })

@login_required
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            for item in sale.items.all():
                if item.batch:
                    item.batch.quantity += item.quantity
                    item.batch.save()
            sale.delete()
            messages.success(request, 'Sale deleted and stock adjusted!')
            return redirect('sale_list')
    return render(request, 'pharmacy/sales/sale_confirm_delete.html', {'sale': sale})

@login_required
def pos(request):
    cart = request.session.get('cart', [])
    products_in_cart = []
    subtotal = Decimal('0.00')
    
    # Process cart items with validation
    for item in cart:
        try:
            product = Product.objects.get(pk=item['product_id'])
            
            # Skip inactive products
            if not product.is_active:
                continue
                
            batch = Batch.objects.get(pk=item['batch_id']) if item.get('batch_id') else None
            
            # Validate batch
            if batch and (batch.quantity <= 0 or batch.expiry_date <= date.today()):
                # Find replacement batch
                new_batch = Batch.objects.filter(
                    product=product,
                    quantity__gt=0,
                    expiry_date__gt=date.today()
                ).order_by('expiry_date').first()
                
                if new_batch:
                    item['batch_id'] = new_batch.id
                    request.session.modified = True
                    batch = new_batch
                else:
                    continue
            
            # Calculate item total
            discount = Decimal(str(item.get('discount', 0)))
            quantity = item['quantity']
            item_total = (product.selling_price - discount) * quantity
            
            products_in_cart.append({
                'product': product,
                'batch': batch,
                'quantity': quantity,
                'unit_price': product.selling_price,
                'discount': discount,
                'total_price': item_total,
                'item_id': item['item_id']
            })
            
            subtotal += item_total
            
        except (Product.DoesNotExist, Batch.DoesNotExist):
            continue
    
    total_amount = subtotal
    
    if request.method == 'POST':
        form = POSForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            discount = form.cleaned_data['discount'] or Decimal('0.00')
            
            # Validate quantity
            if quantity <= 0:
                messages.error(request, 'Quantity must be at least 1')
                return redirect('pos')
            
            # Find available batches
            batches = Batch.objects.filter(
                product=product,
                quantity__gt=0,
                expiry_date__gt=date.today()
            ).order_by('expiry_date')
            
            if not batches.exists():
                messages.error(request, f'No stock available for {product.name}!')
                return redirect('pos')
                
            # Check available quantity
            available_quantity = batches.aggregate(total=Sum('quantity'))['total']
            if quantity > available_quantity:
                messages.warning(request, 
                    f'Only {available_quantity} units of {product.name} available. Added maximum available quantity.')
                quantity = available_quantity
            
            # Find best batch (FIFO)
            batch_to_use = None
            remaining_quantity = quantity
            
            for batch in batches:
                if remaining_quantity <= 0:
                    break
                
                use_qty = min(remaining_quantity, batch.quantity)
                if not batch_to_use or batch_to_use.id == batch.id:
                    batch_to_use = batch
                else:
                    messages.warning(request,
                        f'Stock for {product.name} is spread across multiple batches. Using batch {batch_to_use.batch_number}.')
                    break
                
                remaining_quantity -= use_qty
            
            # Add to cart
            if 'cart' not in request.session:
                request.session['cart'] = []
            
            request.session['cart'].append({
                'item_id': len(request.session['cart']),
                'product_id': product.id,
                'batch_id': batch_to_use.id,
                'quantity': quantity,
                'discount': float(discount)
            })
            request.session.modified = True
            messages.success(request, f'{quantity} x {product.name} added to cart')
            return redirect('pos')
    else:
        form = POSForm()
    
    # Get popular products for quick add
    popular_products = Product.objects.filter(
        is_active=True,
        batches__quantity__gt=0,
        batches__expiry_date__gt=date.today()
    ).distinct().order_by('-sales_count')[:8]
    
    return render(request, 'pharmacy/pos/pos.html', {
        'form': form,
        'products_in_cart': products_in_cart,
        'subtotal': subtotal,
        'total_amount': total_amount,
        'popular_products': popular_products
    })


@login_required
def pos_remove_item(request, item_id):
    cart = request.session.get('cart', [])
    request.session['cart'] = [item for item in cart if item['item_id'] != item_id]
    request.session.modified = True
    messages.success(request, 'Item removed from cart!')
    return redirect('pos')

@login_required
def pos_checkout(request):
    cart = request.session.get('cart', [])
    if not cart:
        messages.error(request, 'Cart is empty!')
        return redirect('pos')
    
    # Calculate totals with validation
    subtotal = Decimal('0.00')
    valid_items = []
    
    for item in cart:
        try:
            product = Product.objects.get(pk=item['product_id'])
            batch = Batch.objects.get(pk=item['batch_id']) if item.get('batch_id') else None
            
            discount = Decimal(str(item.get('discount', 0)))
            quantity = item['quantity']
            item_total = (product.selling_price - discount) * quantity
            
            valid_items.append({
                'product': product,
                'batch': batch,
                'quantity': quantity,
                'discount': discount,
                'item_total': item_total
            })
            
            subtotal += item_total
        except (Product.DoesNotExist, Batch.DoesNotExist):
            continue
    
    if not valid_items:
        messages.error(request, 'No valid items in cart!')
        return redirect('pos')
    
    total_amount = subtotal
    
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Generate invoice number
                    today = date.today()
                    last_invoice = Sale.objects.filter(
                        date__date=today
                    ).order_by('-date').first()
                    
                    if last_invoice:
                        last_num = int(last_invoice.invoice_number.split('-')[-1])
                        invoice_num = f"{today.strftime('%Y%m%d')}-{last_num + 1:04d}"
                    else:
                        invoice_num = f"{today.strftime('%Y%m%d')}-0001"
                    
                    # Create sale
                    sale = Sale.objects.create(
                        invoice_number=invoice_num,
                        patient=form.cleaned_data['patient'],
                        payment_method=form.cleaned_data['payment_method'],
                        subtotal=subtotal,
                        discount_amount=Decimal('0.00'),
                        total_amount=total_amount,
                        notes=form.cleaned_data['notes'],
                        created_by=request.user
                    )
                    
                    # Process items
                    for item in valid_items:
                        product = item['product']
                        batch = item['batch']
                        quantity = item['quantity']
                        discount = item['discount']
                        
                        # Verify stock
                        if batch and batch.quantity < quantity:
                            raise ValueError(f"Insufficient stock for {product.name}")
                        
                        # Create sale item
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            batch=batch,
                            quantity=quantity,
                            unit_price=product.selling_price,
                            discount=discount
                        )
                        
                        # Update stock
                        if batch:
                            batch.quantity -= quantity
                            batch.save()
                        
                        # Update product sales count
                        product.sales_count += quantity
                        product.save()
                        
                        # Check for low stock
                        if product.get_stock_quantity() <= product.min_stock_level:
                            Notification.objects.create(
                                title=f'Low Stock: {product.name}',
                                message=f'{product.name} is below minimum stock level.',
                                notification_type='low_stock',
                                related_object_id=product.id,
                                related_content_type='product',
                                recipient=request.user
                            )
                    
                    # Clear cart
                    request.session['cart'] = []
                    request.session.modified = True
                    
                    messages.success(request, f'Sale completed! Invoice #{sale.invoice_number}')
                    return redirect('sale_detail', pk=sale.pk)
            
            except Exception as e:
                messages.error(request, f'Error processing sale: {str(e)}')
                return redirect('pos_checkout')
    else:
        form = SaleForm()
    
    return render(request, 'pharmacy/pos/pos_checkout.html', {
        'form': form,
        'products_in_cart': [{
            'product': item['product'],
            'batch': item['batch'],
            'quantity': item['quantity'],
            'unit_price': item['product'].selling_price,
            'discount': item['discount'],
            'total_price': item['item_total'],
            'item_id': -1  # Dummy ID for template
        } for item in valid_items],
        'subtotal': subtotal,
        'total_amount': total_amount
    })

@login_required
def ajax_product_batches(request, product_id):
    batches = Batch.objects.filter(
        product_id=product_id,
        quantity__gt=0,
        expiry_date__gt=date.today()
    ).order_by('expiry_date')
    
    data = [{
        'id': batch.id,
        'text': f"{batch.batch_number} (Exp: {batch.expiry_date.strftime('%Y-%m-%d')}, Qty: {batch.quantity})",
        'expiry_date': batch.expiry_date.strftime('%Y-%m-%d'),
        'quantity': batch.quantity
    } for batch in batches]
    
    return JsonResponse(data, safe=False)

@login_required
def ajax_product_by_barcode(request):
    barcode = request.GET.get('barcode', '').strip()
    if not barcode:
        return JsonResponse({'error': 'No barcode provided'}, status=400)
    
    try:
        product = Product.objects.get(barcode=barcode, is_active=True)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'price': str(product.selling_price)
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    

@login_required
def ajax_product_stock(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
        batches = Batch.objects.filter(
            product=product,
            quantity__gt=0,
            expiry_date__gt=date.today()
        ).order_by('expiry_date')
        
        total_quantity = batches.aggregate(total=Sum('quantity'))['total'] or 0
        
        return JsonResponse({
            'available': total_quantity > 0,
            'quantity': total_quantity,
            'batches': [{
                'batch_number': b.batch_number,
                'quantity': b.quantity,
                'expiry_date': b.expiry_date.strftime('%Y-%m-%d')
            } for b in batches]
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

# Stock Adjustment Views
@login_required
def stock_adjustment_list(request):
    adjustments = StockAdjustment.objects.select_related(
        'batch', 'batch__product', 'adjusted_by'
    ).order_by('-date') 
    return render(request, 'pharmacy/inventory/stock_adjustment_list.html', {'adjustments': adjustments})

@login_required
def stock_adjustment_create(request):
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    adjustment = form.save(commit=False)
                    adjustment.adjusted_by = request.user

                    if adjustment.batch:
                        # Ensure the new stock quantity is not negative
                        new_quantity = adjustment.batch.quantity + adjustment.quantity
                        if new_quantity < 0:
                            messages.error(request, 'Adjustment would result in negative stock!')
                            return redirect('stock_adjustment_create')

                        adjustment.batch.quantity = new_quantity
                        adjustment.batch.save()

                    adjustment.save()

                    # Check for low stock and notify if needed
                    if (adjustment.batch and 
                        adjustment.batch.product.get_stock_quantity() <= adjustment.batch.product.min_stock_level):
                        Notification.objects.create(
                            title=f'Low Stock: {adjustment.batch.product.name}',
                            message=f'{adjustment.batch.product.name} is below minimum stock level after adjustment.',
                            notification_type='low_stock',
                            recipient=request.user
                        )

                    messages.success(request, 'Stock adjustment recorded!')
                    return redirect('stock_adjustment_list')
            except Exception as e:
                messages.error(request, f'Error recording adjustment: {str(e)}')
    else:
        form = StockAdjustmentForm()

    return render(request, 'pharmacy/inventory/stock_adjustment_form.html', {
        'form': form,
        'title': 'Create Stock Adjustment'
    })

# Reports
@login_required
def inventory_report(request):
    products = Product.objects.annotate(
        total_stock=Sum('batches__quantity'),
        total_value=ExpressionWrapper(
            F('total_stock') * F('cost_price'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('name')
    
    low_stock = products.filter(total_stock__lte=F('min_stock_level')).exclude(total_stock=0)
    out_of_stock = products.filter(total_stock=0)
    
    context = {
        'products': products,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'report_date': date.today()
    }
    return render(request, 'pharmacy/reports/inventory_report.html', context)

@login_required
def expiry_report(request):
    soon = date.today() + timedelta(days=30)
    expiring_soon = Batch.objects.filter(
        expiry_date__gte=date.today(),
        expiry_date__lte=soon,
        quantity__gt=0
    ).select_related('product').order_by('expiry_date')
    
    expired = Batch.objects.filter(
        expiry_date__lt=date.today(),
        quantity__gt=0
    ).select_related('product').order_by('expiry_date')
    
    context = {
        'expiring_soon': expiring_soon,
        'expired': expired,
        'report_date': date.today(),
        'soon_date': soon
    }
    return render(request, 'pharmacy/reports/expiry_report.html', context)

@login_required
def sales_report(request):
    form = DateRangeForm(request.GET or None)
    
    # Default to current month
    start_date = date.today().replace(day=1)
    end_date = date.today()
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date'] or start_date
        end_date = form.cleaned_data['end_date'] or end_date
    
    # Get sales data for daily trend
    sales = Sale.objects.filter(
        date__date__gte=start_date,
        date__date__lte=end_date
    ).annotate(
        day=TruncDay('date')
    ).values('day').annotate(
        total_sales=Sum('total_amount'),
        num_transactions=Count('id')
    ).order_by('day')
    
    # Calculate metrics
    total_revenue = Sale.objects.filter(
        date__date__gte=start_date,
        date__date__lte=end_date
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_transactions = Sale.objects.filter(
        date__date__gte=start_date,
        date__date__lte=end_date
    ).count()
    
    average_order_value = total_revenue / total_transactions if total_transactions > 0 else 0
    
    # Get top products with percentage
    top_products = SaleItem.objects.filter(
        sale__date__date__gte=start_date,
        sale__date__date__lte=end_date
    ).values('product__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price') - F('discount'))
    ).order_by('-total_revenue')[:10]
    
    # Add percentage of total sales
    for product in top_products:
        product['percentage'] = (product['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
    
    # Get payment method breakdown with percentage
    payment_methods = Sale.objects.filter(
        date__date__gte=start_date,
        date__date__lte=end_date
    ).values('payment_method').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('-total')
    
    for method in payment_methods:
        method['percentage'] = (method['total'] / total_revenue * 100) if total_revenue > 0 else 0
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'sales': sales,
        'top_products': top_products,
        'payment_methods': payment_methods,
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'average_order_value': average_order_value,
        'report_date': date.today(),
        'form': form
    }
    return render(request, 'pharmacy/reports/sales_report.html', context)

@login_required
def financial_summary(request):
    form = DateRangeForm(request.GET or None)
    
    # Default to current month
    start_date = date.today().replace(day=1)
    end_date = date.today()
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date'] or start_date
        end_date = form.cleaned_data['end_date'] or end_date
    
    # Calculate revenue
    revenue = Sale.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).aggregate(
        total_revenue=Sum('total_amount'),
        avg_sale=Avg('total_amount')
    )
    
    # Calculate expenses
    expenses = PurchaseOrder.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date,
        status='received'
    ).aggregate(
        total_expenses=Sum('total_amount')
    )
    
    # Calculate profit
    profit = (revenue['total_revenue'] or 0) - (expenses['total_expenses'] or 0)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'revenue': revenue,
        'expenses': expenses,
        'profit': profit,
        'report_date': date.today(),
        'form': form
    }
    return render(request, 'pharmacy/reports/financial_summary.html', context)

# Billing & Payment Views
@login_required
def billing_list(request):
    billings = Billing.objects.all().order_by('-date')
    return render(request, 'pharmacy/billing/billing_list.html', {'billings': billings})

@login_required
def billing_create(request):
    if request.method == 'POST':
        form = BillingForm(request.POST)
        if form.is_valid():
            billing = form.save(commit=False)
            billing.created_by = request.user
            billing.save()
            messages.success(request, 'Billing record created!')
            return redirect('billing_detail', pk=billing.pk)
    else:
        form = BillingForm(initial={
            'date': date.today(),
            'due_date': date.today() + timedelta(days=30)
        })
    return render(request, 'pharmacy/billing/billing_form.html', {
        'form': form,
        'title': 'Create Billing'
    })

@login_required
def billing_detail(request, pk):
    billing = get_object_or_404(Billing, pk=pk)
    payments = billing.payments.all()
    return render(request, 'pharmacy/billing/billing_detail.html', {
        'billing': billing,
        'payments': payments
    })

@login_required
def billing_update(request, pk):
    billing = get_object_or_404(Billing, pk=pk)
    if request.method == 'POST':
        form = BillingForm(request.POST, instance=billing)
        if form.is_valid():
            form.save()
            messages.success(request, 'Billing record updated!')
            return redirect('billing_detail', pk=billing.pk)
    else:
        form = BillingForm(instance=billing)
    return render(request, 'pharmacy/billing/billing_form.html', {
        'form': form,
        'title': 'Update Billing'
    })

@login_required
def billing_delete(request, pk):
    billing = get_object_or_404(Billing, pk=pk)
    if request.method == 'POST':
        billing.delete()
        messages.success(request, 'Billing record deleted!')
        return redirect('billing_list')
    return render(request, 'pharmacy/billing/billing_confirm_delete.html', {
        'billing': billing
    })


@login_required
def payment_list(request):
    payments = Payment.objects.select_related('billing', 'billing__patient').all().order_by('-payment_date')
    return render(request, 'pharmacy/billing/payment_list.html', {'payments': payments})

@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('billing', 'billing__patient'), pk=pk)
    return render(request, 'pharmacy/billing/payment_detail.html', {'payment': payment})

@login_required
def payment_create(request, billing_pk):
    billing = get_object_or_404(Billing, pk=billing_pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.billing = billing
            payment.created_by = request.user
            
            # Update billing payment status
            total_paid = billing.payments.aggregate(total=Sum('amount'))['total'] or 0
            total_paid += payment.amount
            
            if total_paid >= billing.total_amount:
                billing.payment_status = 'paid'
            elif total_paid > 0:
                billing.payment_status = 'partially_paid'
            else:
                billing.payment_status = 'pending'
            
            with transaction.atomic():
                payment.save()
                billing.save()
            
            messages.success(request, 'Payment recorded!')
            return redirect('billing_detail', pk=billing.pk)
    else:
        form = PaymentForm(initial={
            'payment_date': date.today(),
            'amount': billing.total_amount - (billing.payments.aggregate(total=Sum('amount'))['total'] or 0)
        })
    
    return render(request, 'pharmacy/billing/payment_form.html', {
        'form': form,
        'billing': billing,
        'title': 'Record Payment'
    })

@login_required
def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated!')
            return redirect('billing_detail', pk=payment.billing.pk)
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'pharmacy/billing/payment_form.html', {
        'form': form,
        'billing': payment.billing,
        'title': 'Update Payment'
    })

@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    billing_pk = payment.billing.pk
    if request.method == 'POST':
        payment.delete()
        
        # Update billing payment status
        billing = Billing.objects.get(pk=billing_pk)
        total_paid = billing.payments.aggregate(total=Sum('amount'))['total'] or 0
        
        if total_paid >= billing.total_amount:
            billing.payment_status = 'paid'
        elif total_paid > 0:
            billing.payment_status = 'partially_paid'
        else:
            billing.payment_status = 'pending'
        
        billing.save()
        
        messages.success(request, 'Payment deleted!')
        return redirect('billing_detail', pk=billing_pk)
    return render(request, 'pharmacy/billing/payment_confirm_delete.html', {
        'payment': payment
    })

# Add to views.py
@login_required
def payment_select_billing(request):
    billings = Billing.objects.filter(payment_status__in=['pending', 'partially_paid']).order_by('-date')
    return render(request, 'pharmacy/billing/payment_select_billing.html', {'billings': billings})

# Notification Views
@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:50]  # Limit to 50 most recent
    
    # Mark all as read when viewing
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return render(request, 'pharmacy/notifications/notification_list.html', {
        'notifications': notifications
    })

@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    # Redirect to notification URL if exists, otherwise to notification list
    if notification.url:
        return redirect(notification.url)
    return redirect('notification_list')

@login_required
def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully.')
    return redirect('notification_list')

@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read")
    return redirect('notification_list')

# Alert Rule Views
@login_required
def alert_rules(request):
    rules = AlertRule.objects.all()
    return render(request, 'pharmacy/alerts/alert_rules.html', {'alert_rules': rules})

@login_required
def alert_rule_create(request):
    if request.method == 'POST':
        form = AlertRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()
            messages.success(request, 'Alert rule created successfully!')
            return redirect('alert_rules')
    else:
        form = AlertRuleForm()
    return render(request, 'pharmacy/alerts/alert_rule_form.html', {'form': form})

@login_required
def alert_rule_detail(request, pk):
    rule = get_object_or_404(AlertRule, pk=pk)
    recent_notifications = Notification.objects.filter(
        notification_type=rule.alert_type,
        related_object_id=rule.product.id if rule.product else None
    ).order_by('-created_at')[:10]
    
    return render(request, 'pharmacy/alerts/alert_rule_detail.html', {
        'alert_rule': rule,
        'recent_notifications': recent_notifications
    })

@login_required
def alert_rule_update(request, pk):
    rule = get_object_or_404(AlertRule, pk=pk)
    if request.method == 'POST':
        form = AlertRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Alert rule updated successfully!')
            return redirect('alert_rules')
    else:
        form = AlertRuleForm(instance=rule)
    return render(request, 'pharmacy/alerts/alert_rule_form.html', {'form': form})

@login_required
def alert_rule_delete(request, pk):
    rule = get_object_or_404(AlertRule, pk=pk)
    if request.method == 'POST':
        rule.delete()
        messages.success(request, 'Alert rule deleted successfully!')
        return redirect('alert_rules')
    return render(request, 'pharmacy/alerts/alert_rule_confirm_delete.html', {'alert_rule': rule})


# AJAX Views
@login_required
def ajax_product_batches(request, product_id):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    batches = Batch.objects.filter(
        product_id=product_id,
        quantity__gt=0,
        expiry_date__gt=date.today()
    ).order_by('expiry_date')
    
    data = [{
        'id': batch.id,
        'text': f"{batch.batch_number} (Exp: {batch.expiry_date.strftime('%Y-%m-%d')}, Qty: {batch.quantity})",
        'expiry_date': batch.expiry_date.strftime('%Y-%m-%d'),
        'quantity': batch.quantity
    } for batch in batches]
    
    return JsonResponse(data, safe=False)








from django.db.models import Sum, Count, F, FloatField, ExpressionWrapper, Avg
from django.db.models.functions import Coalesce
from django_countries import countries
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Product, SaleItem  # Replace 'your_app' with your actual app name

@login_required
def country_performance_report(request):
    # Get time period (default to 90 days)
    days = int(request.GET.get('days', 90))
    start_date = date.today() - timedelta(days=days)
    
    # Get previous period for comparison
    prev_start_date = start_date - timedelta(days=days)
    
    # Get all countries with products
    product_countries = Product.objects.exclude(made_in__isnull=True).values_list('made_in', flat=True).distinct()
    available_countries = [(code, name) for code, name in countries if code in product_countries]
    
    # Get top countries by revenue
    top_countries_data = (
        Product.objects
        .filter(saleitem__sale__date__gte=start_date)
        .exclude(made_in__isnull=True)
        .values('made_in')
        .annotate(
            revenue=Sum(F('saleitem__quantity') * (F('saleitem__unit_price') - F('saleitem__discount'))),
            units_sold=Sum('saleitem__quantity'),
            product_count=Count('id', distinct=True),
            avg_margin=ExpressionWrapper(
                Coalesce(
                    Avg(
                        (F('saleitem__unit_price') - F('saleitem__discount') - F('cost_price')) / 
                        F('cost_price') * 100
                    ),
                    0
                ),
                output_field=FloatField()
            )
        )
        .order_by('-revenue')[:5]
    )
    
    # Get top products for each country
    top_countries = []
    for country_data in top_countries_data:
        country_code = country_data['made_in']
        country_name = dict(countries).get(country_code, country_code)
        
        top_products = (
            Product.objects
            .filter(made_in=country_code, saleitem__sale__date__gte=start_date)
            .annotate(
                units_sold=Sum('saleitem__quantity')
            )
            .order_by('-units_sold')[:3]
        )
        
        top_countries.append({
            'code': country_code,
            'name': country_name,
            'revenue': country_data['revenue'] or 0,
            'units_sold': country_data['units_sold'] or 0,
            'avg_margin': country_data['avg_margin'],
            'product_count': country_data['product_count'],
            'top_products': top_products
        })
    
    # Get top country
    top_country = top_countries[0] if top_countries else None
    
    # Calculate growth for top country
    top_country_growth = None
    top_country_revenue_growth = None
    top_country_product_growth = None
    
    if top_country:
        # Revenue growth
        prev_revenue = (
            Product.objects
            .filter(made_in=top_country['code'], saleitem__sale__date__gte=prev_start_date, saleitem__sale__date__lt=start_date)
            .aggregate(
                revenue=Sum(F('saleitem__quantity') * (F('saleitem__unit_price') - F('saleitem__discount')))
            )['revenue'] or 0
        )
        
        if prev_revenue > 0:
            top_country_revenue_growth = round(
                ((top_country['revenue'] - prev_revenue) / prev_revenue * 100), 1  # Fixed missing parenthesis
            )
        
        # Product count growth
        prev_product_count = Product.objects.filter(
            made_in=top_country['code'],
            created_at__lt=start_date
        ).count()
        
        if prev_product_count > 0:
            top_country_product_growth = round(
                ((top_country['product_count'] - prev_product_count) / prev_product_count * 100), 1
            )
    
    # Prepare data for chart
    chart_countries = (
        Product.objects
        .filter(saleitem__sale__date__gte=start_date)
        .exclude(made_in__isnull=True)
        .values('made_in')
        .annotate(
            revenue=Sum(F('saleitem__quantity') * (F('saleitem__unit_price') - F('saleitem__discount'))),
            units_sold=Sum('saleitem__quantity')
        )
        .order_by('-revenue')[:10]
    )
    
    country_names = []
    country_revenues = []
    country_units_sold = []
    
    for item in chart_countries:
        country_names.append(dict(countries).get(item['made_in'], item['made_in']))
        country_revenues.append(float(item['revenue'] or 0))
        country_units_sold.append(item['units_sold'] or 0)
    
    context = {
        'top_country': top_country,
        'top_country_revenue': top_country['revenue'] if top_country else 0,
        'top_country_revenue_growth': top_country_revenue_growth,
        'top_country_product_count': top_country['product_count'] if top_country else 0,
        'top_country_product_growth': top_country_product_growth,
        'top_country_growth': top_country_growth,
        'top_countries': top_countries,
        'country_count': len(available_countries),
        'country_names': country_names,
        'country_revenues': country_revenues,
        'country_units_sold': country_units_sold,
        'country_count_growth': None,  # Could implement similar to above
    }
    
    return render(request, 'pharmacy/reports/country_performance.html', context)


