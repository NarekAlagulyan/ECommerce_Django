from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import View
from django.views.generic.edit import UpdateView, BaseUpdateView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, FormView
from django.contrib.auth.views import login_required
from django.http import Http404
from django.db.models import Q
from django.forms.models import model_to_dict
from django.forms import modelformset_factory

from abc import ABC

from .models import (
    Category,
    Product,
    Cart,
    Customer,
    CartProduct,
    NewProductProxy,
    RateOfProduct,
    Review,
    Order,
    OrderProduct,
)
from .forms import (
    CartProductQuantityForm,
    ProductReviewForm,
    OrderForm,
    CreateOrderProductForm, CustomerUpdateForm
)
from django.http import Http404


# Create your views here.


class HomePageView(View):
    template_name = 'shop/home.html'

    def get(self, request, *args, **kwargs):
        context = {}
        categories = Category.objects.all()[:9]
        products = Product.objects.all()[:9]
        new_products = NewProductProxy.objects.all()
        if request.user.is_authenticated:
            customer = Customer.objects.get(pk=request.user.pk)
            context['last_visited_products'] = customer.lastproductvisited_set.all()
            print(context['last_visited_products'])
        print(categories)
        context.update(
            {
                'categories': categories,
                'products': products,
                'new_products': new_products,
            }
        )
        return render(request, self.template_name, context)


home_page_view = HomePageView.as_view()


class CustomerProfileView(LoginRequiredMixin, View):
    template_name = 'account/customer.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


customer_profile_view = CustomerProfileView.as_view()


class CustomerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    template_name = 'account/customer_update.html'
    form_class = CustomerUpdateForm

    def get_success_url(self):
        return reverse('shop:customer_profile')


customer_profile_update_view = CustomerProfileUpdateView.as_view()


class AllOrCategoryProductListView(ListView):
    """
    Implementation of the of the ListView
    Hear we have 3 cases when we are passing URL parameter.
    1) If we have a category which we can filter and retrieve queryset of the list of objects of given category
    2) If we have as a url parameter  'all-products' and we getting all products in our DB
    3) If we don't have category which was passed and we don't have passed 'all-products'
    than we returning Http404
    """
    model = Product
    context_object_name = 'products'
    template_name = 'shop/product_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.kwargs['category'] != 'all-products' and self.kwargs['category'] != 'new-products':
            queryset = queryset.filter(category__slug=self.kwargs['category'])
            if not queryset:
                raise Http404
        else:
            if self.kwargs['category'] == 'new-products':
                queryset = NewProductProxy.objects.all()
        return queryset


category_product_list_view = AllOrCategoryProductListView.as_view()


@require_POST
def product_star_toggle_view(request):
    if request.method == 'POST':
        product = Product.objects.get(pk=request.POST['product_id'])
        star = int(request.POST['star'])
        data = {}
        try:
            rate_of_product = RateOfProduct.objects.get(
                customer=request.user,
                product=product,
            )
            rated = star != rate_of_product.stars
            rate_of_product.stars = star if rated else None
            rate_of_product.save()
            data['rated'] = rated

        except RateOfProduct.DoesNotExist:
            rate_of_product = RateOfProduct.objects.create(
                customer=request.user,
                product=product,
                stars=star
            )
            data['rated'] = True
        print('rated product', rate_of_product)
        print('stars of product', rate_of_product.stars)
        print(data['rated'])
        data['star'] = star
        return JsonResponse(data, safe=False)


def product_detail_view(request, category, pk):
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            print('form is invalid')

    product = get_object_or_404(Product, pk=pk)
    context = {}

    try:
        cart_product = CartProduct.objects.get(product=product)
        context['cart_product'] = cart_product
    except CartProduct.DoesNotExist:
        pass

    context['product'] = product
    context['is_new'] = product in NewProductProxy.objects.all()
    print('product: ', product)
    context['reviews'] = Review.objects.filter(product=product)

    if request.user.is_authenticated:
        context['review_form'] = ProductReviewForm(initial={'author': request.user, 'product': product})
    return render(request, 'shop/product_detail.html', context)


@login_required
def customer_cart_view(request):
    if request.method == 'POST':
        cart_product_pk = request.POST['cart_product_pk']
        cart_product = get_object_or_404(CartProduct, pk=cart_product_pk)
        form = CartProductQuantityForm(request.POST, instance=cart_product)

        if form.is_valid():
            form.save()
            return HttpResponse('<script>history.back();</script>')

    cart = Cart.objects.get(owner=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'shop/customer_cart.html', context)


@require_POST
def customer_cart_product_remove(request):
    if request.method == 'POST':
        product_pk = request.POST['cart_product_pk']
        cart_product = get_object_or_404(CartProduct, pk=product_pk)
        print(product_pk)
        print(cart_product)
        cart_product.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class SearchProductListView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'shop/searched_products.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')
        q = Q(name__icontains=query) | Q(category__name__icontains=query)
        return queryset.filter(q)


search_product_list = SearchProductListView.as_view()


@require_POST
def add_product_to_cart_or_remove(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            product = Product.objects.get(pk=request.POST['product_id'])
            cart = Cart.objects.get(owner=request.user)
            cart_product_tuple = CartProduct.objects.get_or_create(product=product)
            cart_product = cart_product_tuple[0]

            if cart_product in cart.products.all():
                cart_product.delete()
            else:
                cart_product.total_price = cart_product.get_total_price()
                cart_product.save()
                print('cart_product quantity: ', cart_product.quantity)
                cart.products.add(cart_product)
            data = {
                'product_in_cart': cart_product in cart.products.all(),
                'cart_products_count': cart.products.count(),
            }
            return JsonResponse(data, safe=False)


class AbstractProductOrderCreateView(ABC, LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'shop/order_create.html'

    def setup(self, request, *args, **kwargs):
        self.customer_pk = request.user.pk
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        customer = Customer.objects.get(pk=self.request.user.pk)
        return {
            'customer': customer,
            'country': customer.country,
            'city': customer.city,
            'address': customer.address,
            'zip_code': customer.zip_code,
        }


class SingleProductOrderCreateView(AbstractProductOrderCreateView):
    def setup(self, request, *args, **kwargs):
        request.session['ordering_product_pk'] = kwargs['pk']
        return super().setup(request, *args, **kwargs)

    def get_success_url(self):
        order = self.object
        order_uuid = order.transaction_id
        return reverse('shop:order_product_confirm', kwargs={'uuid': order_uuid, 'pk': self.kwargs['pk']})


order_create_view = SingleProductOrderCreateView.as_view()


class MultipleProductOrderCreateView(AbstractProductOrderCreateView):
    def get_success_url(self):
        order = self.object
        order_uuid = order.transaction_id
        return reverse('shop:order_product_plural_confirm', kwargs={'uuid': order_uuid})


multiple_product_order_create_view = MultipleProductOrderCreateView.as_view()


class CreateOrderProduct(LoginRequiredMixin, CreateView):
    model = OrderProduct
    form_class = CreateOrderProductForm
    template_name = 'shop/single_product_order_confirm.html'

    def setup(self, request, *args, **kwargs):
        self.product_pk = request.session['ordering_product_pk']
        self.order_transaction_id = kwargs['uuid']
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        product = get_object_or_404(Product, pk=self.product_pk)
        order = Order.objects.get(transaction_id=self.order_transaction_id)
        return {
            'product': product,
            'order': order,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = Product.objects.get(pk=self.product_pk)
        context['product'] = product
        return context

    def get_success_url(self):
        order_product = self.object
        return reverse('shop:order_product_complete', kwargs={'uuid': order_product.order.transaction_id})


create_order_product = CreateOrderProduct.as_view()


# @login_required
# def create_order_product_plural(request, uuid):
#     customer_pk = request.user.pk
#     order_transaction_id = uuid
#
#     if request.method == 'POST':
#         print('hello world')
#     else:
#         order = Order.objects.get(transaction_id=order_transaction_id)
#         cart_products = Cart.objects.get(owner__pk=customer_pk).products.all()
#         create_order_product_formset = modelformset_factory(
#             model=OrderProduct,
#             fields=('product', 'order', 'quantity'),
#
#         )
#
#         formset = create_order_product_formset(data={'product': 1, 'order': 1})
#         context = {
#             'formset': formset
#         }
#         print('hello world')
#         return render(request, 'shop/multiple_order_product_confirm.html', context)


def order_product_complete(request, uuid):
    return render(request, 'shop/order_complete.html')


class CustomerOrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'shop/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(customer=self.request.user)


customer_order_list_view = CustomerOrderListView.as_view()