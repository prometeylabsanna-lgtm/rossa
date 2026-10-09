from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


def _admin_prefix() -> str:
    return f'/{settings.ADMIN_URL.strip("/")}/'


def build_unfold_navigation() -> list[dict]:
    prefix = _admin_prefix()
    return [
        {
            'title': _('Сторінки сайту'),
            'separator': True,
            'collapsible': True,
            'items': [
                {
                    'title': _('Головна'),
                    'icon': 'home',
                    'link': reverse_lazy('admin:core_homepage_changelist'),
                    'active': lambda request: (
                        f'{prefix}core/homepage/' in request.path
                        or f'{prefix}core/valueprop/' in request.path
                    ),
                    'items': [
                        {
                            'title': _('Переваги на головній'),
                            'icon': 'star',
                            'link': reverse_lazy('admin:core_valueprop_changelist'),
                        },
                    ],
                },
                {
                    'title': _('Про нас'),
                    'icon': 'info',
                    'link': reverse_lazy('admin:core_aboutpage_changelist'),
                },
                {
                    'title': _('Співпраця'),
                    'icon': 'handshake',
                    'link': reverse_lazy('admin:core_collabpage_changelist'),
                },
                {
                    'title': _('Контакти'),
                    'icon': 'call',
                    'link': reverse_lazy('admin:core_contactspage_changelist'),
                },
                {
                    'title': _('Доставка'),
                    'icon': 'local_shipping',
                    'link': reverse_lazy('admin:core_deliverypage_changelist'),
                },
                {
                    'title': _('Оферта'),
                    'icon': 'description',
                    'link': reverse_lazy('admin:core_offerpage_changelist'),
                },
                {
                    'title': _('Політика конфіденційності'),
                    'icon': 'policy',
                    'link': reverse_lazy('admin:core_privacypage_changelist'),
                },
                {
                    'title': _('Cookies'),
                    'icon': 'cookie',
                    'link': reverse_lazy('admin:core_cookiespage_changelist'),
                },
                {
                    'title': _('Шапка сайту'),
                    'icon': 'web_asset',
                    'link': reverse_lazy('admin:core_headersettings_changelist'),
                },
                {
                    'title': _('Підвал сайту'),
                    'icon': 'vertical_align_bottom',
                    'link': reverse_lazy('admin:core_footersettings_changelist'),
                },
            ],
        },
        {
            'title': _('Каталог'),
            'separator': True,
            'collapsible': True,
            'items': [
                {
                    'title': _('Каталог товарів'),
                    'icon': 'inventory_2',
                    'link': reverse_lazy('admin:catalog_product_changelist'),
                },
                {
                    'title': _('Категорії'),
                    'icon': 'category',
                    'link': reverse_lazy('admin:catalog_category_changelist'),
                },
                {
                    'title': _('Характеристики'),
                    'icon': 'list_alt',
                    'link': reverse_lazy('admin:catalog_characteristic_changelist'),
                },
                {
                    'title': _('Стандартні кольори'),
                    'icon': 'palette',
                    'link': reverse_lazy('admin:catalog_productcoloroption_changelist'),
                },
                {
                    'title': _('Тканини'),
                    'icon': 'texture',
                    'link': reverse_lazy('admin:catalog_fabric_changelist'),
                },
                {
                    'title': _('Відтінки'),
                    'icon': 'colorize',
                    'link': reverse_lazy('admin:catalog_shade_changelist'),
                },
            ],
        },
        {
            'title': _('Заявки'),
            'separator': True,
            'collapsible': True,
            'items': [
                {
                    'title': _('Замовлення'),
                    'icon': 'shopping_bag',
                    'link': reverse_lazy('admin:leads_orderrequest_changelist'),
                },
                {
                    'title': _('Заявки на співпрацю'),
                    'icon': 'groups',
                    'link': reverse_lazy('admin:leads_partnershiplead_changelist'),
                },
                {
                    'title': _('Заявки з контактів'),
                    'icon': 'mail',
                    'link': reverse_lazy('admin:leads_contactlead_changelist'),
                },
            ],
        },
    ]
