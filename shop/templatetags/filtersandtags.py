from django import template
from django.utils.safestring import mark_safe


from ..models import Customer, RateOfProduct, CartProduct
from ..forms import CartProductQuantityForm

register = template.Library()


gold_star = '<button class="star-btn border-0 p-0 m-0 bg-white" type="submit" data-star="%s"><i class="fa fa-star text-warning"></i></button>'
simple_star = '<button class="star-btn border-0 p-0 m-0 bg-white" type="submit" data-star="%s"><i class="fa fa-star text-black"></i></button>'


@register.simple_tag
def product_star_pattern(**kwargs):
    """
    This function makes star-rating pattern for each product.
    There are 3 expected keyword arguments
    1) user and product_id
    2) avg_star

    For the first case, if we passing those 2 arguments, that means that we want to retrieve users rated star pattern
    For the second case, only for avg_star, this is for only to show average stars from all rated customers.

    If avg_star not passed, get customer from passed user argument,
    then try to retrieve product which rate our customer, if customer doesn't rate product, than it will be None.

    if rated product exists, check if it have rated stars,
    if don't have, just make fully empty star pattern, otherwise product rate given by customer pattern.

    If product doesn't not exists then make fully empty star pattern.

    But if avg_star is passed, than just make star pattern from average star from all rated customers

    :except: user, product_pk, avg_star
    :param kwargs:
    :return: mark_safe(pattern)
    """
    avg_star = kwargs.get('avg_star')
    pattern = ''
    if not avg_star:
        customer = Customer.objects.get(pk=kwargs['user'].pk)
        try:
            rate_of_product = RateOfProduct.objects.get(customer=customer, product__pk=kwargs['product_pk'])
        except RateOfProduct.DoesNotExist:
            rate_of_product = None
        if rate_of_product:
            if not rate_of_product.stars:
                for data in range(1, 5 + 1):
                    pattern += simple_star % data
            else:
                for data in range(1, rate_of_product.stars + 1):
                    pattern += gold_star % data
                for data in range(rate_of_product.stars + 1, 5 + 1):
                    pattern += simple_star % data
        else:
            for data in range(1, 5 + 1):
                pattern += simple_star % data
        print('customer star pattern')
    else:
        for data in range(1, avg_star + 1):
            pattern += gold_star % data
        for data in range(avg_star + 1, 5 + 1):
            pattern += simple_star % data
        print('avg star pattern')

    return mark_safe(pattern)


@register.filter
def cart_product_quantity_form(cart_product):
    cart_product = CartProduct.objects.get(pk=cart_product.pk)
    form = CartProductQuantityForm(instance=cart_product)
    return form
