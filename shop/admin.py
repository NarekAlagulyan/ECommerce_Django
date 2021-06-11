from django.contrib import admin

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


class ExtraImageInline(admin.TabularInline):
    model = ExtraImage


class ProductRateInline(admin.StackedInline):
    model = RateOfProduct


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'price',
        'add_date',
    )
    fields = (
        ('category', 'name', 'price'),
        ('description', 'image'),
    )

    inlines = (ExtraImageInline, ProductRateInline)


admin.site.register(Customer)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart)
admin.site.register(Review)
admin.site.register(Order)
admin.site.register(OrderProduct)
admin.site.register(CartProduct)
admin.site.register(LastProductVisited)
