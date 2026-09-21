from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from leads.forms import ContactForm, OrderForm, PartnershipForm
from leads.services import current_lang, notify_manager


def _ok_redirect(request, url_name):
    if request.htmx:
        response = HttpResponse()
        response['HX-Redirect'] = reverse(url_name)
        return response
    return redirect(url_name)


@require_POST
def order_submit(request):
    form = OrderForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.language = current_lang()
        obj.save()
        notify_manager(
            f'ROSSA замовлення: {obj.product_name}',
            (
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
        return _ok_redirect(request, 'core:thanks')
    return render(request, 'leads/order_form.html', {
        'form': form,
        'product': type('P', (), {'name': form.data.get('product_name', '')})(),
        'price': form.data.get('price', ''),
    }, status=400)


@require_POST
def partnership_submit(request):
    form = PartnershipForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.language = current_lang()
        obj.save()
        notify_manager(
            f'ROSSA співпраця: {obj.company}',
            (
                f'Компанія: {obj.company}\n'
                f'Ім’я: {obj.name}\n'
                f'Телефон: {obj.phone}\n'
                f'E-mail: {obj.email}\n'
                f'Місто: {obj.city}\n'
                f'Тип: {obj.get_collab_type_display()}\n'
                f'Повідомлення: {obj.message}\n'
            ),
        )
        return _ok_redirect(request, 'core:thanks')
    return render(request, 'leads/partnership_form.html', {
        'form': form,
        'form_title': form.data.get('company', ''),
        'page': type('P', (), {'form_title': ''})(),
    }, status=400)


@require_POST
def contact_submit(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.language = current_lang()
        obj.save()
        notify_manager(
            f'ROSSA контакти: {obj.name}',
            f'Ім’я: {obj.name}\nТелефон: {obj.phone}\nПовідомлення: {obj.message}\n',
        )
        return _ok_redirect(request, 'core:thanks')
    return render(request, 'leads/contact_form.html', {'form': form}, status=400)
