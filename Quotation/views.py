from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse
from django.contrib import messages
from .models import *

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
    total_quotations = Quotation.objects.count()
    if total_quotations == 0:
        total_submitted = total_drafts = 0
    else:
        total_submitted = Quotation.objects.annotate(c=Count('items')).filter(c__gt=0).count()
        total_drafts    = Quotation.objects.annotate(c=Count('items')).filter(c=0).count()
    return render(request, 'dashboard.html', {
        'recent_customers': Customer.objects.all().order_by('-id')[:8],
        'total_quotations': total_quotations,
        'total_submitted':  total_submitted,
        'total_drafts':     total_drafts,
    })

def logout_view(request):
    request.session.flush(); logout(request); return redirect('login')

# ── CUSTOMER ──
def customer_list(request):
    qs = Customer.objects.all().order_by('-id')
    q  = request.GET.get('search')
    if q: qs = qs.filter(Q(name__icontains=q) | Q(mobile__icontains=q))
    return render(request, 'customer_list.html', {'customers': Paginator(qs,12).get_page(request.GET.get('page')), 'query': q})

def customer_add(request):
    if request.method == "POST":
        mob = request.POST.get('mobile')
        if Customer.objects.filter(mobile=mob).exists():
            messages.error(request, "This phone number is already registered!")
            return redirect('customer_list')
        Customer.objects.create(name=request.POST.get('name'), mobile=mob, email=request.POST.get('email'))
        return redirect('customer_list')
    return render(request, 'customer_list.html')

def customer_edit(request, id):
    c = get_object_or_404(Customer, id=id)
    if request.method == "POST":
        c.name, c.mobile, c.email = request.POST.get('name'), request.POST.get('mobile'), request.POST.get('email')
        c.save(); return redirect('customer_list')
    return render(request, 'customer_list.html', {'customer': c})

def customer_delete(request, id):
    get_object_or_404(Customer, id=id).delete(); return redirect('customer_list')

# ── QUOTATION LIST ──
def quotation_list(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    qs = customer.quotations.all().order_by('-id')
    q  = request.GET.get('search')
    if q: qs = qs.filter(Q(quotation_no__icontains=q) | Q(project_type__icontains=q))
    return render(request, 'quotation_list.html', {
        'customer': customer, 'quotations': Paginator(qs,9).get_page(request.GET.get('page')), 'query': q
    })

def quotation_add(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        Quotation.objects.create(customer=customer, project_type=request.POST.get('project_type'))
        return redirect('quotation_list', customer_id=customer.id)
    return render(request, 'quotation_form.html', {'customer': customer})

def quotation_edit(request, id):
    q = get_object_or_404(Quotation, id=id)
    if request.method == "POST":
        q.project_type = request.POST.get('project_type'); q.save()
        return redirect('quotation_list', customer_id=q.customer.id)
    return render(request, 'quotation_form.html', {'q': q, 'customer': q.customer})

def quotation_delete(request, id):
    q = get_object_or_404(Quotation, id=id); cid = q.customer.id; q.delete()
    return redirect('quotation_list', customer_id=cid)

# ── UNITS / SUBUNITS ──
def unit_list(request):    return render(request, 'unit_list.html', {'units': Unit.objects.all()})
def unit_add(request):
    if request.method=="POST": Unit.objects.create(name=request.POST.get('name')); return redirect('unit_list')
    return render(request,'unit_form.html')
def unit_edit(request,id):
    u=get_object_or_404(Unit,id=id)
    if request.method=="POST": u.name=request.POST.get('name'); u.save(); return redirect('unit_list')
    return render(request,'unit_form.html',{'unit':u})
def unit_delete(request,id): Unit.objects.get(id=id).delete(); return redirect('unit_list')

def subunit_list(request): return render(request,'subunit_list.html',{'subunits':SubUnit.objects.all(),'units':Unit.objects.all()})
def subunit_add(request):
    if request.method=="POST": SubUnit.objects.create(unit_id=request.POST.get('unit'),name=request.POST.get('name')); return redirect('subunit_list')
    return render(request,'subunit_form.html',{'units':Unit.objects.all()})
def subunit_edit(request,id):
    s=get_object_or_404(SubUnit,id=id)
    if request.method=="POST": s.unit_id,s.name=request.POST.get('unit'),request.POST.get('name'); s.save(); return redirect('subunit_list')
    return render(request,'subunit_form.html',{'sub':s,'units':Unit.objects.all()})
def subunit_delete(request,id): SubUnit.objects.get(id=id).delete(); return redirect('subunit_list')

# ── ITEMS ──
def item_list(request):
    qs = Item.objects.all().order_by('-id')
    q  = request.GET.get('search')
    if q: qs = qs.filter(Q(name__icontains=q))
    return render(request,'item_list.html',{'items':Paginator(qs,10).get_page(request.GET.get('page')),'query':q,'units':Unit.objects.all(),'subunits':SubUnit.objects.all()})

def item_add(request):
    if request.method=="POST":
        c=request.POST.get('calculation_type')
        Item.objects.create(unit_id=request.POST.get('unit'),sub_unit_id=request.POST.get('sub_unit'),name=request.POST.get('name'),description=request.POST.get('description'),calculation_type=c,rate=request.POST.get('rate') if c=='nos' else None,image=request.FILES.get('image'))
        return redirect('item_list')
    return render(request,'item_form.html',{'units':Unit.objects.all(),'subunits':SubUnit.objects.all()})

def item_edit(request,id):
    i=get_object_or_404(Item,id=id)
    if request.method=="POST":
        c=request.POST.get('calculation_type')
        i.unit_id,i.sub_unit_id,i.name=request.POST.get('unit'),request.POST.get('sub_unit'),request.POST.get('name')
        i.calculation_type,i.description=c,request.POST.get('description')
        i.rate=request.POST.get('rate') if c=='nos' else None
        if request.FILES.get('image'): i.image=request.FILES.get('image')
        i.save(); return redirect('item_list')
    return render(request,'item_form.html',{'item':i,'units':Unit.objects.all(),'subunits':SubUnit.objects.all()})

def item_delete(request,id): Item.objects.get(id=id).delete(); return redirect('item_list')

# ── MATERIALS ──
def _subunits_json(): return list(SubUnit.objects.values('id','name','unit_id'))

def material_list(request):
    return render(request,'material_list.html',{'materials':Material.objects.all(),'units':Unit.objects.all(),'subunits_json':_subunits_json()})

def material_add(request):
    if request.method=="POST":
        Material.objects.create(unit_id=request.POST.get('unit'),sub_unit_id=request.POST.get('sub_unit') or None,name=request.POST.get('name'),description=request.POST.get('description'),rate=request.POST.get('rate'))
        return redirect('material_list')
    return render(request,'material_form.html',{'units':Unit.objects.all(),'subunits_json':_subunits_json()})

def material_edit(request,id):
    m=get_object_or_404(Material,id=id)
    if request.method=="POST":
        m.unit_id=request.POST.get('unit'); m.sub_unit_id=request.POST.get('sub_unit') or None
        m.name=request.POST.get('name'); m.description=request.POST.get('description'); m.rate=request.POST.get('rate')
        m.save(); return redirect('material_list')
    return render(request,'material_form.html',{'material':m,'units':Unit.objects.all(),'subunits_json':_subunits_json()})

def material_delete(request,id): Material.objects.get(id=id).delete(); return redirect('material_list')


# ── QUOTATION DETAIL ──
def _build_unit_data(quotation_items):
    """Build per-unit totals dict from a queryset of QuotationItems."""
    unit_data = {}
    for q_item in quotation_items:
        u = q_item.item.unit
        if u not in unit_data:
            unit_data[u] = {'mrp_total': 0.0, 'final_total': 0.0, 'discount_display': ''}
        unit_data[u]['mrp_total']   += float(q_item.mrp_total)
        unit_data[u]['final_total'] += float(q_item.final_total)
    for u, t in unit_data.items():
        base = t['final_total']
        val  = float(u.discount_value)
        disc = 0.0
        if val > 0:
            if u.discount_type == 'percentage':
                disc = (base * val) / 100.0
                t['discount_display'] = f"{val}% Off (-₹{disc:,.2f})"
            else:
                disc = val
                t['discount_display'] = f"₹{val} Off"
        t['unit_grand_total'] = max(0.0, base - disc)
    return unit_data


def quotation_detail(request, id):
    quotation      = get_object_or_404(Quotation, id=id)
    units          = Unit.objects.all()
    materials_list = Material.objects.all()

    all_items = quotation.items.all().select_related(
        'item__unit', 'item__sub_unit', 'material'
    ).order_by('item__unit__id', 'item__sub_unit__id', 'id')

    unit_data       = _build_unit_data(all_items)
    grand_mrp_total = sum(t['mrp_total']       for t in unit_data.values())
    grand_net_total = sum(t['unit_grand_total'] for t in unit_data.values())

    if request.method == "POST":
        edit_id     = request.POST.get('edit_id')
        item_id     = request.POST.get('item')
        material_id = request.POST.get('material')
        calc_type   = request.POST.get('calc_type')
        item_count  = int(request.POST.get('item_count', 1) or 1)
        disc_type   = request.POST.get('discount_type', 'percentage')
        disc_val    = float(request.POST.get('discount_value', 0) or 0)
        l  = float(request.POST.get('l_val',  0) or 0)
        d  = float(request.POST.get('d_val',  0) or 0)
        h  = float(request.POST.get('h_val',  0) or 0)
        qv = float(request.POST.get('qty_val', 0) or 0)

        if calc_type == 'nos':
            item_obj     = get_object_or_404(Item, id=item_id)
            current_rate = float(item_obj.rate or 0)
            mat_obj      = None
        else:
            mat_obj      = get_object_or_404(Material, id=material_id)
            current_rate = float(mat_obj.rate)

        base_qty   = (l * max(d, h)) / 929 if calc_type == 'sqft' else (1 if calc_type == 'nos' else qv)
        final_qty  = base_qty * item_count

        if edit_id:
            qi = get_object_or_404(QuotationItem, id=edit_id)
            qi.item_id        = item_id
            qi.material       = mat_obj
            qi.l_val, qi.d_val, qi.h_val, qi.qty_val = l, d, h, qv
            qi.quantity       = final_qty
            qi.item_count     = item_count
            qi.rate           = current_rate
            qi.discount_type  = disc_type
            qi.discount_value = disc_val
            qi.save()
        else:
            QuotationItem.objects.create(
                quotation=quotation, item_id=item_id, material=mat_obj,
                l_val=l, d_val=d, h_val=h, qty_val=qv,
                quantity=final_qty, item_count=item_count,
                rate=current_rate, discount_type='percentage', discount_value=0
            )
        return redirect('quotation_detail', id=id)

    return render(request, 'quotation_detail.html', {
        'quotation':       quotation,
        'units':           units,
        'materials_list':  materials_list,
        'all_items':       all_items,
        'unit_data':       unit_data,
        'grand_mrp_total': grand_mrp_total,
        'grand_net_total': grand_net_total,
    })


def update_unit_discount(request, quotation_id, unit_id):
    if request.method == "POST":
        u = get_object_or_404(Unit, id=unit_id)
        u.discount_type  = request.POST.get('unit_discount_type', 'percentage')
        u.discount_value = float(request.POST.get('unit_discount_value', 0) or 0)
        u.save()
        messages.success(request, f"Discount updated for {u.name}!")
    return redirect('quotation_detail', id=quotation_id)


def delete_quotation_item(request, item_id):
    qi = get_object_or_404(QuotationItem, id=item_id)
    qid = qi.quotation.id; qi.delete()
    return redirect('quotation_detail', id=qid)


def load_subunits(request):
    subs = SubUnit.objects.filter(unit_id=request.GET.get('unit')).order_by('name')
    return HttpResponse('<option value="">-- Select Sub Unit --</option>' +
        ''.join(f'<option value="{s.id}">{s.name}</option>' for s in subs))


def load_items(request):
    items = Item.objects.filter(sub_unit_id=request.GET.get('subunit')).order_by('name')
    return HttpResponse('<option value="">-- Select Item --</option>' +
        ''.join(f'<option value="{i.id}" data-type="{i.calculation_type}" data-item-rate="{i.rate or 0}">{i.name}</option>'
                for i in items))


def quotation_pdf(request, id):
    quotation = get_object_or_404(Quotation, id=id)

    # Read column visibility flags from query string
    # Sent by the detail page via ?hide_rate=1&hide_mrp=1&hide_disc=1
    hide_rate = request.GET.get('hide_rate') == '1'
    hide_mrp  = request.GET.get('hide_mrp')  == '1'
    hide_disc = request.GET.get('hide_disc') == '1'

    quotation_items = quotation.items.all().select_related(
        'item__unit', 'item__sub_unit', 'material'
    ).order_by('item__unit__id', 'item__sub_unit__id', 'id')

    unit_data = _build_unit_data(quotation_items)
    # Also attach items list per unit for the PDF template loop
    for q_item in quotation_items:
        u = q_item.item.unit
        if 'items' not in unit_data[u]:
            unit_data[u]['items'] = []
        unit_data[u]['items'].append(q_item)

    grand_mrp_total = sum(t['mrp_total']       for t in unit_data.values())
    grand_net_total = sum(t['unit_grand_total'] for t in unit_data.values())

    # Pass pre-built CSS class strings — no logic needed inside template attributes
    H = 'col-hidden'  # the hide class
    return render(request, 'quotation_pdf.html', {
        'quotation':       quotation,
        'unit_data':       unit_data,
        'grand_mrp_total': grand_mrp_total,
        'grand_net_total': grand_net_total,
        'hide_rate':       hide_rate,
        'hide_mrp':        hide_mrp,
        'hide_disc':       hide_disc,
        # CSS class strings — empty string = visible, 'col-hidden' = hidden
        'cls_rate':        H if hide_rate else '',
        'cls_mrp':         H if hide_mrp  else '',
        'cls_disc':        H if hide_disc else '',
    })