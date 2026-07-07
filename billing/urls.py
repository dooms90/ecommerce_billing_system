from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('invoice/<int:invoice_id>/', views.invoice_view, name='invoice_view'),
    path('orders/', views.order_history, name='order_history'),
    path('search-ajax/', views.search_products_ajax, name='search_products_ajax'),
    path('dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('invoice/<int:invoice_id>/pdf/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('checkout/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('checkout/remove-coupon/', views.remove_coupon, name='remove_coupon'),
]