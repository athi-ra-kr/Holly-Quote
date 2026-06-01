from django.urls import path
from . import views

urlpatterns = [
    # Auth & Dashboard
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    # --- NEW CUSTOMERS CRUD ---
    path('customers/', views.customer_list, name='customer_list'),
    path('customer/add/', views.customer_add, name='customer_add'),
    path('customer/edit/<int:id>/', views.customer_edit, name='customer_edit'),
    path('customer/delete/<int:id>/', views.customer_delete, name='customer_delete'),

    # --- UPDATED QUOTATIONS (Scoped to a Specific Customer) ---
    path('customer/<int:customer_id>/quotations/', views.quotation_list, name='quotation_list'),
    path('customer/<int:customer_id>/quotation/add/', views.quotation_add, name='quotation_add'),
    
    # Standalone Quotation Actions
    path('quotation/edit/<int:id>/', views.quotation_edit, name='quotation_edit'),
    path('quotation/delete/<int:id>/', views.quotation_delete, name='quotation_delete'),
    path('quotation/detail/<int:id>/', views.quotation_detail, name='quotation_detail'),

    # Units
    path('units/', views.unit_list, name='unit_list'),
    path('unit/add/', views.unit_add, name='unit_add'),
    path('unit/edit/<int:id>/', views.unit_edit, name='unit_edit'),
    path('unit/delete/<int:id>/', views.unit_delete, name='unit_delete'),

    # Sub Units
    path('subunit/add/', views.subunit_add, name='subunit_add'),
    path('subunit/edit/<int:id>/', views.subunit_edit, name='subunit_edit'),
    path('subunit/delete/<int:id>/', views.subunit_delete, name='subunit_delete'),

    # Items
    path('item/add/', views.item_add, name='item_add'),
    path('item/edit/<int:id>/', views.item_edit, name='item_edit'),
    path('item/delete/<int:id>/', views.item_delete, name='item_delete'),

    # Materials
    path('material/add/', views.material_add, name='material_add'),
    path('material/edit/<int:id>/', views.material_edit, name='material_edit'),
    path('material/delete/<int:id>/', views.material_delete, name='material_delete'),
    
    path('subunits/', views.subunit_list, name='subunit_list'),
    path('items/', views.item_list, name='item_list'),
    path('materials/', views.material_list, name='material_list'),
    
    # --- QUOTATION ITEM ACTIONS ---
    path('quotation/item/<int:item_id>/delete/', views.delete_quotation_item, name='delete_quotation_item'),

    # --- SMART DROPDOWN PATHS ---
    path('ajax/load-subunits/', views.load_subunits, name='ajax_load_subunits'),
    path('ajax/load-items/', views.load_items, name='ajax_load_items'),

    # --- NEW UNIT LEVEL ACTIONS ---
    # UPDATED: This path maps the main unit discount form directly to its processing view
    path('quotation/<int:quotation_id>/unit/<int:unit_id>/discount/', views.update_unit_discount, name='update_unit_discount'),
    path('quotation/<int:id>/pdf/', views.quotation_pdf, name='quotation_pdf'),
]