from catalog.models import Category, Product
from django.db.models import Case, IntegerField, Min, Q, When


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
    'price-asc': ('min_fabric_price', 'base_price'),
    'price-desc': ('-min_fabric_price', '-base_price'),
    'name': ('name_uk',),
}


def apply_sort(qs, sort_key: str):
    fields = SORT_MAP.get(sort_key, SORT_MAP['popular'])
    return qs.order_by(*fields)
