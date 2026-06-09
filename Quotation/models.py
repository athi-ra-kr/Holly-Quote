from django.db import models
from datetime import date

# 1. UNIT (e.g., Kitchen, Bedroom, Living Room)
class Unit(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage (%)'),
        ('flat', 'Flat Amount (₹)'),
    ]

    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name


# 2. SUB-UNIT (e.g., Bottom Unit, Wall Unit, Wardrobe)
class SubUnit(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.unit.name} - {self.name}"


# 3. ITEM (The specific design/type with an image)
class Item(models.Model):
    CALCULATION_CHOICES = [
        ('sqft', 'Square Feet'),
        ('rm', 'Running Meter'),
        ('rf', 'Running Feet'),
        ('nos', 'Number'),
    ]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    sub_unit = models.ForeignKey(SubUnit, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    calculation_type = models.CharField(max_length=10, choices=CALCULATION_CHOICES, default='nos')
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='items/', blank=True, null=True)

    def __str__(self):
        return self.name


# 4. MATERIAL (The finish/material with specific rates)
class Material(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    sub_unit = models.ForeignKey(SubUnit, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} (₹{self.rate})"


# CUSTOMER MODEL
class Customer(models.Model):
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


# 5. QUOTATION
class Quotation(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations', null=True, blank=True)
    # ✅ REMOVED unique=True so we can create duplicates with the same number seamlessly!
    quotation_no = models.CharField(max_length=50, blank=True)
    date = models.DateField(auto_now_add=True)
    project_type = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        # This keeps your auto-generation safe! It only makes a new number if one wasn't passed down.
        if not self.quotation_no:
            last_q = Quotation.objects.all().order_by('id').last()
            if not last_q:
                new_id = 1
            else:
                new_id = last_q.id + 1

            current_year = str(date.today().year)[-2:]
            self.quotation_no = f"HBI-QTN-{new_id:03d}/{current_year}-R0"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.quotation_no


# 6. QUOTATION ITEM
class QuotationItem(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage (%)'),
        ('flat', 'Flat Amount (₹)'),
    ]

    quotation = models.ForeignKey(Quotation, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True)
    l_val = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    d_val = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    h_val = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    qty_val = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    item_count = models.PositiveIntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ✅ Optional per-line image. If empty, the template falls back to the Item's own image.
    image = models.ImageField(upload_to='quotation_item_images/', blank=True, null=True)

    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def mrp_total(self):
        return self.quantity * self.rate

    @property
    def discount_amount(self):
        mrp = float(self.mrp_total)
        val = float(self.discount_value)
        if val <= 0:
            return 0.0
        if self.discount_type == 'percentage':
            return (mrp * val) / 100.0
        elif self.discount_type == 'flat':
            return val
        return 0.0

    @property
    def final_total(self):
        total = float(self.mrp_total) - self.discount_amount
        return max(0.0, total)

    def __str__(self):
        return f"{self.quotation.quotation_no} - {self.item.name}"


# 7. TEMPLATE
class Template(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


# 8. TEMPLATE ITEM
class TemplateItem(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage (%)'),
        ('flat', 'Flat Amount (₹)'),
    ]

    template = models.ForeignKey(Template, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    l_val = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    d_val = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    h_val = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    qty_val = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    item_count = models.PositiveIntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def mrp_total(self):
        return self.quantity * self.rate

    @property
    def discount_amount(self):
        mrp = float(self.mrp_total)
        val = float(self.discount_value)
        if val <= 0:
            return 0.0
        if self.discount_type == 'percentage':
            return (mrp * val) / 100.0
        elif self.discount_type == 'flat':
            return val
        return 0.0

    @property
    def final_total(self):
        total = float(self.mrp_total) - self.discount_amount
        return max(0.0, total)

    def __str__(self):
        return f"{self.template.name} - {self.item.name}"