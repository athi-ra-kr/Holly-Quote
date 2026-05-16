from django.db import models
from datetime import date

# 1. UNIT (e.g., Kitchen, Bedroom, Living Room)
class Unit(models.Model):
    name = models.CharField(max_length=100)

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
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} (₹{self.rate})"

# NEW MODEL: CUSTOMER
class Customer(models.Model):
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

# 5. QUOTATION (Updated with null=True and blank=True for migration safety)
class Quotation(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations', null=True, blank=True)
    quotation_no = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField(auto_now_add=True)
    project_type = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
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
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    @property
    def mrp_total(self):
        return self.quantity * self.rate

    def __str__(self):
        return f"{self.quotation.quotation_no} - {self.item.name}"