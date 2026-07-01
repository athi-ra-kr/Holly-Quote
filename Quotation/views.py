from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from functools import wraps
from datetime import date
from decimal import Decimal
from .models import *

VALID_USERNAME = "Hollyblue123@gmail.com"
VALID_PASSWORD = "Hollyblue"


# ── LOGIN GUARD ──
def login_required_session(view_func):
    @wraps(view_func)
    @never_cache
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('user'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped


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


@login_required_session
def dashboard(request):
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
        'total_drafts':      total_drafts,
    })


def logout_view(request):
    request.session.flush(); logout(request); return redirect('login')


# ── CUSTOMER ──
@login_required_session
def customer_list(request):
    qs = Customer.objects.all().order_by('-id')
    q  = request.GET.get('search')
    if q: qs = qs.filter(Q(name__icontains=q) | Q(mobile__icontains=q))
    return render(request, 'customer_list.html', {'customers': Paginator(qs,12).get_page(request.GET.get('page')), 'query': q})

@login_required_session
def customer_add(request):
    if request.method == "POST":
        mob = request.POST.get('mobile')
        if Customer.objects.filter(mobile=mob).exists():
            messages.error(request, "This phone number is already registered!")
            return redirect('customer_list')
        Customer.objects.create(name=request.POST.get('name'), mobile=mob, email=request.POST.get('email'))
        return redirect('customer_list')
    return render(request, 'customer_list.html')

@login_required_session
def customer_edit(request, id):
    c = get_object_or_404(Customer, id=id)
    if request.method == "POST":
        c.name, c.mobile, c.email = request.POST.get('name'), request.POST.get('mobile'), request.POST.get('email')
        c.save(); return redirect('customer_list')
    return render(request, 'customer_list.html', {'customer': c})

@login_required_session
def customer_delete(request, id):
    get_object_or_404(Customer, id=id).delete(); return redirect('customer_list')


# ── QUOTATION LIST ──
@login_required_session
def quotation_list(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    qs = customer.quotations.all().order_by('-id')
    q  = request.GET.get('search')
    if q: qs = qs.filter(Q(quotation_no__icontains=q) | Q(project_type__icontains=q))
    return render(request, 'quotation_list.html', {
        'customer': customer, 'quotations': Paginator(qs,9).get_page(request.GET.get('page')), 'query': q
    })

@login_required_session
def quotation_add(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        Quotation.objects.create(customer=customer, project_type=request.POST.get('project_type'))
        return redirect('quotation_list', customer_id=customer.id)
    return render(request, 'quotation_form.html', {'customer': customer})

@login_required_session
def quotation_edit(request, id):
    q = get_object_or_404(Quotation, id=id)
    if request.method == "POST":
        q.project_type = request.POST.get('project_type'); q.save()
        return redirect('quotation_list', customer_id=q.customer.id)
    return render(request, 'quotation_form.html', {'q': q, 'customer': q.customer})

@login_required_session
def quotation_delete(request, id):
    q = get_object_or_404(Quotation, id=id); cid = q.customer.id; q.delete()
    return redirect('quotation_list', customer_id=cid)


# ── DUPLICATE QUOTATION VIEW ACTION ──
@login_required_session
def quotation_duplicate(request, id):
    original_quotation = get_object_or_404(Quotation, id=id)
    customer_id = original_quotation.customer.id

    new_quotation = Quotation.objects.create(
        customer=original_quotation.customer,
        project_type=original_quotation.project_type,
        quotation_no=original_quotation.quotation_no,
        date=date.today()
    )

    for item in original_quotation.items.all():
        QuotationItem.objects.create(
            quotation=new_quotation,
            item=item.item,
            material=item.material,
            l_val=item.l_val,
            d_val=item.d_val,
            h_val=item.h_val,
            qty_val=item.qty_val,
            quantity=item.quantity,
            item_count=item.item_count,
            rate=item.rate,
            discount_type=item.discount_type,
            discount_value=item.discount_value,
            image=item.image,
        )

    return redirect('quotation_list', customer_id=customer_id)


# ── UNITS / SUBUNITS ──
@login_required_session
def unit_list(request):    return render(request, 'unit_list.html', {'units': Unit.objects.all()})

@login_required_session
def unit_add(request):
    if request.method=="POST": Unit.objects.create(name=request.POST.get('name')); return redirect('unit_list')
    return render(request,'unit_form.html')

@login_required_session
def unit_edit(request,id):
    u=get_object_or_404(Unit,id=id)
    if request.method=="POST": u.name=request.POST.get('name'); u.save(); return redirect('unit_list')
    return render(request,'unit_form.html',{'unit':u})

@login_required_session
def unit_delete(request,id): Unit.objects.get(id=id).delete(); return redirect('unit_list')


@login_required_session
def subunit_list(request): return render(request,'subunit_list.html',{'subunits':SubUnit.objects.all(),'units':Unit.objects.all()})

@login_required_session
def subunit_add(request):
    if request.method=="POST": SubUnit.objects.create(unit_id=request.POST.get('unit'),name=request.POST.get('name')); return redirect('subunit_list')
    return render(request,'subunit_form.html',{'units':Unit.objects.all()})

@login_required_session
def subunit_edit(request,id):
    s=get_object_or_404(SubUnit,id=id)
    if request.method=="POST": s.unit_id,s.name=request.POST.get('unit'),request.POST.get('name'); s.save(); return redirect('subunit_list')
    return render(request,'subunit_form.html',{'sub':s,'units':Unit.objects.all()})

@login_required_session
def subunit_delete(request,id): SubUnit.objects.get(id=id).delete(); return redirect('subunit_list')


# ── ITEMS ──
@login_required_session
def item_list(request):
    qs = Item.objects.all().order_by('-id')
    q  = request.GET.get('search')
    if q: qs = qs.filter(Q(name__icontains=q))
    return render(request,'item_list.html',{'items':Paginator(qs,10).get_page(request.GET.get('page')),'query':q,'units':Unit.objects.all(),'subunits':SubUnit.objects.all()})

@login_required_session
def item_add(request):
    if request.method=="POST":
        c=request.POST.get('calculation_type')
        Item.objects.create(unit_id=request.POST.get('unit'),sub_unit_id=request.POST.get('sub_unit'),name=request.POST.get('name'),description=request.POST.get('description'),calculation_type=c,rate=request.POST.get('rate') if c=='nos' else None,image=request.FILES.get('image'))
        return redirect('item_list')
    return render(request,'item_form.html',{'units':Unit.objects.all(),'subunits':SubUnit.objects.all()})

@login_required_session
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

@login_required_session
def item_delete(request,id): Item.objects.get(id=id).delete(); return redirect('item_list')


# ── MATERIALS ──
def _subunits_json(): return list(SubUnit.objects.values('id','name','unit_id'))

@login_required_session
def material_list(request):
    return render(request,'material_list.html',{'materials':Material.objects.all(),'units':Unit.objects.all(),'subunits_json':_subunits_json()})

@login_required_session
def material_add(request):
    if request.method=="POST":
        Material.objects.create(unit_id=request.POST.get('unit'),sub_unit_id=request.POST.get('sub_unit') or None,name=request.POST.get('name'),description=request.POST.get('description'),rate=request.POST.get('rate'))
        return redirect('material_list')
    return render(request,'material_form.html',{'units':Unit.objects.all(),'subunits_json':_subunits_json()})

@login_required_session
def material_edit(request,id):
    m=get_object_or_404(Material,id=id)
    if request.method=="POST":
        m.unit_id=request.POST.get('unit'); m.sub_unit_id=request.POST.get('sub_unit') or None
        m.name=request.POST.get('name'); m.description=request.POST.get('description'); m.rate=request.POST.get('rate')
        m.save(); return redirect('material_list')
    return render(request,'material_form.html',{'material':m,'units':Unit.objects.all(),'subunits_json':_subunits_json()})

@login_required_session
def material_delete(request,id): Material.objects.get(id=id).delete(); return redirect('material_list')


# ── QUOTATION DETAIL ──
def _build_unit_data(quotation_items, quotation=None, request=None):
    unit_data = {}
    for q_item in quotation_items:
        u = q_item.item.unit
        if u not in unit_data:
            unit_data[u] = {
                'mrp_total': 0.0,
                'final_total': 0.0,
                'discount_display': '',
                'discount_type': 'percentage',
                'discount_value': 0.0,
            }
        unit_data[u]['mrp_total'] += float(q_item.mrp_total)
        unit_data[u]['final_total'] += float(q_item.final_total)

    for u, t in unit_data.items():
        base = t['final_total']
        discount_type = 'percentage'
        discount_value = 0.0

        if quotation and request and request.session:
            override = request.session.get(f'unit_discount_{quotation.id}_{u.id}')
            if override:
                discount_type = override.get('discount_type', 'percentage')
                discount_value = float(override.get('discount_value', 0) or 0)

        disc = 0.0
        if discount_value > 0:
            if discount_type == 'percentage':
                disc = (base * discount_value) / 100.0
                t['discount_display'] = f"{discount_value}% Off (-₹{disc:,.2f})"
            else:
                disc = discount_value
                t['discount_display'] = f"₹{discount_value} Off"

        t['discount_type'] = discount_type
        t['discount_value'] = discount_value
        t['unit_grand_total'] = max(0.0, base - disc)
    return unit_data


@login_required_session
def quotation_detail(request, id):
    quotation      = get_object_or_404(Quotation, id=id)
    units          = Unit.objects.all()
    materials_list = Material.objects.all()

    all_items = quotation.items.all().select_related(
        'item__unit', 'item__sub_unit', 'material'
    ).order_by('item__unit__id', 'item__sub_unit__id', 'id')

    unit_data       = _build_unit_data(all_items, quotation=quotation, request=request)
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

        uploaded_image = request.FILES.get('item_image')

        if calc_type == 'nos':
            item_obj     = get_object_or_404(Item, id=item_id)
            current_rate = float(item_obj.rate or 0)
            mat_obj      = None
        else:
            mat_obj      = get_object_or_404(Material, id=material_id)
            current_rate = float(mat_obj.rate)

        base_qty  = (l * max(d, h)) / 929 if calc_type == 'sqft' else (1 if calc_type == 'nos' else qv)
        final_qty = base_qty * item_count

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
            if uploaded_image:
                qi.image = uploaded_image
            qi.save()
        else:
            qi = QuotationItem.objects.create(
                quotation=quotation, item_id=item_id, material=mat_obj,
                l_val=l, d_val=d, h_val=h, qty_val=qv,
                quantity=final_qty, item_count=item_count,
                rate=current_rate, discount_type=disc_type, discount_value=disc_val
            )
            if uploaded_image:
                qi.image = uploaded_image
                qi.save()
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


@login_required_session
def update_unit_discount(request, quotation_id, unit_id):
    if request.method == "POST":
        u = get_object_or_404(Unit, id=unit_id)
        discount_type = request.POST.get('unit_discount_type', 'percentage')
        discount_value = float(request.POST.get('unit_discount_value', 0) or 0)

        if discount_value > 0:
            request.session[f'unit_discount_{quotation_id}_{unit_id}'] = {
                'discount_type': discount_type,
                'discount_value': discount_value,
            }
        else:
            request.session.pop(f'unit_discount_{quotation_id}_{unit_id}', None)

        messages.success(request, f"Discount updated for {u.name}!")
    return redirect('quotation_detail', id=quotation_id)


@login_required_session
def delete_quotation_item(request, item_id):
    qi = get_object_or_404(QuotationItem, id=item_id)
    qid = qi.quotation.id; qi.delete()
    return redirect('quotation_detail', id=qid)


@login_required_session
def load_subunits(request):
    unit_id = request.GET.get('unit')
    subs = SubUnit.objects.filter(unit_id=unit_id).order_by('name')
    options = '<option value="">-- Select Sub Unit --</option>'
    for s in subs:
        options += f'<option value="{s.id}">{s.name}</option>'
    return HttpResponse(options, content_type='text/html')


@login_required_session
def load_items(request):
    items = Item.objects.filter(sub_unit_id=request.GET.get('subunit')).order_by('name')
    options = ['<option value="">-- Select Item --</option>']
    for i in items:
        img_url = i.image.url if i.image else ""
        options.append(
            f'<option value="{i.id}" data-type="{i.calculation_type}" data-item-rate="{i.rate or 0}" data-image="{img_url}">{i.name}</option>'
        )
    return HttpResponse(''.join(options), content_type='text/html')


@login_required_session
def quotation_pdf(request, id):
    quotation = get_object_or_404(Quotation, id=id)

    hide_rate = request.GET.get('hide_rate') == '1'
    hide_mrp  = request.GET.get('hide_mrp')  == '1'
    hide_disc = request.GET.get('hide_disc') == '1'

    quotation_items = quotation.items.all().select_related(
        'item__unit', 'item__sub_unit', 'material'
    ).order_by('item__unit__id', 'item__sub_unit__id', 'id')

    unit_data = _build_unit_data(quotation_items, quotation=quotation, request=request)
    for q_item in quotation_items:
        u = q_item.item.unit
        if 'items' not in unit_data[u]:
            unit_data[u]['items'] = []
        unit_data[u]['items'].append(q_item)

    grand_mrp_total = sum(t['mrp_total']       for t in unit_data.values())
    grand_net_total = sum(t['unit_grand_total'] for t in unit_data.values())

    H = 'col-hidden'
    return render(request, 'quotation_pdf.html', {
        'quotation':       quotation,
        'unit_data':       unit_data,
        'grand_mrp_total': grand_mrp_total,
        'grand_net_total': grand_net_total,
        'hide_rate':       hide_rate,
        'hide_mrp':        hide_mrp,
        'hide_disc':       hide_disc,
        'cls_rate':        H if hide_rate else '',
        'cls_mrp':         H if hide_mrp  else '',
        'cls_disc':        H if hide_disc else '',
    })


# ---------- TEMPLATE LIST ----------
def template_list(request):
    query = request.GET.get('search', '')
    templates = Template.objects.all().order_by('-id')
    if query:
        templates = templates.filter(name__icontains=query)

    paginator = Paginator(templates, 12)
    templates = paginator.get_page(request.GET.get('page'))

    return render(request, 'template_list.html', {
        'templates': templates,
        'query': query,
    })


# ---------- ADD TEMPLATE ----------
def template_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Template.objects.create(name=name)
    return redirect('template_list')


# ---------- EDIT TEMPLATE ----------
def template_edit(request, template_id):
    tpl = get_object_or_404(Template, id=template_id)
    if request.method == 'POST':
        tpl.name = request.POST.get('name', tpl.name)
        tpl.save()
    return redirect('template_list')


# ---------- DELETE TEMPLATE ----------
def template_delete(request, template_id):
    get_object_or_404(Template, id=template_id).delete()
    return redirect('template_list')


# ---------- helper: save template item ----------
def _save_template_item(request, template):
    def dec(key):
        v = request.POST.get(key)
        try:
            return Decimal(str(v)) if v not in (None, '', 'None') else Decimal(0)
        except Exception:
            return Decimal(0)

    edit_id = request.POST.get('edit_id')
    calc_type = request.POST.get('calc_type')
    material_id = request.POST.get('material') or None
    l_val, d_val, h_val, qty_val = dec('l_val'), dec('d_val'), dec('h_val'), dec('qty_val')
    item_count = int(request.POST.get('item_count') or 1)
    discount_type = request.POST.get('discount_type') or 'percentage'
    discount_value = dec('discount_value')

    item_obj = get_object_or_404(Item, id=request.POST.get('item'))

    material_obj = None
    if calc_type == 'nos':
        rate = item_obj.rate or Decimal(0)
    else:
        if material_id:
            material_obj = Material.objects.filter(id=material_id).first()
        rate = material_obj.rate if material_obj else Decimal(0)

    if calc_type == 'sqft':
        base = (l_val * max(d_val, h_val)) / Decimal(929) if l_val > 0 else qty_val
    elif calc_type == 'nos':
        base = Decimal(1)
    else:
        base = qty_val

    quantity = base * Decimal(item_count)

    ti = get_object_or_404(TemplateItem, id=edit_id) if edit_id else TemplateItem(template=template)
    ti.item = item_obj
    ti.material = material_obj
    ti.l_val, ti.d_val, ti.h_val, ti.qty_val = l_val, d_val, h_val, qty_val
    ti.quantity = quantity
    ti.item_count = item_count
    ti.rate = rate
    ti.discount_type = discount_type
    ti.discount_value = discount_value
    ti.save()


# ---------- TEMPLATE DETAIL ----------
def template_detail(request, template_id):
    template = get_object_or_404(Template, id=template_id)

    if request.method == 'POST':
        _save_template_item(request, template)
        return redirect('template_detail', template_id=template.id)

    all_items = (TemplateItem.objects
                 .filter(template=template)
                 .select_related('item', 'item__unit', 'item__sub_unit', 'material')
                 .order_by('item__unit__id', 'item__sub_unit__id', 'id'))

    unit_data = {}
    grand_mrp_total = Decimal(0)
    grand_net_total = Decimal(0)

    for ti in all_items:
        unit = ti.item.unit
        if unit not in unit_data:
            unit_data[unit] = {'mrp_total': Decimal(0), 'item_net': Decimal(0)}
        mrp = Decimal(str(ti.mrp_total))
        net = Decimal(str(ti.final_total))
        unit_data[unit]['mrp_total'] += mrp
        unit_data[unit]['item_net'] += net
        grand_mrp_total += mrp

    for unit, data in unit_data.items():
        subtotal = data['item_net']
        if unit.discount_value and unit.discount_value > 0:
            if unit.discount_type == 'percentage':
                disc = (subtotal * Decimal(str(unit.discount_value))) / Decimal(100)
            else:
                disc = Decimal(str(unit.discount_value))
        else:
            disc = Decimal(0)
        data['unit_grand_total'] = max(Decimal(0), subtotal - disc)
        grand_net_total += data['unit_grand_total']

    return render(request, 'template_detail.html', {
        'template': template,
        'all_items': all_items,
        'unit_data': unit_data,
        'grand_mrp_total': grand_mrp_total,
        'grand_net_total': grand_net_total,
        'units': Unit.objects.all(),
        'materials_list': Material.objects.all(),
    })


# ---------- DELETE TEMPLATE ITEM ----------
def delete_template_item(request, item_id):
    ti = get_object_or_404(TemplateItem, id=item_id)
    template_id = ti.template.id
    ti.delete()
    return redirect('template_detail', template_id=template_id)


# ---------- UNIT DISCOUNT ----------
def template_unit_discount(request, template_id, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    if request.method == 'POST':
        unit.discount_type = request.POST.get('unit_discount_type') or 'percentage'
        unit.discount_value = request.POST.get('unit_discount_value') or 0
        unit.save()
    return redirect('template_detail', template_id=template_id)


# ---------- APPLY TEMPLATE TO QUOTATION ----------
def apply_template_to_quotation(request, quotation_id):
    quotation = get_object_or_404(Quotation, id=quotation_id)
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        if template_id:
            template = get_object_or_404(Template, id=template_id)
            for ti in template.items.all():
                QuotationItem.objects.create(
                    quotation=quotation, item=ti.item, material=ti.material,
                    l_val=ti.l_val, d_val=ti.d_val, h_val=ti.h_val,
                    qty_val=ti.qty_val, quantity=ti.quantity,
                    item_count=ti.item_count, rate=ti.rate,
                    discount_type=ti.discount_type, discount_value=ti.discount_value,
                )
    return redirect('quotation_detail', quotation.id)


def ajax_templates(request):
    data = [{'id': t.id, 'name': t.name} for t in Template.objects.all().order_by('-id')]
    return JsonResponse({'templates': data})
 
def ajax_template_items(request):
    template_id = request.GET.get('template_id')
    items = []
    if template_id:
        qs = (TemplateItem.objects
              .filter(template_id=template_id)
              .select_related('item', 'item__unit', 'item__sub_unit', 'material'))
        for ti in qs:
            items.append({
                'name': ti.item.name,
                'unit': ti.item.unit.name if ti.item.unit else '',
                'sub_unit': ti.item.sub_unit.name if ti.item.sub_unit else '',
                'count': ti.item_count,
                'rate': float(ti.rate),
                'mrp_total': float(ti.mrp_total),
                'final_total': float(ti.final_total),
            })
    return JsonResponse({'items': items})