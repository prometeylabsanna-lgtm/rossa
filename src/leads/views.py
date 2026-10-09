from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from leads.forms import ContactForm, OrderForm, PartnershipForm
from leads.idempotency import claim_idempotency_key, release_idempotency_key
from leads.rate_limit import allow_lead_post
from leads.services import current_lang, notify_manager


def _ok_redirect(request, url_name):
    if request.htmx:
        response = HttpResponse()
        response['HX-Redirect'] = reverse(url_name)
        return response
    return redirect(url_name)


def _rate_limited(request):
    return HttpResponse('Too Many Requests', status=429, headers={'Retry-After': '60'})


def _save_lead_once(request, form, *, notify_subject, notify_body):
    """Зберігає лід один раз на idempotency_key; дублікат → thanks без повторного save."""
    if getattr(form, 'honeypot_tripped', lambda: False)():
        # Бот заповнив пастку — імітуємо успіх без запису в БД.
        return _ok_redirect(request, 'core:thanks')
    token = form.cleaned_data.get('idempotency_key', '')
    if not claim_idempotency_key(token):
        return _ok_redirect(request, 'core:thanks')
    try:
        obj = form.save(commit=False)
        obj.language = current_lang()
        obj.save()
    except Exception:
        release_idempotency_key(token)
        raise
    notify_manager(notify_subject(obj), notify_body(obj))
    return _ok_redirect(request, 'core:thanks')


@require_POST
def order_submit(request):
    if not allow_lead_post(request):
        return _rate_limited(request)
    form = OrderForm(request.POST)
    if form.is_valid():
        return _save_lead_once(
            request,
            form,
            notify_subject=lambda obj: f'ROSSA замовлення: {obj.product_name}',
            notify_body=lambda obj: (
                f'Модель: {obj.product_name}\n'
                f'Тканина: {obj.fabric_name}\n'
                f'Відтінок: {obj.shade_name}\n'
                f'Ціна: {obj.price} грн\n'
                f'Артикул: {obj.sku}\n'
                f'ПІБ: {obj.name}\n'
                f'Телефон: {obj.phone}\n'
                f'E-mail: {obj.email}\n'
                f'Отримання: {obj.get_fulfillment_display()}\n'
                f'Коментар: {obj.comment}\n'
            ),
        )
    return render(request, 'leads/order_form.html', {
        'form': form,
        'product': type('P', (), {'name': form.data.get('product_name', '')})(),
        'price': form.data.get('price', ''),
    }, status=400)


@require_POST
def partnership_submit(request):
    from core.models import CollabPage

    if not allow_lead_post(request):
        return _rate_limited(request)
    page = CollabPage.load()
    form = PartnershipForm(request.POST, page=page)
    if form.is_valid():
        return _save_lead_once(
            request,
            form,
            notify_subject=lambda obj: f'ROSSA співпраця: {obj.name}',
            notify_body=lambda obj: (
                f'Ім’я: {obj.name}\n'
                f'Телефон: {obj.phone}\n'
                f'E-mail: {obj.email}\n'
                f'Місто: {obj.city}\n'
                f'Повідомлення: {obj.message}\n'
            ),
        )
    return render(request, 'leads/partnership_form.html', {
        'form': form,
        'page': page,
    }, status=400)


@require_POST
def contact_submit(request):
    if not allow_lead_post(request):
        return _rate_limited(request)
    form = ContactForm(request.POST)
    if form.is_valid():
        return _save_lead_once(
            request,
            form,
            notify_subject=lambda obj: f'ROSSA контакти: {obj.name}',
            notify_body=lambda obj: (
                f'Ім’я: {obj.name}\nТелефон: {obj.phone}\nПовідомлення: {obj.message}\n'
            ),
        )
    return render(request, 'leads/contact_form.html', {'form': form}, status=400)
