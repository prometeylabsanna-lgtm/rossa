from django.core.cache import cache
from django.db import models

from core.mixins import TimeStampedModel

PAGE_STYLES_CACHE_KEY = 'page_styles'
CHROME_STYLE_CACHE_KEY = 'chrome_style'


def clear_style_cache() -> None:
    cache.delete(PAGE_STYLES_CACHE_KEY)
    cache.delete(CHROME_STYLE_CACHE_KEY)


class PageStyle(TimeStampedModel):
    """Кольори контенту сторінки (між шапкою і підвалом). Порожні = дефолт сайту."""

    PAGE_HOME = 'home'
    PAGE_ABOUT = 'about'
    PAGE_COLLAB = 'collab'
    PAGE_CONTACTS = 'contacts'
    PAGE_DELIVERY = 'delivery'
    PAGE_OFFER = 'offer'
    PAGE_PRIVACY = 'privacy'
    PAGE_CATALOG = 'catalog'

    PAGE_CHOICES = (
        (PAGE_HOME, 'Головна'),
        (PAGE_ABOUT, 'Про нас'),
        (PAGE_COLLAB, 'Співпраця'),
        (PAGE_CONTACTS, 'Контакти'),
        (PAGE_DELIVERY, 'Доставка'),
        (PAGE_OFFER, 'Оферта'),
        (PAGE_PRIVACY, 'Політика конфіденційності'),
        (PAGE_CATALOG, 'Каталог'),
    )

    DEFAULT_BACKGROUND = '#f8f8f8'
    DEFAULT_TEXT = '#4c4c4c'
    DEFAULT_ACCENT = '#986030'

    page = models.CharField('Сторінка', max_length=32, choices=PAGE_CHOICES, unique=True)
    background_color = models.CharField(
        'Колір фону',
        max_length=32,
        blank=True,
        help_text='Фон між шапкою і підвалом. Порожнє — як на сайті за замовчуванням.',
    )
    text_color = models.CharField(
        'Колір тексту',
        max_length=32,
        blank=True,
        help_text='Основний текст сторінки. Порожнє — як на сайті за замовчуванням.',
    )
    accent_color = models.CharField(
        'Колір підсвітки',
        max_length=32,
        blank=True,
        help_text='Акцентні елементи. Порожнє — як на сайті за замовчуванням.',
    )

    class Meta:
        ordering = ['page']
        verbose_name = 'Оформлення сторінки'
        verbose_name_plural = 'Оформлення сторінок'

    def __str__(self):
        return self.get_page_display()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        clear_style_cache()

    def reset_to_default(self) -> None:
        self.background_color = ''
        self.text_color = ''
        self.accent_color = ''
        self.save(update_fields=['background_color', 'text_color', 'accent_color', 'updated_at'])

    @classmethod
    def for_page(cls, page: str) -> 'PageStyle':
        obj, _ = cls.objects.get_or_create(page=page)
        return obj


class ChromeStyle(TimeStampedModel):
    """Кольори шапки та підвалу (один запис на весь сайт)."""

    DEFAULT_HEADER_BG = '#0a0a0a'
    DEFAULT_HEADER_TEXT = '#f6f2f7'
    DEFAULT_FOOTER_TOP_BG = '#f8f8f8'
    DEFAULT_FOOTER_TOP_TEXT = '#313131'
    DEFAULT_FOOTER_BOTTOM_BG = '#f1efec'
    DEFAULT_FOOTER_BOTTOM_TEXT = '#313131'

    header_bg = models.CharField('Шапка — фон', max_length=32, blank=True)
    header_text = models.CharField('Шапка — текст', max_length=32, blank=True)
    footer_top_bg = models.CharField('Підвал (верх) — фон', max_length=32, blank=True)
    footer_top_text = models.CharField('Підвал (верх) — текст', max_length=32, blank=True)
    footer_bottom_bg = models.CharField('Підвал (низ) — фон', max_length=32, blank=True)
    footer_bottom_text = models.CharField('Підвал (низ) — текст', max_length=32, blank=True)

    class Meta:
        verbose_name = 'Шапка і підвал'
        verbose_name_plural = 'Шапка і підвал'

    def __str__(self):
        return 'Шапка і підвал'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        clear_style_cache()

    def delete(self, *args, **kwargs):
        return None

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def reset_to_default(self) -> None:
        self.header_bg = ''
        self.header_text = ''
        self.footer_top_bg = ''
        self.footer_top_text = ''
        self.footer_bottom_bg = ''
        self.footer_bottom_text = ''
        self.save()

    def effective(self) -> dict[str, str]:
        return {
            'header_bg': (self.header_bg or '').strip() or self.DEFAULT_HEADER_BG,
            'header_text': (self.header_text or '').strip() or self.DEFAULT_HEADER_TEXT,
            'footer_top_bg': (self.footer_top_bg or '').strip() or self.DEFAULT_FOOTER_TOP_BG,
            'footer_top_text': (self.footer_top_text or '').strip() or self.DEFAULT_FOOTER_TOP_TEXT,
            'footer_bottom_bg': (self.footer_bottom_bg or '').strip() or self.DEFAULT_FOOTER_BOTTOM_BG,
            'footer_bottom_text': (self.footer_bottom_text or '').strip() or self.DEFAULT_FOOTER_BOTTOM_TEXT,
        }
