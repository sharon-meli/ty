from django.urls import path
from . import views
app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='index'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('product/<int:pk>/stock/', views.edit_product, name='edit_stock'),
    path('sales/', views.sales_list, name='sales_list'),
    path('sale/add/', views.add_sale, name='add_sale'),
    path('sale/<int:pk>/edit/', views.edit_sale, name='edit_sale'),
    path('sale/<int:pk>/delete/', views.delete_sale, name='delete_sale'),
    path('reports/<str:period>/', views.reports, name='reports'),
    path('reports/<str:period>/pdf/', views.report_pdf, name='report_pdf'),
]
