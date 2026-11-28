import re
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Project, ProjectImage


@override_settings(DEBUG=True, KITCHEN_MODE="off")
class ProjectCardTests(TestCase):
    def test_rebuilding_stylesheet_changes_its_url_on_both_pages(self):
        def stylesheet(page):
            html = self.client.get(reverse(page)).content.decode()
            return re.search(r'href="([^"]+/storefront\.css\?v=[a-f0-9]+)"', html)[1]

        with TemporaryDirectory() as directory, self.settings(BASE_DIR=Path(directory)):
            css = Path(directory) / "static/css/storefront.css"
            css.parent.mkdir(parents=True)
            css.write_bytes(b".project-grid{}")
            before = stylesheet("projects")
            css.write_bytes(b".project-grid{display:grid}")
            after = stylesheet("projects")
            self.assertNotEqual(before, after)
            self.assertEqual(after, stylesheet("home"))

    def test_both_pages_use_the_same_cards_and_covers(self):
        kitchen = Project.objects.create(
            title="آشپزخانه", slug="kitchen", summary="سنگ و چوب", image="demo/hero.jpg", is_demo=True,
        )
        detail = ProjectImage.objects.create(project=kitchen, image="projects/gallery/detail.jpg")
        bath = Project.objects.create(title="حمام", slug="bath", image="projects/bath.jpg")
        for name, level in (("home", "h3"), ("projects", "h2")):
            page = self.client.get(reverse(name))
            self.assertTemplateUsed(page, "partials/project-grid.html")
            self.assertTemplateUsed(page, "partials/project-card.html")
            self.assertContains(page, detail.image.url)
            self.assertContains(page, bath.image.url)
            self.assertContains(page, f"<{level}>{kitchen.title}</{level}>", html=True)

    def test_new_publications_join_the_index_and_handle_missing_photos(self):
        for index in range(2):
            Project.objects.create(title="فضای داخلی", slug=f"room-{index}", image="projects/room.jpg")
        newest = Project.objects.create(title="چیدمان جدید", slug="new", published=False)
        self.assertNotContains(self.client.get(reverse("projects")), newest.get_absolute_url())
        newest.published = True
        newest.save()
        listing = self.client.get(reverse("projects"))
        self.assertContains(listing, 'class="project-card"', count=3)
        self.assertContains(listing, newest.get_absolute_url())
        self.assertContains(listing, "تصویر پروژه در دسترس نیست")
        self.assertNotContains(self.client.get(reverse("home")), newest.get_absolute_url())
