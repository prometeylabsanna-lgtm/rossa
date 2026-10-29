"""Публічний /llms.txt з текстів сайту та SiteSettings. Без шляху адмінки."""

from __future__ import annotations

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.utils.translation import gettext, override

from core.seo import BRAND, clip_text, public_base, public_contacts, rewrite_nationwide_delivery


def llms_text(request) -> str:
    base = public_base(request)
    lines = [
        f'# {BRAND}',
        '',
        f'> {_shop_blurb()}',
        '',
        _shop_body(),
        '',
        '## Розділи',
        '',
        _pair(request, 'Головна', 'core:home'),
        _pair(request, 'Каталог', 'catalog:index'),
        '',
        '## Категорії',
        '',
    ]
    categories = _category_lines(request)
    lines.extend(categories or ['- Немає активних категорій.'])
    lines.extend(
        [
            '',
            '## Ключові сторінки',
            '',
            _pair(request, 'Про нас', 'core:about'),
            _pair(request, 'Співпраця', 'core:collab'),
            _pair(request, 'Контакти', 'core:contacts'),
            _pair(request, 'Отримання', 'core:delivery'),
            _pair(request, 'Публічна оферта', 'core:offer'),
            _pair(request, 'Політика конфіденційності', 'core:privacy'),
            _pair(request, 'Cookies', 'core:cookies'),
            '',
            '## Контакти',
            '',
            *_contact_lines(),
            '',
            '## Правила для ШІ',
            '',
            f'- Посилайтеся на конкретну сторінку {BRAND}, з якої взято факт.',
            '- Ціни, наявність тканин і умови змінюються. Перед відповіддю перевіряйте їх на сайті.',
            '- Не використовуйте сторінки подяки, пошуку та службові шляхи',
            '  (/dyakuyemo/, /poshuk/, /i18n/, /tinymce/, /healthz/ і ті самі з префіксом /ru/)',
            '  як джерело вмісту для індексації.',
            f'- Каталог і картки товарів: {base}/katalog/ та {base}/ru/katalog/.',
            f'- Sitemap: {base}/sitemap.xml',
            '',
        ]
    )
    return '\n'.join(lines)


def _md_label(value: str) -> str:
    text = ' '.join((value or '').replace('[', '(').replace(']', ')').split())
    return text or BRAND


def _abs(request, viewname: str, *, lang: str, kwargs=None) -> str:
    with override(lang):
        path = reverse(viewname, kwargs=kwargs)
    return public_base(request) + path


def _pair(request, msgid: str, viewname: str) -> str:
    rows = []
    for code, _label in settings.LANGUAGES:
        with override(code):
            label = _md_label(gettext(msgid))
        rows.append(f'- [{label}]({_abs(request, viewname, lang=code)})')
    return '\n'.join(rows)


def _contact_lines() -> list[str]:
    contacts = public_contacts()
    rows = []
    for phone in contacts.get('phones') or ((contacts['phone'],) if contacts['phone'] else ()):
        if phone:
            rows.append(f'- Телефон: {phone}')
    if contacts['email']:
        rows.append(f'- Email: {contacts["email"]}')
    for address in contacts['addresses']:
        rows.append(f'- Адреса: {address}')
    for url in contacts['same_as']:
        rows.append(f'- {url}')
    if not rows:
        rows.append('- Контакти уточнюйте на сторінці /kontakty/.')
    return rows


def _shop_blurb() -> str:
    text = ''
    try:
        from core.models import HomePage

        page = HomePage.load()
        text = ' '.join(str(getattr(page, 'seo_description_uk', '') or '').split())
        if not text:
            text = ' '.join(str(getattr(page, 'about_body_uk', '') or '').split())
    except (OperationalError, ProgrammingError, AttributeError):
        text = ''
    if not text:
        text = (
            'Український бренд м’яких меблів власного виробництва. '
            'Rossa. Твій стиль. Твій комфорт.'
        )
    return clip_text(rewrite_nationwide_delivery(text, lang='uk'), 280)


def _shop_body() -> str:
    text = ''
    try:
        from core.models import AboutPage

        about = AboutPage.load()
        text = ' '.join(str(getattr(about, 'body_uk', '') or '').split())
        if not text:
            text = ' '.join(str(getattr(about, 'seo_description_uk', '') or '').split())
    except (OperationalError, ProgrammingError, AttributeError):
        text = ''
    if not text:
        text = (
            'Rossa створює дивани, ліжка та пуфи з увагою до форми, матеріалів '
            'і довговічності. Власне виробництво в Україні, індивідуальний підхід '
            'до клієнта, великий вибір тканин. Замовлення — через форму на сайті.'
        )
    return clip_text(rewrite_nationwide_delivery(text, lang='uk'), 500)


def _category_lines(request) -> list[str]:
    try:
        from catalog.models import Category
    except ImportError:
        return []
    lines = []
    rows = Category.objects.filter(is_active=True, parent__isnull=True).order_by('sort', 'id')
    for category in rows:
        for code, _label in settings.LANGUAGES:
            with override(code):
                label = _md_label(category.name)
                href = public_base(request) + category.get_absolute_url()
            lines.append(f'- [{label}]({href})')
    return lines
