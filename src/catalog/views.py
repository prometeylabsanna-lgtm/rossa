from catalog.selectors import (
    apply_listing_filters,
    apply_sort,
    products_in_category,
    related_products,
    search_products,
    top_categories,
    visible_products,
)
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from leads.forms import OrderForm


def _breadcrumbs(items):
    out = []
    for i, (label, url) in enumerate(items):
        out.append({'label': label, 'url': url, 'has_next': i < len(items) - 1})
    return out


def _category_by_path(slugs):
    from catalog.models import Category

    parent = None
    node = None
    for slug in slugs:
        node = get_object_or_404(Category, slug=slug, parent=parent, is_active=True)
        parent = node
    return node


def _parse_int(value):
    try:
        if value in (None, ''):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _listing_query(request, **overrides):
    params = request.GET.copy()
    params.pop('offset', None)
    for key, value in overrides.items():
        if value in (None, ''):
            params.pop(key, None)
        else:
            params[key] = str(value)
    for key in list(params.keys()):
        if params.get(key) in (None, ''):
            params.pop(key, None)
    return params.urlencode()


def catalog_index(request):
    return _render_listing(
        request,
        category=None,
        crumbs=_breadcrumbs([(_('Головна'), '/'), (_('Каталог'), None)]),
        seo_title=_('Каталог — ROSSA'),
        seo_description=_('Дивани, ліжка та пуфи власного виробництва.'),
        intro=_('Дивани, ліжка та пуфи власного виробництва. Обирайте тканину та відтінок під ваш інтер’єр.'),
    )


def _render_listing(request, category, crumbs, seo_title=None, seo_description=None, intro=None):
    price_min = _parse_int(request.GET.get('price_min'))
    price_max = _parse_int(request.GET.get('price_max'))
    available = request.GET.get('available') == '1'
    sort = request.GET.get('sort', 'popular')
    cat_slug = (request.GET.get('cat') or '').strip()
    selected_cat = None

    if category:
        qs = products_in_category(category)
        qs, _unused_cat = apply_listing_filters(
            qs,
            price_min=price_min,
            price_max=price_max,
            available=available,
        )
        filter_categories = []
        if category.parent:
            children = list(category.parent.children.filter(is_active=True))
            parent_all_url = category.parent.get_absolute_url()
        else:
            children = list(category.children.filter(is_active=True))
            parent_all_url = category.get_absolute_url()
    else:
        qs = visible_products()
        qs, selected_cat = apply_listing_filters(
            qs,
            cat_slug=cat_slug,
            price_min=price_min,
            price_max=price_max,
            available=available,
        )
        filter_categories = list(top_categories())
        children = []
        parent_all_url = None

    qs = apply_sort(qs, sort)
    page_size = settings.CATALOG_PAGE_SIZE
    offset = int(request.GET.get('offset', 0) or 0)
    total = qs.count()
    products = list(qs[offset:offset + page_size])
    next_offset = offset + page_size
    has_more = next_offset < total
    listing_qs = _listing_query(request, sort=sort)

    if category:
        page_title = category.name
        page_seo_title = (
            (category.seo_title if category.seo_title else category.name) + ' — ROSSA'
        )
        page_seo_description = category.seo_description or category.intro or ''
        page_intro = category.intro or intro
    else:
        page_title = _('Каталог')
        page_seo_title = seo_title or (_('Каталог') + ' — ROSSA')
        page_seo_description = seo_description or _('Каталог ROSSA')
        page_intro = intro

    ctx = {
        'category': category,
        'products': products,
        'total': total,
        'sort': sort,
        'has_more': has_more,
        'next_offset': next_offset,
        'children': children,
        'parent_all_url': parent_all_url,
        'filter_categories': filter_categories,
        'selected_cat': selected_cat,
        'price_min': price_min if price_min is not None else '',
        'price_max': price_max if price_max is not None else '',
        'available': available,
        'listing_qs': listing_qs,
        'reset_url': request.path,
        'page_title': page_title,
        'page_intro': page_intro,
        'breadcrumbs': crumbs,
        'seo_title': page_seo_title,
        'seo_description': page_seo_description,
        'canonical_url': request.build_absolute_uri(request.path),
    }
    template = 'partials/product_more.html' if request.htmx else 'catalog/category.html'
    return render(request, template, ctx)


def category_page(request, path):
    slugs = [p for p in path.strip('/').split('/') if p]
    if not slugs:
        raise Http404()
    category = _category_by_path(slugs)
    crumbs = [(_('Головна'), '/'), (_('Каталог'), '/katalog/')]
    chain = []
    node = category
    while node:
        chain.append(node)
        node = node.parent
    for cat in reversed(chain):
        crumbs.append((cat.name, cat.get_absolute_url()))
    crumbs[-1] = (crumbs[-1][0], None)
    return _render_listing(request, category, _breadcrumbs(crumbs))


@require_GET
def product_detail(request, slug):
    product = get_object_or_404(
        visible_products(),
        slug=slug,
    )
    fabric_id = request.GET.get('fabric')
    shade_id = request.GET.get('shade')
    fabrics = [fp.fabric for fp in product.fabric_prices.all() if fp.fabric.is_active]
    if not fabrics:
        from catalog.models import Fabric
        fabrics = list(Fabric.objects.filter(is_active=True))
    selected_fabric = next((f for f in fabrics if str(f.id) == str(fabric_id)), None) or (fabrics[0] if fabrics else None)
    shades = list(selected_fabric.shades.filter(is_active=True)) if selected_fabric else []
    selected_shade = next((s for s in shades if str(s.id) == str(shade_id)), None) or (shades[0] if shades else None)
    price = product.price_for_fabric(selected_fabric) if selected_fabric else product.min_price
    images = []
    if selected_shade:
        images = [img for img in product.shade_images.all() if img.shade_id == selected_shade.id]
    main_image = images[0].image if images else product.default_image
    related_qs = related_products(product, limit=3)
    crumbs = [(_('Головна'), '/'), (_('Каталог'), '/katalog/')]
    if product.category.parent:
        crumbs.append((product.category.parent.name, product.category.parent.get_absolute_url()))
    crumbs.append((product.category.name, product.category.get_absolute_url()))
    crumbs.append((product.name, None))
    sku = ''
    if selected_fabric:
        match = next((fp for fp in product.fabric_prices.all() if fp.fabric_id == selected_fabric.id), None)
        sku = (match.sku if match and match.sku else product.sku)
    ctx = {
        'product': product,
        'fabrics': fabrics,
        'shades': shades,
        'selected_fabric': selected_fabric,
        'selected_shade': selected_shade,
        'price': price,
        'gallery': images,
        'main_image': main_image,
        'related': related_qs,
        'sku': sku,
        'form': OrderForm(initial={
            'product_name': product.name,
            'product_slug': product.slug,
            'fabric_name': selected_fabric.name if selected_fabric else '',
            'shade_name': selected_shade.name if selected_shade else '',
            'sku': sku,
            'price': price,
        }),
        'breadcrumbs': _breadcrumbs(crumbs),
        'seo_title': (product.seo_title or product.name) + ' — ROSSA',
        'seo_description': product.seo_description or (product.description or '')[:160],
        'canonical_url': request.build_absolute_uri(product.get_absolute_url()),
        'og_image': main_image.url if main_image else None,
    }
    if request.htmx:
        return render(request, 'partials/product_config.html', ctx)
    return render(request, 'catalog/product.html', ctx)


@require_GET
def search(request):
    q = request.GET.get('q', '')
    products = search_products(q)[:24]
    ctx = {
        'q': q,
        'products': products,
        'breadcrumbs': _breadcrumbs([(_('Головна'), '/'), (_('Пошук'), None)]),
        'seo_title': _('Пошук — ROSSA'),
        'seo_description': _('Пошук моделей ROSSA за назвою або артикулом.'),
        'canonical_url': request.build_absolute_uri(),
    }
    if request.htmx:
        return render(request, 'partials/search_results.html', ctx)
    return render(request, 'catalog/search.html', ctx)
