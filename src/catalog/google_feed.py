"""Фід товарів для Google Merchant Center (RSS 2.0)."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urljoin

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.utils import translation
from django.views.decorators.http import require_GET

from catalog.selectors import visible_products

G_NS = 'http://base.google.com/ns/1.0'
ET.register_namespace('g', G_NS)

BRAND_FALLBACK = 'Rossa'
MAX_ADDITIONAL_IMAGES = 10
DESCRIPTION_LIMIT = 5000
TITLE_LIMIT = 150
_PRICE_STEP = Decimal('0.01')

FEED_CACHE_KEY = 'catalog:google_merchant_feed:v1'
FEED_CACHE_TIMEOUT = 30 * 60

# Таксономія Google Product Category: ID за slug. Далі піднімаємось до батьків.
GOOGLE_PRODUCT_CATEGORY_BY_SLUG = {
    'divany': '460',  # Furniture > Sofas
    'modulni': '460',  # Furniture > Sofas
    'kutovi': '460',  # Furniture > Sofas
    'pryami': '460',  # Furniture > Sofas
    'yevroknyzhky': '460',  # Furniture > Sofas
    'lizhka': '505764',  # Furniture > Beds & Accessories > Beds & Bed Frames
    'pufy': '458',  # Furniture > Ottomans
}
# Жоден slug у ланцюжку категорій не збігся.
DEFAULT_GOOGLE_PRODUCT_CATEGORY = '436'  # Furniture

_SCRIPT_RE = re.compile(
    r'<(script|style)\b[^>]*>.*?</\1>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r'<[^>]+>')
_ILLEGAL_XML_RE = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F]')
_WS_RE = re.compile(r'\s+')


def plain_text(value: str, *, limit: int = DESCRIPTION_LIMIT) -> str:
    """HTML → текст: теги прибрані, сутності розкриті, пробіли згорнуті."""
    text = _SCRIPT_RE.sub(' ', value or '')
    text = _TAG_RE.sub(' ', text)
    text = html.unescape(text)
    text = _ILLEGAL_XML_RE.sub('', text)
    text = _WS_RE.sub(' ', text).strip()
    if len(text) > limit:
        return text[:limit].rstrip()
    return text


def cap_image_urls(urls: list[str]) -> tuple[str | None, list[str]]:
    """Перше фото — image_link, далі не більше 10 унікальних additional."""
    unique: list[str] = []
    for url in urls:
        if url and url not in unique:
            unique.append(url)
    if not unique:
        return None, []
    return unique[0], unique[1:1 + MAX_ADDITIONAL_IMAGES]


def absolute_url(path: str) -> str:
    """Абсолютний URL від settings.SITE_URL. Уже абсолютний path лишається як є."""
    base = f"{(settings.SITE_URL or '').strip().rstrip('/')}/"
    return urljoin(base, path or '')


def format_price_uah(amount) -> str:
    """Сума з рівно двома знаками після коми та кодом UAH."""
    quantized = _quantized_price(amount)
    return f'{quantized} UAH'


def google_product_category_id(category) -> str:
    """ID категорії Google: slug вузла, потім батьки, інакше Furniture."""
    seen: set[int] = set()
    node = category
    while node is not None and node.pk not in seen:
        seen.add(node.pk)
        mapped = GOOGLE_PRODUCT_CATEGORY_BY_SLUG.get(node.slug)
        if mapped:
            return mapped
        node = node.parent
    return DEFAULT_GOOGLE_PRODUCT_CATEGORY


def invalidate_google_merchant_feed_cache(sender=None, **kwargs) -> None:
    cache.delete(FEED_CACHE_KEY)


def _g(tag: str) -> str:
    return f'{{{G_NS}}}{tag}'


def _add(parent: ET.Element, tag: str, value: str) -> None:
    element = ET.SubElement(parent, tag)
    element.text = value


def _feed_id(product) -> str:
    return f'rossa-{product.pk}'


def _quantized_price(amount) -> Decimal:
    # Грошовий формат: рівно 2 знаки, ROUND_HALF_UP.
    return Decimal(str(amount)).quantize(_PRICE_STEP, rounding=ROUND_HALF_UP)


def _brand(product) -> str:
    if not any(field.name == 'brand' for field in product._meta.concrete_fields):
        return BRAND_FALLBACK
    value = getattr(product, 'brand', None)
    if isinstance(value, str) and value.strip():
        return plain_text(value, limit=70)
    if value not in (None, ''):
        text = plain_text(str(value), limit=70)
        if text:
            return text
    return BRAND_FALLBACK


def _product_type(category) -> str:
    names: list[str] = []
    seen: set[int] = set()
    node = category
    while node is not None and node.pk not in seen:
        seen.add(node.pk)
        label = (node.name_uk or '').strip()
        if label:
            names.append(label)
        node = node.parent
    names.reverse()
    return ' > '.join(names)


def _absolute_media(image) -> str:
    if not image:
        return ''
    try:
        url = image.url
    except ValueError:
        return ''
    if not url:
        return ''
    return absolute_url(url)


def _product_image_urls(product) -> list[str]:
    urls: list[str] = []
    main = _absolute_media(product.default_image)
    if main:
        urls.append(main)
    for color in product.colors.all():
        if not color.is_active:
            continue
        gallery = [
            row.image
            for row in product.gallery_for_color(color.color_id)
            if row.image
        ]
        images = gallery or ([color.image] if color.image else [])
        for image in images:
            url = _absolute_media(image)
            if url:
                urls.append(url)
    return urls


def _append_item(channel: ET.Element, product) -> None:
    image_link, extra = cap_image_urls(_product_image_urls(product))
    pricing = product.resolve_prices()
    raw_current = pricing.get('current')
    if not image_link or raw_current is None:
        return
    current = _quantized_price(raw_current)
    if current <= 0:
        return
    regular = _quantized_price(pricing.get('regular') or raw_current)
    item = ET.SubElement(channel, 'item')
    _add(item, _g('id'), _feed_id(product))
    title = plain_text(product.name_uk, limit=TITLE_LIMIT) or str(product.pk)
    _add(item, 'title', title)
    _add(item, 'description', plain_text(product.description_uk) or title)
    _add(
        item,
        'link',
        absolute_url(reverse('catalog:product', kwargs={'slug': product.slug})),
    )
    _add(item, _g('image_link'), image_link)
    for url in extra:
        _add(item, _g('additional_image_link'), url)
    if pricing.get('on_sale') and regular > current:
        _add(item, _g('price'), format_price_uah(regular))
        _add(item, _g('sale_price'), format_price_uah(current))
    else:
        _add(item, _g('price'), format_price_uah(current))
    _add(
        item,
        _g('availability'),
        'in_stock' if product.is_available else 'out_of_stock',
    )
    _add(item, _g('condition'), 'new')
    _add(item, _g('brand'), _brand(product))
    sku = (getattr(product, 'sku', '') or '').strip()
    if sku:
        _add(item, _g('mpn'), sku)
    else:
        _add(item, _g('identifier_exists'), 'no')
    _add(item, _g('product_type'), _product_type(product.category))
    _add(item, _g('google_product_category'), google_product_category_id(product.category))


def render_google_merchant_xml() -> bytes:
    with translation.override('uk'):
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        _add(channel, 'title', 'ROSSA')
        _add(channel, 'link', absolute_url('/'))
        _add(channel, 'description', 'Каталог меблів ROSSA')
        for product in visible_products().order_by('pk'):
            _append_item(channel, product)
        return ET.tostring(rss, encoding='utf-8', xml_declaration=True)


@require_GET
def google_merchant_feed(request):
    body = cache.get(FEED_CACHE_KEY)
    if body is None:
        body = render_google_merchant_xml()
        cache.set(FEED_CACHE_KEY, body, FEED_CACHE_TIMEOUT)
    return HttpResponse(body, content_type='application/xml; charset=utf-8')
