from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("products/", views.product_list, name="list"),
    path("category/<str:slug>/", views.product_list, name="category"),
    path("product/<int:pk>/<str:slug>/", views.product_detail, name="detail"),
    path("product/<int:pk>/review/", views.add_review, name="review"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/<int:pk>/toggle/", views.wishlist_toggle, name="wishlist_toggle"),
]
