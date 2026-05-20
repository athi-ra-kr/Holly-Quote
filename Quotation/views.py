from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout 
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Q, Count # Added Count here to help us count items!
from django.http import HttpResponse, JsonResponse
from django.contrib import messages 
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
    
    # --- NEW REAL-TIME COUNTS FOR YOUR CARDS ---
    # 1. Count all quotations in the database
    total_quotations = Quotation.objects.count()
    
    # Check if there are any quotations at all first to prevent ghost counts!
    if total_quotations == 0:
        total_submitted = 0
        total_drafts = 0
    else:
        # 2. Count quotations that have 1 or more items added to them (Submitted)
        total_submitted = Quotation.objects.annotate(items_count=Count('items')).filter(items_count__gt=0).count()
        
        # 3. Count quotations that have exactly 0 items added to them (Drafts)
        total_drafts = Quotation.objects.annotate(items_count=Count('items')).filter(items_count=0).count()
    
    # ✨ GIRL, LOOK AT YOUR VS CODE TERMINAL FOR THESE PRINTS! ✨
    print("================ DEBUG COUNTS ================")
    print(f"Total Quotations in DB: {total_quotations}")
    print(f"Total Submitted in DB: {total_submitted}")
    print(f"Total Drafts in DB: {total_drafts}")
    print("==============================================")
    
    recent_customers = Customer.objects.all().order_by('-id')[:8]
    
    # Pass the real numbers to your template context
    context = {
        'recent_customers': recent_customers,
        'total_quotations': total_quotations,
        'total_submitted': total_submitted,
        'total_drafts': total_drafts,
    }
    
    return render(request, 'dashboard.html', context)

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
        if Customer.objects.filter(mobile=mobile_number).exists():
            messages.error(request, "This phone number is already registered to another customer!")
            return redirect('customer_list')
            
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


# -------- QUOTATION VIEWS --------
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


# -------- STRUCTURAL MODEL CONTROLLERS --------
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
        'items': page_obj, 'query': query, 'units': Unit.objects.all(), 'subunits': SubUnit.objects.all(),
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


# -------- DETAILED QUOTATION MANAGER --------
def quotation_detail(request, id):
    quotation = get_object_or_404(Quotation, id=id)
    units = Unit.objects.all()
    materials_list = Material.objects.all()
    quotation_items = quotation.items.all().order_by('-id')
    
    unit_data = {}
    for q_item in quotation_items:
        main_unit = q_item.item.unit
        if main_unit not in unit_data:
            unit_data[main_unit] = {
                'mrp_total': 0.0,
                'final_total': 0.0,
                'discount_display': ''
            }
        unit_data[main_unit]['mrp_total'] += float(q_item.mrp_total)
        unit_data[main_unit]['final_total'] += float(q_item.final_total)

    for main_unit, totals in unit_data.items():
        base_amt = totals['final_total']
        val = float(main_unit.discount_value)
        unit_discount = 0.0
        
        if val > 0:
            if main_unit.discount_type == 'percentage':
                unit_discount = (base_amt * val) / 100.0
                totals['discount_display'] = f"{val}% Off (-₹{unit_discount:,.2f})"
            elif main_unit.discount_type == 'flat':
                unit_discount = val
                totals['discount_display'] = f"₹{val} Off"
        
        totals['unit_grand_total'] = max(0.0, base_amt - unit_discount)

    grand_mrp_total = sum(t['mrp_total'] for t in unit_data.values())
    grand_net_total = sum(t['unit_grand_total'] for t in unit_data.values())

    paginator = Paginator(quotation_items, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        edit_id = request.POST.get('edit_id')
        item_id = request.POST.get('item')
        material_id = request.POST.get('material')
        calc_type = request.POST.get('calc_type')
        item_count = int(request.POST.get('item_count', 1) or 1)
        
        disc_type = request.POST.get('discount_type', 'percentage')
        disc_val = float(request.POST.get('discount_value', 0) or 0)

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
            qi.discount_type = disc_type
            qi.discount_value = disc_val
            qi.save()
        else:
            QuotationItem.objects.create(
                quotation=quotation, item_id=item_id, material=mat_obj,
                l_val=l, d_val=d, h_val=h, qty_val=qv,
                quantity=final_quantity, item_count=item_count, rate=current_rate,
                discount_type='percentage', discount_value=0
            )
        return redirect('quotation_detail', id=id)

    return render(request, 'quotation_detail.html', {
        'quotation': quotation, 
        'units': units, 
        'materials_list': materials_list, 
        'page_obj': page_obj,
        'unit_data': unit_data, 
        'grand_mrp_total': grand_mrp_total, 
        'grand_net_total': grand_net_total, 
    })

def update_unit_discount(request, quotation_id, unit_id):
    if request.method == "POST":
        main_unit = get_object_or_404(Unit, id=unit_id)
        main_unit.discount_type = request.POST.get('unit_discount_type', 'percentage')
        main_unit.discount_value = float(request.POST.get('unit_discount_value', 0) or 0)
        main_unit.save()
        messages.success(request, f"Discount updated for {main_unit.name}!")
    return redirect('quotation_detail', id=quotation_id)

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


def quotation_pdf(request, id):
    quotation = get_object_or_404(Quotation, id=id)
    quotation_items = quotation.items.all().order_by('item__unit__id', 'item__sub_unit__id')

    unit_data = {}
    for q_item in quotation_items:
        main_unit = q_item.item.unit
        if main_unit not in unit_data:
            unit_data[main_unit] = {'mrp_total': 0.0, 'final_total': 0.0, 'items': []}
        unit_data[main_unit]['mrp_total'] += float(q_item.mrp_total)
        unit_data[main_unit]['final_total'] += float(q_item.final_total)
        unit_data[main_unit]['items'].append(q_item)

    for main_unit, totals in unit_data.items():
        base_amt = totals['final_total']
        val = float(main_unit.discount_value)
        unit_discount = 0.0
        if val > 0:
            if main_unit.discount_type == 'percentage':
                unit_discount = (base_amt * val) / 100.0
            elif main_unit.discount_type == 'flat':
                unit_discount = val
        totals['unit_grand_total'] = max(0.0, base_amt - unit_discount)

    grand_mrp_total = sum(t['mrp_total'] for t in unit_data.values())
    grand_net_total = sum(t['unit_grand_total'] for t in unit_data.values())

    return render(request, 'quotation_pdf.html', {
        'quotation': quotation,
        'unit_data': unit_data,
        'grand_mrp_total': grand_mrp_total,
        'grand_net_total': grand_net_total,
    })