from django.contrib import admin
from .models import Product, Sale

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','price','qty','cost_price')
    list_editable = ('qty',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product','quantity','sold_at')
    date_hierarchy = 'sold_at'
