"""Підкатегорії диванів у меню та каталозі."""

from __future__ import annotations

from catalog.models import Category

# slug, name_uk, name_ru, sort
SOFA_SUBCATEGORIES = (
    ('modulni', 'Модульні', 'Модульные', 0),
    ('kutovi', 'Кутові', 'Угловые', 1),
    ('pryami', 'Прямі', 'Прямые', 2),
    ('yevroknyzhky', 'Єврокнижки', 'Еврокнижки', 3),
)

SOFA_SUBCATEGORY_SLUGS = frozenset(slug for slug, *_ in SOFA_SUBCATEGORIES)


def ensure_sofa_parent() -> Category:
    sofas, _ = Category.objects.get_or_create(
        slug='divany',
        parent=None,
        defaults={
            'name_uk': 'Дивани',
            'name_ru': 'Диваны',
            'sort': 0,
            'is_active': True,
        },
    )
    sofas.name_uk = 'Дивани'
    sofas.name_ru = 'Диваны'
    sofas.sort = 0
    sofas.is_active = True
    sofas.save()
    return sofas


def ensure_sofa_subcategories(sofas: Category | None = None) -> dict[str, Category]:
    if sofas is None:
        sofas = ensure_sofa_parent()
    children: dict[str, Category] = {}
    keep = set(SOFA_SUBCATEGORY_SLUGS)
    for slug, uk, ru, sort in SOFA_SUBCATEGORIES:
        obj, _ = Category.objects.get_or_create(
            slug=slug,
            parent=sofas,
            defaults={
                'name_uk': uk,
                'name_ru': ru,
                'sort': sort,
                'is_active': True,
            },
        )
        obj.name_uk = uk
        obj.name_ru = ru
        obj.sort = sort
        obj.is_active = True
        obj.save()
        children[slug] = obj
    # Не видаляємо чужі підкатегорії — лише гарантуємо потрібні.
    _ = keep
    return children
