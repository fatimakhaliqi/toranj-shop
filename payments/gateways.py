"""درگاه‌های پرداخت. در حال حاضر: زرین‌پال (واقعی) و درگاه آزمایشی (فقط در حالت DEBUG)."""
import uuid

from django.conf import settings
from django.urls import reverse


class GatewayError(Exception):
    pass


class ZarinpalGateway:
    name = "zarinpal"

    def __init__(self):
        host = "sandbox.zarinpal.com" if settings.ZARINPAL_SANDBOX else "payment.zarinpal.com"
        self.base = f"https://{host}/pg/v4/payment"
        self.start_base = f"https://{host}/pg/StartPay/"

    def _post(self, path, payload):
        import requests  # در requirements.txt موجود است
        try:
            resp = requests.post(f"{self.base}/{path}.json", json=payload, timeout=15,
                                 headers={"Accept": "application/json"})
            return resp.json()
        except Exception as exc:
            raise GatewayError("ارتباط با درگاه پرداخت برقرار نشد.") from exc

    def request(self, payment, callback_url, mobile=""):
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": payment.amount * 10,  # تومان → ریال
            "callback_url": callback_url,
            "description": f"سفارش {payment.order.code}",
        }
        if mobile:
            payload["metadata"] = {"mobile": mobile}
        data = self._post("request", payload).get("data") or {}
        if data.get("code") == 100 and data.get("authority"):
            return data["authority"]
        raise GatewayError("درگاه پرداخت درخواست را نپذیرفت.")

    def start_url(self, payment):
        return self.start_base + payment.authority

    def verify(self, payment, status_param):
        if status_param != "OK":
            return False, ""
        data = self._post("verify", {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": payment.amount * 10,
            "authority": payment.authority,
        }).get("data") or {}
        if data.get("code") in (100, 101):
            return True, str(data.get("ref_id", ""))
        return False, ""


class MockGateway:
    """فقط برای توسعه: صفحه‌ی پرداخت جعلی که موفق/ناموفق را شبیه‌سازی می‌کند."""
    name = "mock"

    def request(self, payment, callback_url, mobile=""):
        return "MOCK" + uuid.uuid4().hex[:24]

    def start_url(self, payment):
        return reverse("payments:mock", args=[payment.authority])

    def verify(self, payment, status_param):
        return status_param == "OK", "MOCK-REF-" + payment.authority[-6:]


def get_gateway():
    if settings.ZARINPAL_MERCHANT_ID:
        return ZarinpalGateway()
    if settings.DEBUG:
        return MockGateway()
    raise GatewayError("درگاه پرداخت تنظیم نشده است.")
