# فروشگاه اینترنتی فارسی (Django 5.2)

امکانات: کاتالوگ و جستجو و فیلتر، سبد خرید، کد تخفیف، ثبت سفارش با رزرو موجودی، پرداخت زرین‌پال،
حساب کاربری (ورود با ایمیل/نام کاربری، آدرس‌ها، بازیابی رمز)، علاقه‌مندی، نظرات با تأیید مدیر،
پنل مدیریت فارسی، sitemap/robots، تقویم شمسی.

## اجرا روی کامپیوتر (ویندوز)
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py seed_demo        # (اختیاری) محصولات نمونه
    python manage.py runserver

## تست
    python manage.py test

## انتشار
مراحل کامل در پیام همراه فایل آمده. فایل‌های نمونه: `deploy/` و `.env.production`.
دستور لغو سفارش‌های پرداخت‌نشده (با cron هر ۱۰ دقیقه):
    venv/bin/python manage.py expire_unpaid_orders
