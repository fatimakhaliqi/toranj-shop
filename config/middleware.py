from django.conf import settings


class SecurityHeadersMiddleware:
    """CSP و Permissions-Policy. پنل ادمین جنگو از CSP معاف است."""

    CSP = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "object-src 'none'; base-uri 'self'; "
        "form-action 'self' https://payment.zarinpal.com https://sandbox.zarinpal.com; "
        "frame-ancestors 'none'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.lstrip("/").startswith(settings.ADMIN_URL):
            response.headers.setdefault("Content-Security-Policy", self.CSP)
        response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        return response
