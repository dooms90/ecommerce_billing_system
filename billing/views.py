from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import uuid
from .models import Product, Category, Customer, Order, OrderItem, Invoice, Coupon
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse

def generate_invoice_number():
    now = timezone.now()

    if now.month >= 4:
        fy_start_year = now.year
        fy_end_year = now.year + 1
    else:
        fy_start_year = now.year - 1
        fy_end_year = now.year

    fy_label = f"{fy_start_year}-{str(fy_end_year)[-2:]}"

    count_this_fy = Invoice.objects.filter(invoice_number__contains=f"/{fy_label}/").count()
    next_number = count_this_fy + 1

    return f"INV/{fy_label}/{next_number:04d}"


def home(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    if query:
        products = products.filter(name__icontains=query)

    if category_id:
        products = products.filter(category__id=category_id)

    return render(request, 'billing/home.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'billing/product_detail.html', {
        'product': product,
    })


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity

    request.session['cart'] = cart
    return redirect('view_cart')


def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    grand_total = 0

    for product_id_str, quantity in cart.items():
        product = get_object_or_404(Product, id=int(product_id_str))
        subtotal = product.price * quantity
        grand_total += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return render(request, 'billing/cart.html', {
        'cart_items': cart_items,
        'grand_total': grand_total,
    })


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart

    return redirect('view_cart')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        Customer.objects.create(user=user, phone=phone)

        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')

    return render(request, 'billing/signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'billing/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('view_cart')

    cart_items = []
    subtotal_total = 0
    for product_id_str, quantity in cart.items():
        product = get_object_or_404(Product, id=int(product_id_str))
        subtotal = product.price * quantity
        subtotal_total += subtotal
        cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})

    discount_amount = 0
    coupon_code = request.session.get('coupon_code')
    coupon_error = None

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            discount_amount = coupon.calculate_discount(subtotal_total)
        except Coupon.DoesNotExist:
            coupon_error = "Applied coupon is no longer valid."
            del request.session['coupon_code']
            coupon_code = None

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cod')
        billing_address = request.POST.get('billing_address', '').strip()
        same_as_billing = request.POST.get('same_as_billing') == 'on'
        shipping_address = billing_address if same_as_billing else request.POST.get('shipping_address', '').strip()

        customer, created = Customer.objects.get_or_create(user=request.user)
        order = Order.objects.create(
            customer=customer,
            status='paid',
            payment_method=payment_method,
            billing_address=billing_address,
            shipping_address=shipping_address,
            same_as_billing=same_as_billing
        )

        subtotal_recalc = 0
        tax_total = 0

        for product_id_str, quantity in cart.items():
            product = get_object_or_404(Product, id=int(product_id_str))
            category_tax_rate = product.category.tax_rate if product.category else 18

            item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price,
                tax_rate_applied=category_tax_rate
            )

            subtotal_recalc += item.subtotal()
            tax_total += item.tax_amount()

            product.stock = max(0, product.stock - quantity)
            product.save()

        final_discount = 0
        final_coupon_code = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
                final_discount = coupon.calculate_discount(subtotal_recalc)
                final_coupon_code = coupon.code
            except Coupon.DoesNotExist:
                pass

        shipping_charge = 50
        final_total = subtotal_recalc + tax_total - final_discount + shipping_charge

        invoice_number = generate_invoice_number()
        invoice = Invoice.objects.create(
            order=order,
            invoice_number=invoice_number,
            tax_amount=round(tax_total, 2),
            discount_amount=round(final_discount, 2),
            coupon_code=final_coupon_code,
            shipping_charge=shipping_charge,
            grand_total=round(final_total, 2)
        )

        request.session['cart'] = {}
        request.session.pop('coupon_code', None)

        return redirect('invoice_view', invoice_id=invoice.id)

    grand_total_estimate = subtotal_total - discount_amount

    return render(request, 'billing/checkout.html', {
        'cart_items': cart_items,
        'subtotal_total': subtotal_total,
        'discount_amount': discount_amount,
        'coupon_code': coupon_code,
        'coupon_error': coupon_error,
        'grand_total': grand_total_estimate,
    })

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip()
        if Coupon.objects.filter(code__iexact=code, active=True).exists():
            request.session['coupon_code'] = code
        else:
            request.session['coupon_code'] = None
            request.session.pop('coupon_code', None)
    return redirect('checkout')


@login_required
def remove_coupon(request):
    request.session.pop('coupon_code', None)
    return redirect('checkout')

@login_required
def invoice_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    order = invoice.order
    items = order.items.all()

    return render(request, 'billing/invoice.html', {
        'invoice': invoice,
        'order': order,
        'items': items,
    })

@login_required
def order_history(request):
    customer, created = Customer.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')

    return render(request, 'billing/order_history.html', {
        'orders': orders,
    })

from django.http import JsonResponse

def search_products_ajax(request):
    query = request.GET.get('q', '')
    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)[:8]
    else:
        products = products.none()

    results = []
    for p in products:
        results.append({
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
            'stock': p.stock,
            'url': f'/product/{p.id}/',
        })

    return JsonResponse({'results': results})

@staff_member_required
def sales_dashboard(request):
    from datetime import datetime

    orders_qs = Order.objects.filter(status='paid')
    invoices_qs = Invoice.objects.all()

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    quick_filter = request.GET.get('quick_filter', '')

    now = timezone.now()

    if quick_filter == 'this_week':
        start = now - timezone.timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start)
        invoices_qs = invoices_qs.filter(order__created_at__gte=start)
   
    elif quick_filter == 'this_month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start)
        invoices_qs = invoices_qs.filter(order__created_at__gte=start)
    elif quick_filter == 'last_month':
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = first_of_this_month
        last_month_start = (first_of_this_month - timezone.timedelta(days=1)).replace(day=1)
        orders_qs = orders_qs.filter(created_at__gte=last_month_start, created_at__lt=last_month_end)
        invoices_qs = invoices_qs.filter(order__created_at__gte=last_month_start, order__created_at__lt=last_month_end)
    elif quick_filter == 'this_year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start)
        invoices_qs = invoices_qs.filter(order__created_at__gte=start)
    elif start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timezone.timedelta(days=1)
            orders_qs = orders_qs.filter(created_at__gte=start_dt, created_at__lt=end_dt)
            invoices_qs = invoices_qs.filter(order__created_at__gte=start_dt, order__created_at__lt=end_dt)
        except ValueError:
            pass

    total_orders = orders_qs.count()
    total_revenue = invoices_qs.aggregate(total=Sum('grand_total'))['total'] or 0
    total_tax_collected = invoices_qs.aggregate(total=Sum('tax_amount'))['total'] or 0

    filtered_order_ids = orders_qs.values_list('id', flat=True)

    top_products = (
        OrderItem.objects.filter(order__id__in=filtered_order_ids)
        .values('product__name')
        .annotate(total_sold=Sum('quantity'), revenue=Sum('price_at_purchase'))
        .order_by('-total_sold')[:5]
    )

    recent_orders = orders_qs.order_by('-created_at')

    return render(request, 'billing/sales_dashboard.html', {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_tax_collected': total_tax_collected,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'start_date': start_date,
        'end_date': end_date,
        'quick_filter': quick_filter,
    })

@login_required
def download_invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    order = invoice.order
    items = order.items.all()

    template = get_template('billing/invoice_pdf.html')
    html = template.render({
        'invoice': invoice,
        'order': order,
        'items': items,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response