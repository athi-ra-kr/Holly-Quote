import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

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
