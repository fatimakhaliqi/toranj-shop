from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("", views.order_list, name="list"),
    path("<str:code>/", views.order_detail, name="detail"),
    path("<str:code>/cancel/", views.order_cancel, name="cancel"),
]
