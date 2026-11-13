from django.core.management.base import BaseCommand

from orders.services import expire_unpaid_orders


class Command(BaseCommand):
    help = "سفارش‌های پرداخت‌نشده‌ی قدیمی را لغو و موجودی را برمی‌گرداند (با cron هر ۱۰ دقیقه اجرا شود)."

    def handle(self, *args, **options):
        self.stdout.write(f"{expire_unpaid_orders()} سفارش لغو شد.")
