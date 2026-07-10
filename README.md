E-commerce Billing System

A full-stack e-commerce and billing web application built with Django and MySQL. Customers can browse products, manage a cart, apply coupons, check out with GST-compliant tax calculation, and download invoices — while admins get a dedicated sales dashboard.

✨ Features

Customer-facing
🔐 Signup / Login / Logout (Django authentication)
🔍 Product search — live AJAX search + full search & category filter
🗂️ Category browsing page
🛍️ Product catalog with detail pages
🛒 Session-based shopping cart with live item-count badge
🎟️ Coupon codes — percentage or flat discount, applied before tax
💳 Payment method selection (Cash on Delivery / Card / UPI — simulated)
📍 Separate billing & shipping addresses
🧾 GST-compliant tax calculation, per product category (0% / 5% / 18% / 40%)
🚚 Shipping charge on invoice
🧮 Financial-year based invoice numbering (INV/2026-27/0001)
📄 Invoice print & PDF download
📦 Customer order history

Admin-facing
⚙️ Full Django admin panel — manage Products, Categories, Coupons, Orders, Invoices, Customers
📊 Sales dashboard — total orders, revenue, tax collected, top-selling products
📅 Date-range filters on the dashboard (This Week / This Month / Last Month / This Year / custom range)
📈 Stock visibility restricted to staff/superuser accounts


