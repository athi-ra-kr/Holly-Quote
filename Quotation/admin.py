from django.contrib import admin
from .models import Unit, SubUnit, Item, Material, Quotation, QuotationItem

@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    # This adds the columns to the list view
    list_display = ('quotation', 'item', 'l_val', 'd_val', 'h_val', 'qty_val', 'item_count', 'quantity', 'rate', 'mrp_total')
    
    # This allows you to click and edit them inside the admin form
    fields = ('quotation', 'item', 'material', 'l_val', 'd_val', 'h_val', 'qty_val', 'item_count', 'quantity', 'rate')
    
    # Optional: makes quantity read-only if you want the model to calculate it automatically
    # readonly_fields = ('quantity',) 

# Register other models so they show up too
admin.site.register(Unit)
admin.site.register(SubUnit)
admin.site.register(Item)
admin.site.register(Material)
admin.site.register(Quotation)