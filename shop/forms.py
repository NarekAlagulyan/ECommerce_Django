from django import forms
from django.core.validators import ValidationError

from allauth.account.forms import SignupForm
from django_countries.widgets import CountrySelectWidget
from django_countries import countries
from captcha.fields import CaptchaField

from .models import CartProduct, Product, Review, Order, OrderProduct, Customer


class CustomerSignupForm(SignupForm):
    first_name = forms.CharField(max_length=50, label='First name')
    last_name = forms.CharField(max_length=50, label='Last name')
    country = forms.ChoiceField(widget=CountrySelectWidget, choices=countries, label='Country')
    city = forms.CharField(max_length=255, label='City')
    address = forms.CharField(max_length=255, label='Address')
    zip_code = forms.CharField(max_length=255, label='Zipcode')
    image = forms.ImageField(required=False)
    can_send_notification = forms.BooleanField(required=False)

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.country = self.cleaned_data['country']
        user.city = self.cleaned_data['city']
        user.address = self.cleaned_data['address']
        user.zip_code = self.cleaned_data['zip_code']
        user.image = self.cleaned_data['image']
        user.can_send_notification = self.cleaned_data['can_send_notification']
        user.save()
        return user


class CustomerUpdateForm(forms.ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = Customer
        fields = (
            'username',
            'first_name',
            'last_name',
            'country',
            'city',
            'address',
            'zip_code',
            'image',
            'can_send_notification'
        )


class CartProductQuantityForm(forms.ModelForm):
    class Meta:
        model = CartProduct
        fields = ('quantity',)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise ValidationError(
                'Quantity of the product cannot be less then 0. Given %(quantity)',
                code='invalid',
                params={'quantity': quantity}
            )
        return quantity


class ProductSearchForm(forms.Form):
    def __init__(self):
        super().__init__()
        self.fields['query'].label = ''

    query = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': 'Search'}))


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = '__all__'
        widgets = {'author': forms.HiddenInput(), 'product': forms.HiddenInput()}


class OrderForm(forms.ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = Order
        exclude = ('date_ordered', 'complete', 'transaction_id')
        widgets = {'customer': forms.HiddenInput()}


class CreateOrderProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['min'] = 1

    captcha = CaptchaField()

    class Meta:
        model = OrderProduct
        fields = ('product', 'order', 'quantity')
        widgets = {'product': forms.HiddenInput(), 'order': forms.HiddenInput()}


