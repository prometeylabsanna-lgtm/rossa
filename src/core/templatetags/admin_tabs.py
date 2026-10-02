from django import template
from django.template.loader import render_to_string
from unfold.templatetags.unfold import (
    _count_errors_in_general,
    _count_errors_in_inline,
    _get_tabs_list,
    tabs as tabs_filter,
)

register = template.Library()


@register.simple_tag(name='tab_list', takes_context=True)
def tab_list(context, page, opts=None):
    """Unfold tab_list + fieldset tabs as top-level (Контент ukr/ru замість Загальне)."""
    inlines_list = []
    datasets_list = []
    data = {
        'is_popup': context.get('is_popup'),
        'tabs_list': _get_tabs_list(context, page, opts),
        'fieldset_tabs': [],
    }

    adminform = context.get('adminform')
    if adminform:
        data['fieldset_tabs'] = tabs_filter(adminform)

    if adminform and context.get('inline_admin_formsets'):
        data['error_count'] = _count_errors_in_general(
            adminform,
            context['inline_admin_formsets'],
        )
        for inline in context.get('inline_admin_formsets') or []:
            inline.error_count = _count_errors_in_inline(inline)

    if page == 'changeform' and len(data.get('tabs_list') or []) == 0:
        for inline in context.get('inline_admin_formsets') or []:
            if opts and getattr(inline.opts, 'tab', False):
                inlines_list.append(inline)

        if inlines_list:
            data['inlines_list'] = inlines_list

        for dataset in context.get('datasets') or []:
            if dataset and getattr(dataset, 'tab', False):
                datasets_list.append(dataset)

        if datasets_list:
            data['datasets_list'] = datasets_list

        # Якщо є вкладені fieldset-вкладки без інлайнів — все одно показуємо tab bar
        if data['fieldset_tabs'] and not inlines_list and not datasets_list:
            data['inlines_list'] = []

    return render_to_string(
        'unfold/helpers/tab_list.html',
        request=context['request'],
        context=data,
    )
