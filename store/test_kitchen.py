from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from .kitchen import _recipe, kitchen_scene
from .models import Category, Finish, Product, Variant


@override_settings(KITCHEN_MODE="demo")
class KitchenTests(TestCase):
    def test_render_inventory_and_read_only_links(self):
        scene = kitchen_scene()
        root = Path(settings.BASE_DIR)/"static"/"kitchens"/scene["id"]
        for key, slot in scene["slots"].items():
            for model in slot["models"]:
                for variant in model["variants"]:
                    self.assertTrue((root/variant["thumb"].split("/")[-1]).is_file())
                    page = self.client.get(variant["url"])
                    self.assertContains(page,variant["availability"])
                    self.assertContains(page,variant["name"])
                    self.assertNotContains(page,'name="operation"')
                    for view in scene["views"].values():
                        self.assertIn(model["id"]+"."+variant["id"],view["hits"][key])
        for camera in scene["views"]:
            for size in ("small","large"):
                self.assertTrue((root/f"{camera}-{size}.webp").is_file())
            for group, keys in scene["groups"].items():
                options = [[v["index"] for m in scene["slots"][k]["models"] for v in m["variants"]] for k in keys]
                for indices in product(*options):
                    if any(indices):
                        name = "-".join(map(str,indices))
                        self.assertTrue((root/f"{camera}-{group}-{name}.webp").is_file())

    def test_demo_gating(self):
        url = reverse("kitchen-demo",args=["hood","bell"])
        self.assertEqual(self.client.get(url,{"finish":"missing"}).status_code,404)
        with override_settings(KITCHEN_MODE="off"):
            self.assertNotContains(self.client.get("/"),'id="kitchen-data"')
            self.assertEqual(self.client.get(url).status_code,404)

    @override_settings(KITCHEN_MODE="catalog")
    def test_live_binding_tracks_publication_and_stock(self):
        recipe = deepcopy(_recipe(settings.KITCHEN_SCENE))
        recipe["slots"]["faucet"]["models"][0]["variants"][0]["sku"] = "TEST-TAP"
        category = Category.objects.create(name="آشپزخانه",slug="kitchen")
        item = Product.objects.create(name="شیر آزمایشی",slug="test-tap",category=category)
        finish = Finish.objects.create(name="طلایی",slug="gold")
        variant = Variant.objects.create(product=item,finish=finish,sku="TEST-TAP",stock=0)
        with patch("store.kitchen._recipe",return_value=recipe):
            def mapped():
                return kitchen_scene()["slots"]["faucet"]["models"][0]["variants"][0]
            self.assertEqual(mapped()["availability"],"ناموجود")
            self.assertEqual(mapped()["url"],item.get_absolute_url()+"?finish=gold")
            variant.stock = 4
            variant.save()
            self.assertEqual(mapped()["availability"],"موجود")
            item.is_demo = True
            item.save()
            self.assertIsNone(kitchen_scene())

