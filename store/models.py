from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField("نام", max_length=100)
    slug = models.SlugField(unique=True)
    description = models.CharField("توضیح", max_length=240, blank=True)
    image = models.ImageField("تصویر", upload_to="categories/", blank=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ("order", "pk")
        verbose_name = "دسته"
        verbose_name_plural = "دسته‌ها"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField("نام", max_length=100)
    slug = models.SlugField(unique=True)
    is_demo = models.BooleanField("نمونه توسعه", default=False)

    class Meta:
        ordering = ("name",)
        verbose_name = "برند"
        verbose_name_plural = "برندها"

    def __str__(self):
        return self.name


class Finish(models.Model):
    name = models.CharField("نام", max_length=100)
    slug = models.SlugField(unique=True)
    color = models.CharField("رنگ", max_length=7, blank=True, validators=[
        RegexValidator(r"\A#[0-9a-fA-F]{6}\Z", "رنگ را به صورت ‎#RRGGBB وارد کنید.")
    ])

    class Meta:
        ordering = ("name",)
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("نام", max_length=150)
    slug = models.SlugField(unique=True)
    model = models.CharField("مدل", max_length=60, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, blank=True, null=True)
    description = models.TextField("توضیحات", blank=True)
    material = models.CharField("جنس", max_length=120, blank=True)
    size = models.CharField("ابعاد", max_length=120, blank=True)
    image = models.ImageField("تصویر اصلی", upload_to="products/", blank=True)
    featured = models.BooleanField("منتخب", default=False)
    active = models.BooleanField("منتشرشده", default=True)
    is_demo = models.BooleanField("نمونه توسعه", default=False)

    class Meta:
        ordering = ("-pk",)
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product", kwargs={"slug": self.slug})


class Variant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    finish = models.ForeignKey(Finish, on_delete=models.PROTECT)
    sku = models.CharField("شناسه کالا", unique=True, max_length=75)
    price = models.PositiveIntegerField("قیمت (تومان)", null=True, blank=True)
    stock = models.PositiveIntegerField("موجودی", null=True, blank=True)
    image = models.ImageField("تصویر پرداخت", upload_to="variants/", blank=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ("order", "pk")
        constraints = [
            models.UniqueConstraint(fields=("product", "finish"), name="unique_product_finish"),
        ]
        verbose_name = "گزینه خرید"
        verbose_name_plural = "گزینه‌های خرید"

    def __str__(self):
        return f"{self.product} / {self.finish}"

    @property
    def purchasable(self):
        return self.price is not None and self.stock is not None and self.stock > 0


class VariantImage(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField("تصویر", upload_to="variants/gallery/")
    alt = models.CharField("متن جایگزین", max_length=180)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ("order", "pk")


class Project(models.Model):
    title = models.CharField("عنوان", max_length=150)
    slug = models.SlugField(unique=True)
    summary = models.CharField("خلاصه", max_length=240)
    body = models.TextField("متن")
    image = models.ImageField("تصویر اصلی", upload_to="projects/", blank=True)
    products = models.ManyToManyField(Product, blank=True, verbose_name="محصولات")
    published = models.BooleanField("منتشرشده", default=True)
    is_demo = models.BooleanField("نمونه توسعه", default=False)

    class Meta:
        ordering = ("pk",)
        verbose_name = "پروژه"
        verbose_name_plural = "پروژه‌ها"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("project", kwargs={"slug": self.slug})


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField("تصویر", upload_to="projects/gallery/")
    alt = models.CharField("متن جایگزین", max_length=180)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ("order", "pk")


class Article(models.Model):
    title = models.CharField("عنوان", max_length=150)
    slug = models.SlugField(unique=True)
    summary = models.CharField("خلاصه", max_length=240)
    body = models.TextField("متن")
    image = models.ImageField("تصویر", upload_to="journal/", blank=True)
    published = models.BooleanField("منتشرشده", default=False)
    published_at = models.DateField("تاریخ انتشار", blank=True, null=True)

    class Meta:
        ordering = ("-published_at", "pk")
        verbose_name = "مطلب"
        verbose_name_plural = "مطالب"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("article", kwargs={"slug": self.slug})


class Inquiry(models.Model):
    class Kind(models.TextChoices):
        CONSULT = "consult", "مشاوره"
        QUOTE = "quote", "استعلام قیمت"
        VISIT = "visit", "هماهنگی بازدید"
        BASKET = "basket", "هماهنگی خرید"

    kind = models.CharField("نوع درخواست", max_length=10, choices=Kind.choices)
    name = models.CharField("نام", max_length=100)
    phone = models.CharField("شماره تماس", max_length=16)
    message = models.TextField("جزئیات", blank=True, max_length=2000)
    preferred_date = models.DateField("روز پیشنهادی", null=True, blank=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    basket = models.JSONField("محصولات درخواست", default=list, blank=True)
    created = models.DateTimeField("زمان ثبت", auto_now_add=True)
    handled = models.BooleanField("پیگیری‌شده", default=False)

    class Meta:
        ordering = ("-created",)
        verbose_name = "درخواست شوروم"
        verbose_name_plural = "درخواست‌های شوروم"

    def __str__(self):
        return f"{self.get_kind_display()} · {self.name}"


class CartLine(models.Model):
    basket = models.CharField(max_length=32)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("basket", "variant"), name="unique_basket_variant"),
            models.CheckConstraint(condition=models.Q(quantity__gte=1, quantity__lte=99), name="cart_line_quantity_range"),
        ]
