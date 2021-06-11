from django.shortcuts import get_object_or_404

from .models import Category, Cart, Product, Category, Customer, LastProductVisited
from .forms import ProductSearchForm


def context_processor_middleware(request):
    context = {}
    categories = Category.objects.all()
    if request.user.is_authenticated:
        cart = Cart.objects.get(owner=request.user)
        cart_products_count = cart.products.count()
        context['cart'] = cart
        context['cart_products_count'] = cart_products_count
    context['categories'] = categories
    context['search_form'] = ProductSearchForm()
    return context


class LastProductVisitedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            if view_func.__name__ == 'product_detail_view':
                product = get_object_or_404(Product, pk=view_kwargs['pk'])
                customer = Customer.objects.get(pk=request.user.pk)
                try:
                    current_product_visited = LastProductVisited.objects.get(customer=customer, product=product)
                except LastProductVisited.DoesNotExist:
                    current_product_visited = LastProductVisited.objects.create(customer=customer, product=product)
                # If last_product_visited already exist but, not in a first position, then
                # we should modify his add_date as a current date and it will automatically becomes as a first in QS.
                # By saving, modifies add_date because 'auto_now=True' in DateTimeField
                if current_product_visited != customer.lastproductvisited_set.first():
                    current_product_visited.save()


