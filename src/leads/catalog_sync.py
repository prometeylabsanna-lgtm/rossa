"""Сверка снапшота заявки з актуальним товаром каталогу."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MSG_PRODUCT_UNAVAILABLE = _('Товар недоступний для замовлення')


def _fabric_matches(fabric, label: str) -> bool:
    if not fabric or not label:
        return False
    if fabric.name == label:
        return True
    return label in {fabric.name_uk, fabric.name_ru}


def resolve_order_catalog_snapshot(*, product_slug: str, fabric_name: str = '') -> dict:
    """
    Повертає серверні product_name / price / sku / fabric_name.
    Кидає ValidationError лише якщо товар невидимий (is_active=False).
    is_available блокується на UI («Замовити»); консультація / preorder — дозволені.
    """
    from catalog.models import Fabric, Product

    slug = (product_slug or '').strip()
    if not slug:
        raise ValidationError(MSG_PRODUCT_UNAVAILABLE, code='product_unavailable')

    product = (
        Product.objects.filter(is_active=True, slug=slug)
        .prefetch_related('fabric_prices__fabric')
        .first()
    )
    if product is None:
        raise ValidationError(MSG_PRODUCT_UNAVAILABLE, code='product_unavailable')

    fabric_label = (fabric_name or '').strip()
    selected_fabric = None
    if fabric_label:
        for fp in product.fabric_prices.all():
            if fp.fabric and fp.fabric.is_active and _fabric_matches(fp.fabric, fabric_label):
                selected_fabric = fp.fabric
                break
        if selected_fabric is None:
            for fabric in Fabric.objects.filter(is_active=True):
                if _fabric_matches(fabric, fabric_label):
                    selected_fabric = fabric
                    break

    if selected_fabric is not None:
        price = product.price_for_fabric(selected_fabric)
        match = next(
            (fp for fp in product.fabric_prices.all() if fp.fabric_id == selected_fabric.id),
            None,
        )
        sku = (match.sku if match and match.sku else product.sku) or ''
        fabric_out = selected_fabric.name
    else:
        price = product.min_price
        sku = product.sku or ''
        fabric_out = fabric_label

    return {
        'product_name': product.name,
        'product_slug': product.slug,
        'price': int(price),
        'sku': sku,
        'fabric_name': fabric_out,
    }
