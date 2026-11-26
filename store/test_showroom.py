from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, Finish, Inquiry, Product, Variant


class ShowroomRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="شیرآلات", slug="faucets")
        item = Product.objects.create(category=category, name="شیر تست", slug="fixture")
        finish = Finish.objects.create(name="کروم", slug="chrome")
        cls.variant = Variant.objects.create(product=item, finish=finish, sku="QA-CR", stock=2, price=150)

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.get(self.variant.product.get_absolute_url())
        self.csrf = self.client.cookies["csrftoken"].value

    def test_basket_request_keeps_snapshot_and_validates_available_stock(self):
        cart_url = reverse("cart-change", args=[self.variant.pk])
        data = {"operation": "add", "quantity": "۲"}
        self.assertEqual(self.client.post(cart_url, data).status_code, 403)
        headers = {"HTTP_X_CSRFTOKEN": self.csrf, "HTTP_HX_REQUEST": "true"}
        self.assertEqual(self.client.post(cart_url, data, **headers).status_code, 200)
        self.assertEqual(self.client.post(cart_url, data, **headers).status_code, 422)
        contact = {"name": "بازدیدکننده", "phone": "۰۹۱۱۰۰۰۰۰۰۰"}
        checkout = reverse("checkout")
        result = self.client.post(checkout, contact, HTTP_X_CSRFTOKEN=self.csrf)
        self.assertRedirects(result, checkout)
        inquiry = Inquiry.objects.get(kind=Inquiry.Kind.BASKET)
        self.assertEqual(inquiry.basket[0]["sku"], self.variant.sku)
        self.assertEqual(inquiry.basket[0]["quantity"], 2)
        self.assertEqual(inquiry.basket[0]["unit_price_toman"], 150)
        self.assertEqual(inquiry.phone, "09110000000")
        self.assertContains(self.client.get(reverse("cart")), self.variant.sku)
        self.assertNotContains(Client().get(reverse("cart")), self.variant.sku)
        self.variant.stock = 0
        self.variant.save()
        self.assertRedirects(self.client.post(checkout, contact, HTTP_X_CSRFTOKEN=self.csrf), reverse("cart"))
        self.assertEqual(Inquiry.objects.count(), 1)

    def test_quote_keeps_selected_variant_and_visit_rejects_a_past_date(self):
        contact = reverse("contact")
        data = {"name": "بازدیدکننده", "phone": "۰۹۱۱۰۰۰۰۰۰۰"}
        headers = {"HTTP_X_CSRFTOKEN": self.csrf}
        result = self.client.post(contact + "?kind=visit", {**data, "preferred_date": "2001-01-01"}, **headers)
        self.assertContains(result, 'href="#id_preferred_date"')
        self.assertFalse(Inquiry.objects.exists())
        for kind in ("visit", "consult", "quote"):
            url = contact + "?kind=" + kind
            if kind == "quote":
                url += "&product=fixture&finish=chrome"
            self.assertEqual(self.client.post(url, data, **headers).status_code, 302)
        self.assertEqual(Inquiry.objects.get(kind="quote").variant, self.variant)
        self.assertEqual(Inquiry.objects.count(), 3)
