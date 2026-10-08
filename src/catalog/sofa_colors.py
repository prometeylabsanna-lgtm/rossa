"""Єдина палітра відтінків для диванів (HEX-кружечки)."""

from __future__ import annotations

from django.db.models import Q

from catalog.models import Fabric, Product, ProductColor, ProductColorOption, Shade
from catalog.sofa_categories import SOFA_SUBCATEGORY_SLUGS

# slug, name_uk, name_ru, hex, sort
SOFA_COLOR_PALETTE = (
    ('beige', 'Беж', 'Беж', '#D4C4A8', 0),
    ('light-grey', 'Світло-сірий', 'Светло-серый', '#C5C5C0', 1),
    ('green', 'Зелений', 'Зелёный', '#6E7F5E', 2),
    ('orange', 'Оранжевий', 'Оранжевый', '#C86A3C', 3),
    ('graphite', 'Графіт', 'Графит', '#4A4A4A', 4),
    ('brown', 'Коричневий', 'Коричневый', '#3C2415', 5),
)

SOFA_CATEGORY_SLUGS = frozenset({'divany'}) | SOFA_SUBCATEGORY_SLUGS


def ensure_color_options() -> dict[str, ProductColorOption]:
    options: dict[str, ProductColorOption] = {}
    keep = {row[0] for row in SOFA_COLOR_PALETTE}
    for slug, name_uk, name_ru, hex_color, sort in SOFA_COLOR_PALETTE:
        option, _ = ProductColorOption.objects.get_or_create(
            slug=slug,
            defaults={
                'name_uk': name_uk,
                'name_ru': name_ru,
                'hex_color': hex_color,
                'sort': sort,
                'is_active': True,
            },
        )
        option.name_uk = name_uk
        option.name_ru = name_ru
        option.hex_color = hex_color
        option.sort = sort
        option.is_active = True
        option.save()
        options[slug] = option
    ProductColorOption.objects.exclude(slug__in=keep).update(is_active=False)
    return options


def sync_fabric_shades(fabrics=None) -> None:
    """Оновлює Shade для категорій тканини під ту саму палітру."""
    qs = fabrics if fabrics is not None else Fabric.objects.filter(is_active=True)
    keep = {row[0] for row in SOFA_COLOR_PALETTE}
    for fabric in qs:
        for shade_slug, name_uk, name_ru, hex_color, sort in SOFA_COLOR_PALETTE:
            shade, _ = Shade.objects.get_or_create(
                fabric=fabric,
                slug=shade_slug,
                defaults={
                    'name_uk': name_uk,
                    'name_ru': name_ru,
                    'hex_color': hex_color,
                    'sort': sort,
                },
            )
            shade.name_uk = name_uk
            shade.name_ru = name_ru
            shade.hex_color = hex_color
            shade.sort = sort
            shade.is_active = True
            shade.save()
        Shade.objects.filter(fabric=fabric).exclude(slug__in=keep).delete()


def sofa_products_queryset():
    return Product.objects.filter(
        Q(category__slug__in=SOFA_CATEGORY_SLUGS)
        | Q(category__parent__slug='divany')
    ).distinct()


def is_sofa_category_key(cat_key: str) -> bool:
    return cat_key in SOFA_SUBCATEGORY_SLUGS


def attach_sofa_palette(
    product: Product,
    options: dict[str, ProductColorOption] | None = None,
    *,
    image_paths: dict[str, str] | None = None,
    replace_file=None,
) -> int:
    """
    Прив'язує повну палітру до дивана.
    image_paths — опційні шляхи seed-медіа; без шляху кружечок лишається без нового фото.
    """
    if options is None:
        options = ensure_color_options()
    image_paths = image_paths or {}
    keep_ids = {options[slug].id for slug, *_ in SOFA_COLOR_PALETTE if slug in options}
    ProductColor.objects.filter(product=product).exclude(color_id__in=keep_ids).delete()

    created_or_updated = 0
    for slug, _uk, _ru, _hex, sort in SOFA_COLOR_PALETTE:
        option = options[slug]
        color_obj, _ = ProductColor.objects.get_or_create(
            product=product,
            color=option,
            defaults={
                'sort': sort,
                'is_active': True,
            },
        )
        color_obj.sort = sort
        color_obj.is_active = True
        path = image_paths.get(slug)
        if path and replace_file is not None:
            replace_file(
                color_obj.image,
                path,
                dest_name=f'{product.slug}-{slug}.webp',
            )
        color_obj.save()
        created_or_updated += 1
    return created_or_updated


def sync_all_sofa_colors() -> tuple[int, int]:
    """Повертає (кількість options, кількість product-color зв'язків)."""
    options = ensure_color_options()
    sync_fabric_shades()
    linked = 0
    for product in sofa_products_queryset():
        linked += attach_sofa_palette(product, options)
    return len(options), linked
