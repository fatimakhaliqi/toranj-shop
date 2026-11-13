from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from config.ratelimit import ratelimit

from .forms import ReviewForm
from .models import Category, Product, Review, WishlistItem

SORTS = {
    "new": ("جدیدترین", ["-created_at"]),
    "bestseller": ("پرفروش‌ترین", ["-sold_count", "-created_at"]),
    "cheap": ("ارزان‌ترین", ["price"]),
    "expensive": ("گران‌ترین", ["-price"]),
}


def _int(value):
    try:
        return max(0, int(str(value).strip()))
    except (TypeError, ValueError):
        return None


def with_rating(qs):
    return qs.annotate(
        avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
        review_count=Count("reviews", filter=Q(reviews__is_approved=True), distinct=True),
    )


def product_list(request, slug=None):
    category = get_object_or_404(Category, slug=slug, is_active=True) if slug else None
    qs = Product.objects.filter(is_active=True, category__is_active=True).prefetch_related("images")
    if category:
        qs = qs.filter(category_id__in=category.family_ids())

    q = request.GET.get("q", "").strip()[:100]
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(short_description__icontains=q) | Q(sku__iexact=q))
    min_p, max_p = _int(request.GET.get("min")), _int(request.GET.get("max"))
    if min_p is not None:
        qs = qs.filter(price__gte=min_p)
    if max_p:
        qs = qs.filter(price__lte=max_p)
    if request.GET.get("in_stock") == "1":
        qs = qs.filter(stock__gt=0)
    if request.GET.get("discount") == "1":
        qs = qs.filter(compare_at_price__gt=F("price"))

    sort = request.GET.get("sort", "new")
    if sort not in SORTS:
        sort = "new"
    qs = with_rating(qs).order_by(*SORTS[sort][1])

    page = Paginator(qs, settings.PAGE_SIZE).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "catalog/product_list.html", {
        "category": category, "page": page, "q": q, "sort": sort, "sorts": SORTS,
        "querystring": params.urlencode(),
        "min": request.GET.get("min", ""), "max": request.GET.get("max", ""),
        "in_stock": request.GET.get("in_stock") == "1", "discount": request.GET.get("discount") == "1",
    })


def product_detail(request, pk, slug):
    product = get_object_or_404(with_rating(Product.objects.filter(is_active=True, category__is_active=True)),
                                pk=pk)
    if slug != product.slug:
        return redirect(product, permanent=True)
    reviews = product.reviews.filter(is_approved=True).select_related("user")[:20]
    related = with_rating(Product.objects.filter(is_active=True, category=product.category)
                          .exclude(pk=product.pk).prefetch_related("images"))[:4]
    wished = request.user.is_authenticated and WishlistItem.objects.filter(
        user=request.user, product=product).exists()
    return render(request, "catalog/product_detail.html", {
        "product": product, "images": product.images.all(), "reviews": reviews, "related": related,
        "wished": wished, "review_form": ReviewForm(),
        "qty_range": range(1, min(product.stock, 10) + 1),
    })


@login_required
@require_POST
@ratelimit("review", limit=10, window=3600)
def add_review(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    form = ReviewForm(request.POST)
    if form.is_valid():
        Review.objects.update_or_create(
            product=product, user=request.user,
            defaults={"rating": form.cleaned_data["rating"], "comment": form.cleaned_data["comment"],
                      "is_approved": False})
        messages.success(request, "نظر شما ثبت شد و پس از تأیید نمایش داده می‌شود.")
    else:
        messages.error(request, "نظر یا امتیاز معتبر نیست.")
    return redirect(product)


@login_required
@require_POST
def wishlist_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    obj, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        messages.info(request, "از علاقه‌مندی‌ها حذف شد.")
    else:
        messages.success(request, "به علاقه‌مندی‌ها اضافه شد.")
    return redirect(product)


@login_required
def wishlist(request):
    items = WishlistItem.objects.filter(user=request.user, product__is_active=True) \
        .select_related("product").prefetch_related("product__images")
    return render(request, "catalog/wishlist.html", {"items": items})
