from django.db import models
from django.db.models.aggregates import Avg, Sum
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError

from datetime import timedelta
from uuid import uuid4

from django_countries.fields import CountryField

# Create your models here.

CUSTOMER_IMAGE_STORAGE = 'customer-images'
CATEGORY_IMAGE_STORAGE = 'category-images'
PRODUCT_IMAGE_STORAGE = 'product-images'


class Customer(AbstractUser):
    country = CountryField(blank_label='Select country', verbose_name='Country')
    city = models.CharField(max_length=255, verbose_name='City')
    address = models.CharField(max_length=255, verbose_name='Address')
    zip_code = models.CharField(max_length=255, verbose_name='Zip Code')
    image = models.ImageField(upload_to=CUSTOMER_IMAGE_STORAGE, default=r'customer-images/def.jpg')
    can_send_notification = models.BooleanField(default=True)

    class Meta(AbstractUser.Meta):
        verbose_name_plural = 'Customers'
        verbose_name = 'Customer'


class Category(models.Model):
    name = models.CharField(max_length=25, unique=True, db_index=True, verbose_name='Category name')
    image = models.ImageField(upload_to=CATEGORY_IMAGE_STORAGE)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'
        verbose_name = 'Category'
        ordering = ['-name']

    def __str__(self):
        return self.name

    def set_slug(self):
        self.slug = self.name

    def get_absolute_url(self):
        return reverse('shop:category_products_list', kwargs={'category': self.slug})


class Product(models.Model):
    class Meta:
        verbose_name_plural = 'Products'
        verbose_name = 'Product'
        ordering = ('-add_date',)

    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Product category')
    name = models.CharField(max_length=50, verbose_name='Product name')
    description = models.TextField(verbose_name='About this product')
    image = models.ImageField(upload_to=PRODUCT_IMAGE_STORAGE)
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Price')
    add_date = models.DateTimeField(auto_now_add=True, db_index=True)

    def clean(self):
        super().clean()
        errors = []
        if self.description[0].islower():
            errors.append(
                ValidationError('Description cannot starts with lower case.', code='invalid', )
            )
        if len(self.description) < 20:
            errors.append(
                ValidationError('Description is to short, length of the character should be greater than 20.',
                                code='invalid')
            )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.name} || {self.price}$'

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'category': self.category.slug, 'pk': self.pk})

    @property
    def get_image_url(self):
        return self.image.url

    def get_usd_price(self):
        return f'${self.price}'

    def get_avg_star(self):
        data = self.rateofproduct_set.aggregate(avg_star=Avg('stars'))
        avg_star = int(round(data['avg_star'])) if data['avg_star'] else None
        print(avg_star)
        return avg_star


class LastProductVisited(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    add_date = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ('-add_date',)

    def __str__(self):
        return self.product.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        last_visited_products = self.customer.lastproductvisited_set
        if last_visited_products.count() > 12:
            last_visited_products.last().delete()


class NewProductManager(models.Manager):
    def get_queryset(self):
        now = timezone.now()
        return super().get_queryset().filter(add_date__gte=now - timedelta(days=7))[:9]


class NewProductProxy(Product):
    objects = NewProductManager()

    class Meta:
        proxy = True
        ordering = ('-add_date',)
        verbose_name_plural = 'New products'
        verbose_name = 'New product'

    def __str__(self):
        return super().__str__() + ' || NEW'


class Cart(models.Model):
    owner = models.OneToOneField(Customer, on_delete=models.CASCADE, verbose_name='Cart owner')
    products = models.ManyToManyField('CartProduct', related_name='cart_products', verbose_name='Products')

    def __str__(self):
        return f"{self.owner.username}'s cart"

    def total_price(self):
        return self.products.aggregate(sum_price=Sum('total_price'))['sum_price']

    def get_absolute_url(self):
        pass


class CartProduct(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=(MinValueValidator(1),))
    total_price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        verbose_name='Total price',
        default=0
    )

    def __str__(self):
        return self.product.__str__()

    def save(self, *args, **kwargs):
        self.total_price = self.get_total_price()
        super().save(*args, **kwargs)

    def get_total_price(self):
        return self.quantity * self.product.price


class RateOfProduct(models.Model):
    PRODUCT_RATING = (
        (1, 'Bad'),
        (2, 'Not bad'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stars = models.PositiveSmallIntegerField(choices=PRODUCT_RATING, null=True, blank=True)


class Review(models.Model):
    class Meta:
        verbose_name_plural = 'Reviews'
        verbose_name = 'Review'

    author = models.OneToOneField(Customer, on_delete=models.SET('Customer Deleted'), verbose_name='Review author')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    content = models.TextField(verbose_name='Review')

    def __str__(self):
        return f'Review to "{self.product.name}" by "{self.author.username}"'


class Order(models.Model):
    class Meta:
        verbose_name_plural = 'Orders'
        verbose_name = 'Order'

    customer = models.ForeignKey(Customer, on_delete=models.SET('Customer Deleted'), verbose_name='Order customer')
    country = CountryField(blank_label='Select country', verbose_name='Country')
    city = models.CharField(max_length=255, verbose_name='City')
    address = models.CharField(max_length=255, verbose_name='Address')
    zip_code = models.CharField(max_length=255, verbose_name='Zip Code')
    date_ordered = models.DateTimeField(auto_now_add=True, verbose_name='Date ordered')
    complete = models.BooleanField(default=False, verbose_name='Order complete')
    transaction_id = models.UUIDField(default=uuid4, unique=True, editable=False)


class OrderProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(1000)], )


class ExtraImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=PRODUCT_IMAGE_STORAGE)

    def get_image_url(self):
        return self.image.url


@receiver(post_save, sender=Customer)
def create_customer_cart(sender, **kwargs):
    customer = kwargs['instance']
    if kwargs['created']:
        Cart.objects.create(owner=customer)

