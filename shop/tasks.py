from datetime import timedelta
from celery import shared_task
from django.utils import timezone

from shop.models import Order


@shared_task
def delete_order_if_no_related_order_product():
    orders = Order.objects.all()
    now = timezone.now()

    for order in orders:
        if now - timedelta(days=1) >= order.date_ordered:
            if not order.orderproduct_set:
                order.delete()
