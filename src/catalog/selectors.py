from catalog.models import Category, Product
from django.db.models import Case, IntegerField, Min, Q, When
from django.db.models.functions import Coalesce


def visible_products():
    return (
        Product.objects.filter(is_active=True)
        .select_related('category', 'category__parent')
        .prefetch_related(
            'fabric_prices__fabric',
            'shade_images__shade',
            'shade_images__shade__fabric',
        )
        .annotate(min_fabric_price=Min('fabric_prices__price'))
    )


def with_effective_price(qs):
    if 'effective_price' in getattr(qs.query, 'annotations', {}):
        return qs
    return qs.annotate(effective_price=Coalesce('min_fabric_price', 'base_price'))


def home_featured():
    return visible_products().annotate(
        featured=Case(
            When(badge=Product.Badge.HIT, then=0),
            When(badge=Product.Badge.NEW, then=1),
            When(badge=Product.Badge.TOP, then=2),
            default=3,
            output_field=IntegerField(),
        )
    ).order_by('featured', '-created_at')


def products_in_category(category: Category):
    qs = visible_products()
    child_ids = list(category.children.filter(is_active=True).values_list('id', flat=True))
    if child_ids:
        return qs.filter(category_id__in=[category.id, *child_ids])
    return qs.filter(category=category)


def related_products(product: Product, *, limit: int = 3):
    """Товари з тієї ж / батьківської категорії; якщо мало — добиваємо з каталогу."""
    exclude_pk = product.pk
    collected: list[Product] = []
    seen: set[int] = {exclude_pk}

    def _extend(qs) -> bool:
        for item in qs:
            if item.pk in seen:
                continue
            seen.add(item.pk)
            collected.append(item)
            if len(collected) >= limit:
                return True
        return False

    if _extend(products_in_category(product.category).exclude(pk=exclude_pk)):
        return collected

    parent = product.category.parent
    if parent and _extend(products_in_category(parent).exclude(pk=exclude_pk)):
        return collected

    _extend(home_featured().exclude(pk=exclude_pk))
    return collected


def top_categories():
    return Category.objects.filter(is_active=True, parent__isnull=True).order_by('sort')


def apply_listing_filters(qs, *, cat_slug=None, price_min=None, price_max=None, available=False):
    selected_cat = None
    if cat_slug:
        selected_cat = Category.objects.filter(
            is_active=True,
            parent__isnull=True,
            slug=cat_slug,
        ).first()
        if selected_cat:
            qs = products_in_category(selected_cat)
    qs = with_effective_price(qs)
    if price_min is not None:
        qs = qs.filter(effective_price__gte=price_min)
    if price_max is not None:
        qs = qs.filter(effective_price__lte=price_max)
    if available:
        qs = qs.filter(is_available=True)
    return qs, selected_cat


def search_products(query: str):
    q = (query or '').strip()
    if not q:
        return visible_products().none()
    return visible_products().filter(
        Q(name_uk__icontains=q)
        | Q(name_ru__icontains=q)
        | Q(sku__icontains=q)
        | Q(type_uk__icontains=q)
        | Q(type_ru__icontains=q)
    )


SORT_MAP = {
    'popular': ('-badge', '-created_at'),
    'new': ('-created_at',),
    'price-asc': ('effective_price', 'base_price'),
    'price-desc': ('-effective_price', '-base_price'),
    'name': ('name_uk',),
}


def apply_sort(qs, sort_key: str):
    qs = with_effective_price(qs)
    fields = SORT_MAP.get(sort_key, SORT_MAP['popular'])
    return qs.order_by(*fields)
