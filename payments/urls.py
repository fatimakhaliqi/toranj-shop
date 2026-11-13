from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("start/<str:code>/", views.start, name="start"),
    path("callback/", views.callback, name="callback"),
    path("mock/<str:authority>/", views.mock, name="mock"),
]
