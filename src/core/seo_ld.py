"""JSON-LD: Organization, WebSite, BreadcrumbList, Product+Offer. Без FAQPage."""

from __future__ import annotations

import json
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from core.seo import (
    BRAND,
    _url_name,
    absolute_media,
    absolute_url,
    plain_text,
    public_base,
    public_contacts,
    rewrite_nationwide_delivery,
)

CONTENT_URL_NAMES = frozenset(
    {'about', 'collab', 'contacts', 'delivery', 'offer', 'privacy', 'cookies'}
)


def json_ld_script(data: dict) -> str:
    payload = json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, separators=(',', ':'))
    payload = (
        payload.replace('&', '\\u0026')
        .replace('<', '\\u003c')
        .replace('>', '\\u003e')
        .replace('\u2028', '\\u2028')
        .replace('\u2029', '\\u2029')
    )
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


def build_graph(context) -> dict:
    request = context['request']
    base = public_base(request)
    site = context.get('site_settings')
    graph = [_organization(request, site), _website(base)]
    crumbs = _breadcrumbs(context, request)
    if crumbs is not None:
        graph.append(crumbs)
    product = _product_node(context, request)
    if product is not None:
        graph.append(product)
    return {'@context': 'https://schema.org', '@graph': graph}


def _organization(request, site) -> dict:
    base = public_base(request)
    node = {
        '@type': 'Organization',
        '@id': f'{base}/#organization',
        'name': BRAND,
        'url': f'{base}/',
    }
    logo = getattr(site, 'logo', None) if site is not None else None
    if logo:
        try:
            node['logo'] = absolute_media(request, logo.url)
        except ValueError:
            pass
    contacts = public_contacts()
    if contacts['phone']:
        node['telephone'] = contacts['phone']
    if contacts['email']:
        node['email'] = contacts['email']
    if contacts['address']:
        node['address'] = {
            '@type': 'PostalAddress',
            'streetAddress': contacts['address'],
            'addressCountry': 'UA',
        }
    if contacts['same_as']:
        node['sameAs'] = list(contacts['same_as'])
    return node


def _website(base: str) -> dict:
    return {
        '@type': 'WebSite',
        '@id': f'{base}/#website',
        'name': BRAND,
        'url': f'{base}/',
        'inLanguage': ['uk-UA', 'ru-RU'],
        'publisher': {'@id': f'{base}/#organization'},
    }


def _crumb_list(items: list[tuple[str, str]]) -> dict:
    return {
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': index, 'name': name, 'item': url}
            for index, (name, url) in enumerate(items, start=1)
        ],
    }


def _home_crumb(request) -> tuple[str, str]:
    return (gettext('Головна'), absolute_url(reverse('core:home'), request))


def _catalog_crumb(request) -> tuple[str, str]:
    return (gettext('Каталог'), absolute_url(reverse('catalog:index'), request))


def _breadcrumbs(context, request):
    url_name = _url_name(request)
    if url_name == 'product' and context.get('product') is not None:
        return _product_crumbs(context['product'], request)
    if url_name == 'category' and context.get('category') is not None:
        items = [_home_crumb(request), _catalog_crumb(request)]
        items.extend(_category_chain(context['category'], request))
        return _crumb_list(items)
    view_name = getattr(request.resolver_match, 'view_name', '') or ''
    if view_name == 'catalog:index':
        return _crumb_list([_home_crumb(request), _catalog_crumb(request)])
    if url_name in CONTENT_URL_NAMES:
        title = _content_title(context, url_name)
        if not title:
            return None
        canonical = context.get('canonical_url') or absolute_url(request.path, request)
        return _crumb_list([_home_crumb(request), (title, canonical)])
    # Fallback: HTML breadcrumbs з views
    crumbs = context.get('breadcrumbs') or []
    if len(crumbs) >= 2:
        items = []
        for crumb in crumbs:
            label = plain_text(crumb.get('label') or '')
            if not label:
                continue
            url = crumb.get('url')
            if url:
                items.append((label, absolute_url(url, request)))
            else:
                items.append((label, absolute_url(request.path, request)))
        if len(items) >= 2:
            return _crumb_list(items)
    return None


def _category_chain(category, request) -> list[tuple[str, str]]:
    base = public_base(request)
    chain = []
    node = category
    while node:
        chain.append(node)
        node = node.parent
    return [(n.name, base + n.get_absolute_url()) for n in reversed(chain)]


def _product_crumbs(product, request) -> dict:
    items = [_home_crumb(request), _catalog_crumb(request)]
    if product.category_id:
        items.extend(_category_chain(product.category, request))
    items.append((product.name, absolute_url(product.get_absolute_url(), request)))
    return _crumb_list(items)


def _content_title(context, url_name: str) -> str:
    page = context.get('page')
    if page is not None:
        title = plain_text(getattr(page, 'title', '') or '')
        if title:
            return title
    defaults = {
        'about': gettext('Про нас'),
        'collab': gettext('Співпраця'),
        'contacts': gettext('Контакти'),
        'delivery': gettext('Отримання'),
        'offer': gettext('Публічна оферта'),
        'privacy': gettext('Політика конфіденційності'),
        'cookies': 'Cookies',
    }
    return defaults.get(url_name, '')


def _product_node(context, request):
    if _url_name(request) != 'product':
        return None
    product = context.get('product')
    if product is None:
        return None
    canonical = absolute_url(product.get_absolute_url(), request)
    images = []
    main = context.get('main_image')
    if main:
        try:
            images.append(absolute_media(request, main.url))
        except (ValueError, AttributeError):
            pass
    gallery = context.get('gallery') or []
    for shot in gallery:
        try:
            url = absolute_media(request, shot.url)
        except (ValueError, AttributeError):
            continue
        if url and url not in images:
            images.append(url)
    if not images:
        cover = getattr(product, 'cover_image', None) or getattr(product, 'default_image', None)
        if cover:
            try:
                images.append(absolute_media(request, cover.url))
            except (ValueError, AttributeError):
                pass

    price = context.get('price')
    if price is None:
        pricing = product.resolve_prices()
        price = pricing.get('current')
    try:
        price_dec = Decimal(str(price)).quantize(Decimal('0.01'))
    except Exception:
        price_dec = Decimal(str(product.base_price)).quantize(Decimal('0.01'))

    availability = (
        'https://schema.org/InStock'
        if getattr(product, 'is_available', True)
        else 'https://schema.org/OutOfStock'
    )
    node = {
        '@type': 'Product',
        'name': product.name,
        'url': canonical,
        'brand': {'@type': 'Brand', 'name': BRAND},
        'offers': {
            '@type': 'Offer',
            'url': canonical,
            'priceCurrency': 'UAH',
            'price': f'{price_dec}',
            'availability': availability,
        },
    }
    sku = plain_text(context.get('sku') or getattr(product, 'sku', '') or '')
    if sku:
        node['sku'] = sku
    description = rewrite_nationwide_delivery(
        plain_text(
            getattr(product, 'seo_description', '') or getattr(product, 'description', '') or ''
        )
    )
    if description:
        node['description'] = description
    if images:
        node['image'] = images
    return node
