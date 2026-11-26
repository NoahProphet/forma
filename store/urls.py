from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse_lazy

from . import views
from .kitchen import demo_detail

urlpatterns = [
    path("", views.home, name="home"),
    path("kitchen-preview/<slug:category>/<slug:model>/", demo_detail, name="kitchen-demo"),
    path("login/", LoginView.as_view(
        template_name="account/access.html",
        next_page=reverse_lazy("account"),
        extra_context={"title": "ورود به حساب", "private_page": True},
    ), name="login"),
    path("register/", views.register_account, name="register"),
    path("account/", views.account, name="account"),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy("home")), name="logout"),
    path("shop/", views.shop, name="shop"),
    path("product/<slug:slug>/", views.product, name="product"),
    path("compare/", views.compare, name="compare"),
    path("compare/<slug:slug>/", views.change_comparison, name="change-comparison"),
    path("cart/", views.cart, name="cart"),
    path("cart/<int:pk>/", views.cart_change, name="cart-change"),
    path("checkout/", views.checkout, name="checkout"),
    path("brands/", views.brands, name="brands"),
    path("projects/", views.project_index, name="projects"),
    path("projects/<slug:slug>/", views.project, name="project"),
    path("journal/", views.journal, name="journal"),
    path("journal/<slug:slug>/", views.article, name="article"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("faq/", views.faq, name="faq"),
]
