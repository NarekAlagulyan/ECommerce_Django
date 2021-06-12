from django.contrib import admin
from django.utils.safestring import mark_safe
from django.conf import settings

from .models import (
    Customer,
    Category,
    Product,
    Cart,
    Review,
    Order,
    OrderProduct,
    ExtraImage,
    NewProductProxy,
    RateOfProduct,
    CartProduct,
    LastProductVisited
)


# Register your models here.

host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'http://127.0.0.1:8000'


class ExtraImageInline(admin.TabularInline):
    model = ExtraImage


class ProductRateInline(admin.StackedInline):
    model = RateOfProduct


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'price',
        'get_img_html_tag',
        'add_date',
        'slug'
    )
    fields = (
        ('category', 'name', 'price'),
        ('description', 'image', 'slug'),
        ('get_img_html_tag',)
    )
    readonly_fields = (
        'slug', 'get_img_html_tag',
    )

    inlines = (ExtraImageInline, ProductRateInline)

    def get_img_html_tag(self, obj, width=300):
        tag = f'<img src="{obj.get_image_url}" alt="product-image" width={width} class="rounded">'
        return mark_safe(tag)
    get_img_html_tag.allow_tags = True


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'get_img_html_tag',
        'slug',
    )
    fields = (
        ('name', 'image',),
        ('slug', 'get_img_html_tag'),
    )
    readonly_fields = (
        'slug',
        'get_img_html_tag',
    )

    def get_img_html_tag(self, obj, width=300):
        tag = f'<img src="{obj.get_image_url}" alt="product-image" width={width} class="rounded">'
        return mark_safe(tag)
    get_img_html_tag.allow_tags = True


class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'get_full_name',
        'email',
        'get_location_address'
    )
    fields = (
        ('username', 'email',),
        ('first_name', 'last_name',),
        ('country', 'city', 'address', 'zip_code',),
        ('is_staff',),
        ('is_active',),
        ('can_send_notification',),
    )

    @admin.display(description='Location address')
    def get_location_address(self, obj):
        location = f'{obj.country} {obj.city} {obj.address} {obj.zip_code}'
        return location


class CartAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'get_cart_products_quantity'
    )
    fields = (
        'owner',
        ('products', 'get_cart_products_urls')

    )
    readonly_fields = ('get_cart_products_urls',)

    @admin.display(description='products quantity')
    def get_cart_products_quantity(self, obj):
        return obj.products.count()

    @admin.display(description='product links')
    def get_cart_products_urls(self, obj):
        a_tags = ''
        for product in obj.products.all():
            a_tags += f'<a href="{product.get_absolute_url}" class="link">{host}{product.get_absolute_url}</a><br>'
        return mark_safe(f'<div>{a_tags}</div>') if a_tags else 'No related products with the cart to show link'

    get_cart_products_urls.allow_tags = True


class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'author',
    )
    fields = (
        'author',
        ('product', 'get_product_url'),
        'content'
    )
    readonly_fields = ('get_product_url',)

    @admin.display(description='product link')
    def get_product_url(self, obj):
        a_tag = f'<a href="{obj.get_product_absolute_url}" class="link">{host}{obj.get_product_absolute_url}</a>'
        return mark_safe(f'{a_tag}')
    get_product_url.allow_tags = True


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Order)
admin.site.register(OrderProduct)
admin.site.register(CartProduct)
admin.site.register(LastProductVisited)
