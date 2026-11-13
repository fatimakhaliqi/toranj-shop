from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path("faq/", TemplateView.as_view(template_name="pages/faq.html"), name="faq"),
    path("terms/", TemplateView.as_view(template_name="pages/terms.html"), name="terms"),
    path("contact/", views.contact, name="contact"),
    path("robots.txt", views.robots, name="robots"),
]
