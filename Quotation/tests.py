import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from . import views
from .models import Customer, Item, Quotation, QuotationItem, SubUnit, Unit


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class QuotationPdfImageTests(TestCase):
    def setUp(self):
        self.unit = Unit.objects.create(name='Kitchen')
        self.sub_unit = SubUnit.objects.create(unit=self.unit, name='Wardrobe')
        self.item = Item.objects.create(
            unit=self.unit,
            sub_unit=self.sub_unit,
            name='Test Item',
            calculation_type='nos',
            rate=100,
        )
        self.customer = Customer.objects.create(name='Test Customer', mobile='9999999999')
        self.quotation = Quotation.objects.create(customer=self.customer, project_type='Test')

        self.item_image = self._create_image_file('item-image.png', color='blue')
        self.item.image = self.item_image
        self.item.save()

        self.quotation_item = QuotationItem.objects.create(
            quotation=self.quotation,
            item=self.item,
            quantity=1,
            rate=100,
        )

        self.quotation_image = self._create_image_file('quotation-image.png', color='red')
        self.quotation_item.image = self.quotation_image
        self.quotation_item.save()

    def _create_image_file(self, name, color):
        image = Image.new('RGB', (20, 20), color=color)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')

    def test_pdf_prefers_quotation_item_image(self):
        session = self.client.session
        session['user'] = 'test-user'
        session.save()

        response = self.client.get(reverse('quotation_pdf', args=[self.quotation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'quotation-image.png')
        self.assertNotContains(response, 'item-image.png')

    def test_new_item_uses_posted_discount_when_created(self):
        session = self.client.session
        session['user'] = 'test-user'
        session.save()

        response = self.client.post(
            reverse('quotation_detail', args=[self.quotation.id]),
            {
                'item': self.item.id,
                'material': '',
                'calc_type': 'nos',
                'item_count': 1,
                'discount_type': 'flat',
                'discount_value': 25,
                'l_val': 0,
                'd_val': 0,
                'h_val': 0,
                'qty_val': 0,
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        created_item = QuotationItem.objects.filter(quotation=self.quotation).latest('id')
        self.assertEqual(created_item.discount_type, 'flat')
        self.assertEqual(created_item.discount_value, 25)

    def test_unit_discount_only_affects_target_quotation(self):
        session = self.client.session
        session['user'] = 'test-user'
        session.save()

        other_customer = Customer.objects.create(name='Other Customer', mobile='8888888888')
        other_quotation = Quotation.objects.create(customer=other_customer, project_type='Other')

        QuotationItem.objects.create(quotation=other_quotation, item=self.item, quantity=1, rate=100)

        session[f'unit_discount_{self.quotation.id}_{self.unit.id}'] = {
            'discount_type': 'flat',
            'discount_value': 10,
        }
        session.save()

        response = self.client.post(
            reverse('update_unit_discount', args=[self.quotation.id, self.unit.id]),
            {
                'unit_discount_type': 'flat',
                'unit_discount_value': 10,
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)

        request = self.client.get(reverse('quotation_detail', args=[self.quotation.id])).wsgi_request
        unit_data_for_current = views._build_unit_data(self.quotation.items.all(), quotation=self.quotation, request=request)
        current_unit = next(iter(unit_data_for_current))
        self.assertEqual(unit_data_for_current[current_unit]['unit_grand_total'], 90.0)

        request_other = self.client.get(reverse('quotation_detail', args=[other_quotation.id])).wsgi_request
        unit_data_for_other = views._build_unit_data(other_quotation.items.all(), quotation=other_quotation, request=request_other)
        other_unit = next(iter(unit_data_for_other))
        self.assertEqual(unit_data_for_other[other_unit]['unit_grand_total'], 100.0)

