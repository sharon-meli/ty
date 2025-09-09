from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.name

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField()
    sold_at = models.DateTimeField(auto_now_add=True)
    def total(self):
        return self.quantity * self.product.price
    def profit(self):
        return self.quantity * (self.product.price - self.product.cost_price)
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
