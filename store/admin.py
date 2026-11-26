from django.contrib import admin

from .models import Article, Brand, Category, Finish, Inquiry, Product, Project, ProjectImage, Variant, VariantImage

admin.site.site_header = "مدیریت شوروم فرما"


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "category", "brand", "active", "featured", "is_demo")
    list_filter = ("category", "brand", "active", "featured", "is_demo")
    search_fields = ("name", "model", "variants__sku")
    inlines = [VariantInline]


class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 0


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "finish", "price", "stock")
    search_fields = ("sku", "product__name")
    inlines = [VariantImageInline]


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "published", "is_demo")
    filter_horizontal = ("products",)
    inlines = [ProjectImageInline]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "name", "phone", "created", "handled")
    list_filter = ("kind", "handled")
    search_fields = ("name", "phone", "message")
    readonly_fields = ("created", "kind", "name", "phone", "message", "preferred_date", "variant", "basket")


admin.site.register([Article, Brand, Category, Finish])
