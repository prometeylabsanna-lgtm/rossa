from catalog.models import Category, Product
from catalog.selectors import apply_sort, products_in_category, search_products, visible_products
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
    parent = None
    node = None
    for slug in slugs:
        node = get_object_or_404(Category, slug=slug, parent=parent, is_active=True)
        parent = node
    return node


def catalog_index(request):
    categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by('sort')
    return render(request, 'catalog/index.html', {
        'categories': categories,
        'breadcrumbs': _breadcrumbs([(_('Головна'), '/'), (_('Продукція'), None)]),
        'seo_title': _('Продукція — ROSSA'),
        'seo_description': _('Дивани, ліжка та пуфи власного виробництва.'),
        'canonical_url': request.build_absolute_uri(),
    })


def _render_listing(request, category, crumbs):
    qs = products_in_category(category) if category else visible_products()
    if request.GET.get('available') == '1':
        qs = qs.filter(is_available=True)
    sort = request.GET.get('sort', 'popular')
    qs = apply_sort(qs, sort)
    page_size = settings.CATALOG_PAGE_SIZE
    offset = int(request.GET.get('offset', 0) or 0)
    total = qs.count()
    products = list(qs[offset:offset + page_size])
    next_offset = offset + page_size
    has_more = next_offset < total
    children = []
    parent_all_url = None
    if category:
        if category.parent:
            children = list(category.parent.children.filter(is_active=True))
            parent_all_url = category.parent.get_absolute_url()
        else:
            children = list(category.children.filter(is_active=True))
            parent_all_url = category.get_absolute_url()
    ctx = {
        'category': category,
        'products': products,
        'total': total,
        'sort': sort,
        'has_more': has_more,
        'next_offset': next_offset,
        'children': children,
        'parent_all_url': parent_all_url,
        'breadcrumbs': crumbs,
        'seo_title': (category.seo_title if category and category.seo_title else (category.name if category else 'Каталог')) + ' — ROSSA',
        'seo_description': (category.seo_description or category.intro) if category else 'Каталог ROSSA',
        'canonical_url': request.build_absolute_uri(request.path),
    }
    template = 'partials/product_more.html' if request.htmx else 'catalog/category.html'
    return render(request, template, ctx)


def category_page(request, path):
    slugs = [p for p in path.strip('/').split('/') if p]
    if not slugs:
        raise Http404()
    category = _category_by_path(slugs)
    crumbs = [(_('Головна'), '/'), (_('Продукція'), '/katalog/')]
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
    related_qs = products_in_category(product.category).exclude(pk=product.pk)
    if related_qs.count() < 3 and product.category.parent:
        related_qs = products_in_category(product.category.parent).exclude(pk=product.pk)
    related_qs = related_qs[:3]
    crumbs = [(_('Головна'), '/')]
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
