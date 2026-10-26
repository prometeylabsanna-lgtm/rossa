"""Фід товарів для Google Merchant Center (RSS 2.0)."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

from django.http import HttpResponse
from django.urls import reverse
from django.utils import translation
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from catalog.selectors import visible_products

G_NS = 'http://base.google.com/ns/1.0'
ET.register_namespace('g', G_NS)

BRAND_FALLBACK = 'Rossa'
MAX_ADDITIONAL_IMAGES = 10
DESCRIPTION_LIMIT = 5000
TITLE_LIMIT = 150
ID_LIMIT = 50

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


def _g(tag: str) -> str:
    return f'{{{G_NS}}}{tag}'


def _add(parent: ET.Element, tag: str, value: str) -> None:
    element = ET.SubElement(parent, tag)
    element.text = value


def _feed_id(product) -> str:
    sku = (getattr(product, 'sku', '') or '').strip()
    if sku:
        return sku[:ID_LIMIT]
    return str(product.pk)


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


def _absolute_image(request, image) -> str:
    if not image:
        return ''
    try:
        url = image.url
    except ValueError:
        return ''
    return request.build_absolute_uri(url)


def _product_image_urls(request, product) -> list[str]:
    urls: list[str] = []
    main = _absolute_image(request, product.default_image)
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
            url = _absolute_image(request, image)
            if url:
                urls.append(url)
    return urls


def _price_uah(product) -> str:
    # Та сама «ціна від», що в каталозі: мінімум цін тканин або базова.
    return f'{int(product.min_price):.2f} UAH'


def _append_item(channel: ET.Element, request, product) -> None:
    item = ET.SubElement(channel, 'item')
    _add(item, _g('id'), _feed_id(product))
    title = plain_text(product.name_uk, limit=TITLE_LIMIT) or str(product.pk)
    _add(item, 'title', title)
    _add(item, 'description', plain_text(product.description_uk) or title)
    _add(
        item,
        'link',
        request.build_absolute_uri(
            reverse('catalog:product', kwargs={'slug': product.slug}),
        ),
    )
    image_link, extra = cap_image_urls(_product_image_urls(request, product))
    if image_link:
        _add(item, _g('image_link'), image_link)
    for url in extra:
        _add(item, _g('additional_image_link'), url)
    _add(item, _g('price'), _price_uah(product))
    _add(
        item,
        _g('availability'),
        'in_stock' if product.is_available else 'out_of_stock',
    )
    _add(item, _g('condition'), 'new')
    _add(item, _g('brand'), _brand(product))
    _add(item, _g('product_type'), _product_type(product.category))


def render_google_merchant_xml(request) -> bytes:
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    _add(channel, 'title', 'ROSSA')
    _add(channel, 'link', request.build_absolute_uri('/'))
    _add(channel, 'description', 'Каталог меблів ROSSA')
    for product in visible_products().order_by('pk'):
        _append_item(channel, request, product)
    return ET.tostring(rss, encoding='utf-8', xml_declaration=True)


@cache_page(60 * 30)
@require_GET
def google_merchant_feed(request):
    with translation.override('uk'):
        body = render_google_merchant_xml(request)
    return HttpResponse(body, content_type='application/xml; charset=utf-8')
