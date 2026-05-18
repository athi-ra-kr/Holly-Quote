from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout 
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Q 
from django.http import HttpResponse, JsonResponse
from django.contrib import messages  # Added this to handle our error alerts!
from .models import *

# VALIDATION
VALID_USERNAME = "Hollyblue123@gmail.com"
VALID_PASSWORD = "Hollyblue"

@never_cache 
def login_view(request):
    if request.session.get('user'): return redirect('dashboard')
    if request.method == "POST":
        u, p = request.POST.get("username"), request.POST.get("password")
        if u == VALID_USERNAME and p == VALID_PASSWORD:
            request.session['user'] = u
            return redirect('dashboard')
        return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

@never_cache
def dashboard(request):
    if not request.session.get('user'): return redirect('login')
    
    # Girl, we are fetching the top 4 most recent customers here!
    recent_customers = Customer.objects.all().order_by('-id')[:8]
    
    # We pass them into our template context dictionary
    return render(request, 'dashboard.html', {'recent_customers': recent_customers})

def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('login')

# -------- CUSTOMER VIEWS --------
def customer_list(request):
    qs = Customer.objects.all().order_by('-id')
    q = request.GET.get('search')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(mobile__icontains=q))
    
    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'customer_list.html', {'customers': page_obj, 'query': q})

def customer_add(request):
    if request.method == "POST":
        mobile_number = request.POST.get('mobile')
        
        # Look here, girl! We check if any customer already has this mobile number
        if Customer.objects.filter(mobile=mobile_number).exists():
            messages.error(request, "This phone number is already registered to another customer!")
            return redirect('customer_list')
            
        # If it doesn't exist, we safely create it!
        Customer.objects.create(
            name=request.POST.get('name'),
            mobile=mobile_number,
            email=request.POST.get('email')
        )
        return redirect('customer_list')
    return render(request, 'customer_list.html')

def customer_edit(request, id):
    c = get_object_or_404(Customer, id=id)
    if request.method == "POST":
        c.name, c.mobile, c.email = request.POST.get('name'), request.POST.get('mobile'), request.POST.get('email')
        c.save()
        return redirect('customer_list')
    return render(request, 'customer_list.html', {'customer': c})

def customer_delete(request, id):
    get_object_or_404(Customer, id=id).delete()
    return redirect('customer_list')


# -------- QUOTATION VIEWS (Scoped to Customer) --------
def quotation_list(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    qs = customer.quotations.all().order_by('-id')
    
    q = request.GET.get('search')
    if q:
        qs = qs.filter(Q(quotation_no__icontains=q) | Q(project_type__icontains=q))
    
    paginator = Paginator(qs, 9) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'quotation_list.html', {
        'customer': customer,
        'quotations': page_obj,
        'query': q
    })

def quotation_add(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        Quotation.objects.create(
            customer=customer,
            project_type=request.POST.get('project_type')
        )
        return redirect('quotation_list', customer_id=customer.id)
    return render(request, 'quotation_form.html', {'customer': customer})

def quotation_edit(request, id):
    q = get_object_or_404(Quotation, id=id)
    if request.method == "POST":
        q.project_type = request.POST.get('project_type')
        q.save()
        return redirect('quotation_list', customer_id=q.customer.id)
    return render(request, 'quotation_form.html', {'q': q, 'customer': q.customer})

def quotation_delete(request, id):
    q = get_object_or_404(Quotation, id=id)
    customer_id = q.customer.id
    q.delete()
    return redirect('quotation_list', customer_id=customer_id)


# -------- EXISTING CRUD VIEWS --------
def unit_list(request): return render(request, 'unit_list.html', {'units': Unit.objects.all()})
def unit_add(request):
    if request.method == "POST":
        Unit.objects.create(name=request.POST.get('name'))
        return redirect('unit_list')
    return render(request, 'unit_form.html')

def unit_edit(request, id):
    u = get_object_or_404(Unit, id=id)
    if request.method == "POST":
        u.name = request.POST.get('name')
        u.save()
        return redirect('unit_list')
    return render(request, 'unit_form.html', {'unit': u})

def unit_delete(request, id):
    Unit.objects.get(id=id).delete()
    return redirect('unit_list')

def subunit_list(request): return render(request, 'subunit_list.html', {'subunits': SubUnit.objects.all(), 'units': Unit.objects.all()})

def subunit_add(request):
    if request.method == "POST":
        SubUnit.objects.create(unit_id=request.POST.get('unit'), name=request.POST.get('name'))
        return redirect('subunit_list')
    return render(request, 'subunit_form.html', {'units': Unit.objects.all()})

def subunit_edit(request, id):
    s = get_object_or_404(SubUnit, id=id)
    if request.method == "POST":
        s.unit_id, s.name = request.POST.get('unit'), request.POST.get('name')
        s.save()
        return redirect('subunit_list')
    return render(request, 'subunit_form.html', {'sub': s, 'units': Unit.objects.all()})

def subunit_delete(request, id):
    SubUnit.objects.get(id=id).delete()
    return redirect('subunit_list')

def item_list(request):
    items_qs = Item.objects.all().order_by('-id')
    query = request.GET.get('search')
    if query:
        items_qs = items_qs.filter(Q(name__icontains=query))
    paginator = Paginator(items_qs, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'item_list.html', {
        'items': page_obj,
        'query': query,
        'units': Unit.objects.all(),
        'subunits': SubUnit.objects.all(),
    })

def item_add(request):
    if request.method == "POST":
        c = request.POST.get('calculation_type')
        Item.objects.create(
            unit_id=request.POST.get('unit'), sub_unit_id=request.POST.get('sub_unit'),
            name=request.POST.get('name'), description=request.POST.get('description'),
            calculation_type=c, rate=request.POST.get('rate') if c == 'nos' else None,
            image=request.FILES.get('image')
        )
        return redirect('item_list')
    return render(request, 'item_form.html', {'units': Unit.objects.all(), 'subunits': SubUnit.objects.all()})

def item_edit(request, id):
    i = get_object_or_404(Item, id=id)
    if request.method == "POST":
        c = request.POST.get('calculation_type')
        i.unit_id, i.sub_unit_id, i.name = request.POST.get('unit'), request.POST.get('sub_unit'), request.POST.get('name')
        i.calculation_type, i.description = c, request.POST.get('description')
        i.rate = request.POST.get('rate') if c == 'nos' else None
        if request.FILES.get('image'): i.image = request.FILES.get('image')
        i.save()
        return redirect('item_list')
    return render(request, 'item_form.html', {'item': i, 'units': Unit.objects.all(), 'subunits': SubUnit.objects.all()})

def item_delete(request, id):
    Item.objects.get(id=id).delete()
    return redirect('item_list')

def material_list(request): return render(request, 'material_list.html', {'materials': Material.objects.all(), 'units': Unit.objects.all()})

def material_add(request):
    if request.method == "POST":
        Material.objects.create(unit_id=request.POST.get('unit'), name=request.POST.get('name'), rate=request.POST.get('rate'))
        return redirect('material_list')
    return render(request, 'material_form.html', {'units': Unit.objects.all()})

def material_edit(request, id):
    m = get_object_or_404(Material, id=id)
    if request.method == "POST":
        m.unit_id, m.name, m.rate = request.POST.get('unit'), request.POST.get('name'), request.POST.get('rate')
        m.save()
        return redirect('material_list')
    return render(request, 'material_form.html', {'material': m, 'units': Unit.objects.all()})

def material_delete(request, id):
    Material.objects.get(id=id).delete()
    return redirect('material_list')

def quotation_detail(request, id):
    quotation = get_object_or_404(Quotation, id=id)
    units = Unit.objects.all()
    materials_list = Material.objects.all()
    quotation_items = quotation.items.all().order_by('-id')
    paginator = Paginator(quotation_items, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        edit_id = request.POST.get('edit_id')
        item_id = request.POST.get('item')
        material_id = request.POST.get('material')
        calc_type = request.POST.get('calc_type')
        item_count = int(request.POST.get('item_count', 1) or 1)
        mat_obj = get_object_or_404(Material, id=material_id)
        current_rate = float(mat_obj.rate)

        l = float(request.POST.get('l_val', 0) or 0)
        d = float(request.POST.get('d_val', 0) or 0)
        h = float(request.POST.get('h_val', 0) or 0)
        qv = float(request.POST.get('qty_val', 0) or 0)

        if calc_type == 'sqft':
            base_quantity = (l * max(d, h)) / 929
        else:
            base_quantity = qv

        final_quantity = base_quantity * item_count

        if edit_id:
            qi = get_object_or_404(QuotationItem, id=edit_id)
            qi.item_id = item_id
            qi.material = mat_obj
            qi.l_val, qi.d_val, qi.h_val, qi.qty_val = l, d, h, qv
            qi.quantity = final_quantity
            qi.item_count = item_count
            qi.rate = current_rate
            qi.save()
        else:
            QuotationItem.objects.create(
                quotation=quotation, item_id=item_id, material=mat_obj,
                l_val=l, d_val=d, h_val=h, qty_val=qv,
                quantity=final_quantity, item_count=item_count, rate=current_rate
            )
        return redirect('quotation_detail', id=id)

    return render(request, 'quotation_detail.html', {
        'quotation': quotation, 'units': units, 'materials_list': materials_list, 'page_obj': page_obj
    })

def delete_quotation_item(request, item_id):
    qi = get_object_or_404(QuotationItem, id=item_id)
    qid = qi.quotation.id
    qi.delete()
    return redirect('quotation_detail', id=qid)

def load_subunits(request):
    subs = SubUnit.objects.filter(unit_id=request.GET.get('unit')).order_by('name')
    opts = '<option value="">-- Select Sub Unit --</option>' + ''.join([f'<option value="{s.id}">{s.name}</option>' for s in subs])
    return HttpResponse(opts)

def load_items(request):
    items = Item.objects.filter(sub_unit_id=request.GET.get('subunit')).order_by('name')
    opts = '<option value="">-- Select Item --</option>' + ''.join([f'<option value="{i.id}" data-type="{i.calculation_type}">{i.name}</option>' for i in items])
    return HttpResponse(opts)