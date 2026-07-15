E-commerce Billing System

A full-stack e-commerce and billing web application built with Django and MySQL. Customers can browse products, manage a cart, apply coupons, check out with GST-compliant tax calculation, and download invoices — while admins get a dedicated sales dashboard.

## ✨ Features

### 👤 Customer-facing Features

- 🔐 Signup, Login & Logout (Django Authentication)
- 🔍 Live AJAX Product Search
- 🔎 Advanced Search with Category Filter
- 🗂️ Category Browsing Page
- 🛍️ Product Catalog with Product Detail Pages
- 🛒 Session-based Shopping Cart with Live Item Count Badge
- 🎟️ Coupon Code Support (Percentage & Flat Discount)
- 💳 Payment Method Selection (Cash on Delivery / Card / UPI – Simulated)
- 📍 Separate Billing & Shipping Addresses
- 🧾 GST-Compliant Tax Calculation (0%, 5%, 18%, 40%)
- 🚚 Shipping Charge Calculation
- 🧮 Financial Year-Based Invoice Number Generation (e.g., INV/2026-27/0001)
- 📄 Printable Invoice & PDF Download
- 📦 Customer Order History

## Admin-facing
- Full Django admin panel — manage Products, Categories, Coupons, Orders, Invoices, Customers
- Sales dashboard — total orders, revenue, tax collected, top-selling products
- Date-range filters on the dashboard (This Week / This Month / Last Month / This Year / custom range)
- Stock visibility restricted to staff/superuser accounts

## 🛠️ Tech Stack

| Layer | Technology |
|--------|------------|
| Backend | Python, Django |
| Database | MySQL |
| Frontend | HTML5, CSS3, JavaScript (AJAX) |
| PDF Generation | xhtml2pdf |
| Image Handling | Pillow |

📁 Project Structure
## 📁 Project Structure

```text
ecommerce_billing_system/
├── billing/
│   ├── models.py              # Category, Product, Customer, Order, OrderItem, Invoice, Coupon
│   ├── views.py               # Business logic (cart, checkout, invoice, dashboard)
│   ├── urls.py
│   ├── admin.py
│   ├── context_processors.py
│   ├── templates/
│   │   └── billing/           # HTML templates
│   └── static/
│       └── billing/           # CSS, JavaScript, Images
├── Ecommerce_billing_system/
│   ├── settings.py
│   └── urls.py
├── manage.py
├── requirements.txt
├── .env                      
└── .gitignore            
```
Demo link :
http://127.0.0.1:8000/
<br>
http://127.0.0.1:8000/admin
