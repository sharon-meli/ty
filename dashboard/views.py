from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import Product, Sale
from .forms import ProductForm, SaleForm, SaleSearchForm
from django.db.models import Sum, F
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.template.loader import render_to_string

# Dashboard
def index(request):
    products = Product.objects.all().order_by('name')
    total_sales = Sale.objects.aggregate(total=Sum(F('quantity') * F('product__price')))['total'] or 0
    recent_sales = Sale.objects.order_by('-sold_at')[:10]
    low_stock = list(products.filter(qty__lte=1).values('name','qty'))
    return render(request,'dashboard/index.html',{'products':products,'total_sales':total_sales,'recent_sales':recent_sales,'low_stock':low_stock})

# Product CRUD
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard:index')
    else:
        form = ProductForm()
    return render(request,'dashboard/add_product.html',{'form':form})

def edit_product(request, pk):
    prod = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=prod)
        if form.is_valid():
            form.save()
            return redirect('dashboard:index')
    else:
        form = ProductForm(instance=prod)
    return render(request,'dashboard/edit_product.html',{'form':form,'product':prod})

def delete_product(request, pk):
    prod = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        prod.delete()
        return redirect('dashboard:index')
    return render(request,'dashboard/confirm_delete.html',{'product':prod})

# Sales CRUD with automatic stock adjustments
def sales_list(request):
    sales = Sale.objects.select_related('product').order_by('-sold_at')
    return render(request,'dashboard/sales_list.html',{'sales':sales})

def add_sale(request):
    search_form = SaleSearchForm(request.GET or None)
    products = Product.objects.all().order_by('name')
    if search_form.is_valid():
        q = search_form.cleaned_data.get('q') or ''
        if q:
            products = products.filter(name__icontains=q)
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            prod = sale.product
            prod.qty = max(prod.qty - sale.quantity, 0)
            prod.save()
            sale.save()
            return redirect('dashboard:sales_list')
    else:
        form = SaleForm()
    return render(request,'dashboard/add_sale.html',{'form':form,'products':products,'search_form':search_form})

def edit_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            new_sale = form.save(commit=False)

            # revert original quantity to original product first
            original_product = sale.product
            original_product.qty = original_product.qty + sale.quantity
            original_product.save()

            # If product changed, remove from new product
            if new_sale.product.id != sale.product.id:
                new_prod = new_sale.product
                if new_sale.quantity > new_prod.qty:
                    form.add_error('quantity','Not enough stock for selected product')
                    # revert original revert to original state: subtract original again
                    original_product.qty = max(original_product.qty - sale.quantity, 0)
                    original_product.save()
                    return render(request,'dashboard/edit_sale.html',{'form':form,'sale':sale})
                new_prod.qty = new_prod.qty - new_sale.quantity
                new_prod.save()
            else:
                # same product (we already added back original qty), now subtract new qty
                prod = new_sale.product
                if new_sale.quantity > prod.qty:
                    form.add_error('quantity','Not enough stock for selected product')
                    # revert original_product back (subtract original)
                    original_product.qty = max(original_product.qty - sale.quantity, 0)
                    original_product.save()
                    return render(request,'dashboard/edit_sale.html',{'form':form,'sale':sale})
                prod.qty = prod.qty - new_sale.quantity
                prod.save()

            new_sale.save()
            return redirect('dashboard:sales_list')
    else:
        form = SaleForm(instance=sale)
    return render(request,'dashboard/edit_sale.html',{'form':form,'sale':sale})

def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        prod = sale.product
        prod.qty = prod.qty + sale.quantity
        prod.save()
        sale.delete()
        return redirect('dashboard:sales_list')
    return render(request,'dashboard/confirm_delete_sale.html',{'sale':sale})

# Reports + PDF
def reports(request, period='daily'):
    qs = Sale.objects.select_related('product')
    if period == 'daily':
        grouped = qs.annotate(period=TruncDay('sold_at')).values('period').annotate(
            total_qty=Sum('quantity'),
            total_sales=Sum(F('quantity') * F('product__price')),
            total_profit=Sum(F('quantity') * (F('product__price') - F('product__cost_price')))
        ).order_by('-period')
    elif period == 'weekly':
        grouped = qs.annotate(period=TruncWeek('sold_at')).values('period').annotate(
            total_qty=Sum('quantity'),
            total_sales=Sum(F('quantity') * F('product__price')),
            total_profit=Sum(F('quantity') * (F('product__price') - F('product__cost_price')))
        ).order_by('-period')
    else:
        grouped = qs.annotate(period=TruncMonth('sold_at')).values('period').annotate(
            total_qty=Sum('quantity'),
            total_sales=Sum(F('quantity') * F('product__price')),
            total_profit=Sum(F('quantity') * (F('product__price') - F('product__cost_price')))
        ).order_by('-period')

    by_product = qs.values('product__name').annotate(
        qty_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('product__price')),
        profit=Sum(F('quantity') * (F('product__price') - F('product__cost_price')))
    ).order_by('-revenue')

    totals = qs.aggregate(
        total_qty=Sum('quantity'),
        total_sales=Sum(F('quantity') * F('product__price')),
        total_profit=Sum(F('quantity') * (F('product__price') - F('product__cost_price')))
    )
    return render(request,'dashboard/reports.html',{'grouped':grouped,'period':period,'totals':totals,'by_product':list(by_product)})

def report_pdf(request, period='daily'):
    qs = Sale.objects.select_related('product')
    by_product = qs.values('product__name').annotate(
        qty_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('product__price')),
        profit=Sum(F('quantity') * (F('product__price') - F('product__cost_price')))
    )
    totals = qs.aggregate(
        total_qty=Sum('quantity'),
        total_sales=Sum(F('quantity') * F('product__price')),
        total_profit=Sum(F('quantity') * (F('product__price') - F('product__cost_price')))
    )
    context = {'grouped': [], 'period': period, 'totals': totals, 'by_product': list(by_product)}
    html_string = render_to_string('dashboard/report_pdf.html', context)
    try:
        from weasyprint import HTML
        pdf = HTML(string=html_string).write_pdf()
        return HttpResponse(pdf, content_type='application/pdf')
    except Exception as e:
        return HttpResponse('PDF generation failed: %s' % e)
