from django.urls import path, include
from .views import (
    home_page_view,
    product_detail_view,
    add_product_to_cart_or_remove,
    category_product_list_view,
    customer_cart_view,
    search_product_list,
    search_redirect,
    product_star_toggle_view,
    customer_cart_product_remove,
    order_create_view,
    create_order_product,
    order_product_complete,
    customer_order_list_view,
    multiple_product_order_create_view,
    customer_profile_view, customer_profile_update_view,
)

cart_urlpatterns = [
    path('add-remove/', add_product_to_cart_or_remove, name='cart_add_remove'),
    path('product/remove/', customer_cart_product_remove, name='cart_product_remove'),
    path('my/', customer_cart_view, name='customer_cart'),
    path('my/order-all/', multiple_product_order_create_view, name='order_all_cart_product'),
]

search_urlpatterns = [
    path('redirect/', search_redirect, name='search_redirect'),
    path('<str:query>/', search_product_list, name='search_product'),
]

category_urlpatterns = [
    path('<int:pk>/order-process/', order_create_view, name='order_process'),
    path('<int:pk>/', product_detail_view, name='product_detail'),
    path('', category_product_list_view, name='category_products_list'),
]

app_name = 'shop'
urlpatterns = [
    path('', home_page_view, name='home'),
    path('my-profile', customer_profile_view, name='customer_profile'),
    path('account/<int:pk>/update/', customer_profile_update_view, name='customer_update'),

    path('cart/', include(cart_urlpatterns)),
    path('search-product/', include(search_urlpatterns)),
    path('rate-product-star/', product_star_toggle_view, name='product_star_toggle'),
    path('category-<slug:category>/', include(category_urlpatterns)),
    path('product-<int:pk>/order-<uuid>/confirm/', create_order_product, name='order_product_confirm'),
    path('order/<uuid>/complete/', order_product_complete, name='order_product_complete'),
    path('my-orders/', customer_order_list_view, name='customer_order_list'),

    # path('all-cart-products/order-<uuid>/confirm/', create_order_product_plural, name='order_product_plural_confirm'),


]

