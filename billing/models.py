from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    TAX_CHOICES = [
        (0, '0% - Essential/Exempt goods'),
        (5, '5% - Daily essentials, groceries, medicines'),
        (18, '18% - Standard rate (electronics, clothing, most goods)'),
        (40, '40% - Luxury/sin goods'),
    ]

    name = models.CharField(max_length=100)
    tax_rate = models.PositiveIntegerField(choices=TAX_CHOICES, default=18)

    def __str__(self):
        return f"{self.name} ({self.tax_rate}% GST)"


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Percentage'),
        ('flat', 'Flat Amount'),
    ]

    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percent':
            return round(subtotal * self.discount_value / 100, 2)
        else:
            return min(self.discount_value, subtotal)


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cod')

    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    same_as_billing = models.BooleanField(default=True)

    def total_amount(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"Order #{self.id} - {self.customer.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate_applied = models.PositiveIntegerField(default=18)

    def subtotal(self):
        return self.quantity * self.price_at_purchase

    def tax_amount(self):
        return round(self.subtotal() * self.tax_rate_applied / 100, 2)

    def total_with_tax(self):
        return self.subtotal() + self.tax_amount()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=30, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=20, blank=True, null=True)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Invoice {self.invoice_number}"