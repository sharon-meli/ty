from django import forms
from .models import Product, Sale

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','cost_price','price','qty']

class SaleSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Search product name')

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product','quantity']

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        quantity = cleaned.get('quantity')
        if product and quantity and quantity > product.qty:
            raise forms.ValidationError('Not enough stock for this product.')
        return cleaned
