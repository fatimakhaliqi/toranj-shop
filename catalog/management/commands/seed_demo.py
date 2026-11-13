import random

from django.core.management.base import BaseCommand

from catalog.models import Category, Product
from orders.models import Coupon

DATA = {
    ("موبایل و تبلت", "📱"): ["گوشی هوشمند مدل آلفا", "گوشی هوشمند مدل بتا", "تبلت ۱۰ اینچ", "پاوربانک ۲۰۰۰۰ میلی‌آمپر"],
    ("لپ‌تاپ و کامپیوتر", "💻"): ["لپ‌تاپ ۱۵ اینچ", "ماوس بی‌سیم", "کیبورد مکانیکال", "هارد اکسترنال ۱ ترابایت"],
    ("لوازم خانگی", "🏠"): ["جاروبرقی شارژی", "قهوه‌ساز اتوماتیک", "هواپز ۵ لیتری", "سرخ‌کن بدون روغن"],
    ("مد و پوشاک", "👕"): ["تی‌شرت نخی مردانه", "مانتو تابستانی", "کفش کتانی راحتی", "کوله‌پشتی ضدآب"],
    ("ورزش و سفر", "⚽"): ["توپ فوتبال", "کیسه خواب", "بطری آب ورزشی", "دمبل ۵ کیلویی"],
    ("کتاب و لوازم تحریر", "📚"): ["رمان کلاسیک", "دفتر یادداشت", "ست خودکار", "کتاب آموزش برنامه‌نویسی"],
}


class Command(BaseCommand):
    help = "داده‌ی نمونه برای دیدن ظاهر سایت (قبل از انتشار، محصولات نمونه را از ادمین پاک کنید)."

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write("محصولی وجود دارد؛ چیزی اضافه نشد.")
            return
        rnd, n = random.Random(7), 0
        for order, ((name, icon), products) in enumerate(DATA.items()):
            cat = Category.objects.create(name=name, icon=icon, sort_order=order)
            for title in products:
                n += 1
                price = rnd.choice([190, 350, 490, 790, 1250, 2400, 3900]) * 1000
                Product.objects.create(
                    category=cat, name=title, sku=f"DEMO-{n:03d}", price=price,
                    compare_at_price=int(price * 1.25) if n % 3 == 0 else None,
                    stock=rnd.randint(0, 25), is_featured=n % 5 == 0, sold_count=rnd.randint(0, 40),
                    short_description="محصول نمونه برای نمایش ظاهر فروشگاه.",
                    description="این یک توضیح نمونه است. از پنل مدیریت ویرایش کنید.")
        Coupon.objects.get_or_create(code="WELCOME10", defaults={"percent": 10, "max_discount": 200000})
        self.stdout.write(self.style.SUCCESS(f"{n} محصول نمونه و کد تخفیف WELCOME10 ساخته شد."))
