from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from pages.sitemaps import SITEMAPS

admin.site.site_header = "مدیریت فروشگاه"
admin.site.site_title = "مدیریت فروشگاه"
admin.site.index_title = "پنل مدیریت"

handler404 = "pages.views.error_404"
handler500 = "pages.views.error_500"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("payments/", include("payments.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("", include("catalog.urls")),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
