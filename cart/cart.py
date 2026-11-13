from catalog.models import Product
from orders.models import Coupon
from orders.pricing import shipping_cost


class Cart:
    KEY, COUPON_KEY = "cart", "coupon_code"
    MAX_QTY = 20

    def __init__(self, request):
        self.session = request.session
        self.data = dict(self.session.get(self.KEY) or {})
        self._items = None

    def _save(self):
        self.session[self.KEY] = self.data
        self.session.modified = True
        self._items = None

    def add(self, product, qty=1):
        self.set(product, self.data.get(str(product.pk), 0) + qty)

    def set(self, product, qty):
        qty = max(0, min(int(qty), self.MAX_QTY, product.stock))
        if qty:
            self.data[str(product.pk)] = qty
        else:
            self.data.pop(str(product.pk), None)
        self._save()

    def remove(self, product_id):
        self.data.pop(str(product_id), None)
        self._save()

    def clear(self):
        self.data = {}
        self.session.pop(self.COUPON_KEY, None)
        self._save()

    def items(self):
        if self._items is None:
            ids = [int(k) for k in self.data if str(k).isdigit()]
            products = Product.objects.filter(pk__in=ids, is_active=True).prefetch_related("images").in_bulk(ids)
            self._items = []
            for pk in ids:
                product = products.get(pk)
                qty = min(self.data[str(pk)], product.stock) if product else 0
                if qty > 0:
                    self._items.append({"product": product, "quantity": qty,
                                        "unit_price": product.price, "line_total": product.price * qty})
        return self._items

    def __len__(self):
        return sum(i["quantity"] for i in self.items())

    @property
    def subtotal(self):
        return sum(i["line_total"] for i in self.items())

    @property
    def coupon_code(self):
        return self.session.get(self.COUPON_KEY, "")

    @property
    def coupon(self):
        code = self.coupon_code
        return Coupon.objects.filter(code__iexact=code).first() if code else None

    @property
    def discount(self):
        coupon = self.coupon
        if coupon and not coupon.validate_for(self.subtotal):
            return coupon.discount_for(self.subtotal)
        return 0

    @property
    def shipping(self):
        return shipping_cost(self.subtotal - self.discount)

    @property
    def total(self):
        return self.subtotal - self.discount + self.shipping
