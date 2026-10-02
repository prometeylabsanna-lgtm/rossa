import re

from django.core.cache import cache
from django.db import models

from core.mixins import SeoFieldsMixin, TimeStampedModel
from core.utils import localized


class SiteSettings(TimeStampedModel):
    phone = models.CharField('Телефон 1', max_length=64)
    phone_2 = models.CharField('Телефон 2', max_length=64, blank=True)
    phone_3 = models.CharField('Телефон 3', max_length=64, blank=True)
    email = models.EmailField('E-mail')
    telegram_url = models.URLField('Telegram URL', blank=True)
    telegram_handle = models.CharField('Telegram @', max_length=64, blank=True)
    instagram_url = models.URLField('Instagram URL', blank=True)
    facebook_url = models.URLField('Facebook URL', blank=True)
    tiktok_url = models.URLField('TikTok URL', blank=True)
    address_uk = models.CharField('Адреса (ukr)', max_length=255)
    address_ru = models.CharField('Адреса (ru)', max_length=255, blank=True)
    hours_uk = models.CharField('Графік (ukr)', max_length=128)
    hours_ru = models.CharField('Графік (ru)', max_length=128, blank=True)
    footer_tagline_uk = models.CharField('Підпис у підвалі (ukr)', max_length=255, blank=True)
    footer_tagline_ru = models.CharField('Підпис у підвалі (ru)', max_length=255, blank=True)
    map_image = models.ImageField('Карта / салон', upload_to='brand/', blank=True)
    logo = models.ImageField('Логотип', upload_to='brand/', blank=True)
    guarantee_uk = models.CharField('Гарантія (ukr)', max_length=128, blank=True)
    guarantee_ru = models.CharField('Гарантія (ru)', max_length=128, blank=True)
    delivery_label_uk = models.CharField('Доставка (ukr)', max_length=128, blank=True)
    delivery_label_ru = models.CharField('Доставка (ru)', max_length=128, blank=True)

    class Meta:
        verbose_name = 'Налаштування сайту'
        verbose_name_plural = 'Налаштування сайту'

    def __str__(self):
        return 'ROSSA'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('site_settings')

    def delete(self, *args, **kwargs):
        pass

    @staticmethod
    def tel_href(phone: str) -> str:
        digits = re.sub(r'\D', '', phone or '')
        if not digits:
            return ''
        if digits.startswith('0') and len(digits) == 10:
            digits = '38' + digits
        elif len(digits) == 9:
            digits = '380' + digits
        if not digits.startswith('380') and len(digits) < 12:
            digits = '380' + digits.lstrip('0')
        return f'+{digits}'

    @property
    def phone_tel(self):
        return self.tel_href(self.phone)

    @property
    def phones(self):
        items = []
        for value in (self.phone, self.phone_2, self.phone_3):
            value = (value or '').strip()
            if value:
                items.append({'display': value, 'tel': self.tel_href(value)})
        return items

    @classmethod
    def load(cls):
        cached = cache.get('site_settings')
        if cached is not None:
            return cached
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'phone': '067 540 77 11',
                'phone_2': '073 076 77 55',
                'phone_3': '050 029 05 00',
                'email': 'rossamebli2016@gmail.com',
                'telegram_url': 'https://t.me/rossaukr',
                'telegram_handle': '@rossaukr',
                'instagram_url': 'https://www.instagram.com/rossa_mebel_ua',
                'facebook_url': 'https://www.facebook.com/share/19wDTQG2Vc/',
                'tiktok_url': 'https://www.tiktok.com/@rossa_ua',
                'address_uk': 'м. Київ, вул. Індустріальна, 12',
                'address_ru': 'г. Киев, ул. Индустриальная, 12',
                'hours_uk': 'Пн–Сб, 10:00–19:00',
                'hours_ru': 'Пн–Сб, 10:00–19:00',
            },
        )
        cache.set('site_settings', obj, 300)
        return obj

    @property
    def address(self):
        return localized(self, 'address')

    @property
    def hours(self):
        return localized(self, 'hours')

    @property
    def footer_tagline(self):
        return localized(self, 'footer_tagline')

    @property
    def guarantee(self):
        return localized(self, 'guarantee')

    @property
    def delivery_label(self):
        return localized(self, 'delivery_label')


class HeaderSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Шапка сайту'
        verbose_name_plural = 'Шапка сайту'


class FooterSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Підвал сайту'
        verbose_name_plural = 'Підвал сайту'


class HomePage(SeoFieldsMixin, TimeStampedModel):
    section_categories_uk = models.CharField('Категорії (ukr)', max_length=128, default='Категорії')
    section_categories_ru = models.CharField('Категорії (ru)', max_length=128, blank=True)
    section_bestsellers_uk = models.CharField('Хіти (ukr)', max_length=128, default='Популярні моделі')
    section_bestsellers_ru = models.CharField('Хіти (ru)', max_length=128, blank=True)
    about_title_uk = models.CharField('Про ROSSA — заголовок (ukr)', max_length=255, blank=True)
    about_title_ru = models.CharField('Про ROSSA — заголовок (ru)', max_length=255, blank=True)
    about_body_uk = models.TextField('Про ROSSA — текст (ukr)', blank=True)
    about_body_ru = models.TextField('Про ROSSA — текст (ru)', blank=True)
    about_video = models.FileField('Про ROSSA — відео', upload_to='home/video/', blank=True)
    craft_title_uk = models.CharField('Заголовок блоку «виробництво» (ukr)', max_length=255)
    craft_title_ru = models.CharField('Заголовок блоку «виробництво» (ru)', max_length=255, blank=True)
    craft_body_uk = models.TextField('Текст блоку «виробництво» (ukr)')
    craft_body_ru = models.TextField('Текст блоку «виробництво» (ru)', blank=True)
    craft_link_uk = models.CharField('Текст посилання «Про нас» (ukr)', max_length=128, blank=True)
    craft_link_ru = models.CharField('Текст посилання «Про нас» (ru)', max_length=128, blank=True)
    craft_image = models.ImageField('Фото майстерні', upload_to='home/', blank=True)
    cta_banner_title_uk = models.CharField('Текст банера-запрошення (ukr)', max_length=255, blank=True)
    cta_banner_title_ru = models.CharField('Текст банера-запрошення (ru)', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Головна'
        verbose_name_plural = 'Головна'

    def __str__(self):
        return 'Головна'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={
            'craft_title_uk': 'Кожна деталь має значення',
            'craft_body_uk': '',
        })
        return obj

    @property
    def section_categories(self):
        return localized(self, 'section_categories')

    @property
    def section_bestsellers(self):
        return localized(self, 'section_bestsellers')

    @property
    def about_title(self):
        return localized(self, 'about_title')

    @property
    def about_body(self):
        return localized(self, 'about_body')

    @property
    def craft_title(self):
        return localized(self, 'craft_title')

    @property
    def craft_body(self):
        return localized(self, 'craft_body')

    @property
    def craft_link(self):
        return localized(self, 'craft_link')

    @property
    def cta_banner_title(self):
        return localized(self, 'cta_banner_title')

    @property
    def seo_title(self):
        return localized(self, 'seo_title')

    @property
    def seo_description(self):
        return localized(self, 'seo_description')


class HeroSlide(TimeStampedModel):
    page = models.ForeignKey(
        HomePage,
        on_delete=models.CASCADE,
        related_name='hero_slides',
        verbose_name='Головна',
    )
    image = models.ImageField('Зображення', upload_to='home/slides/')
    image_alt_uk = models.CharField('Підпис / alt (ukr)', max_length=160, blank=True)
    image_alt_ru = models.CharField('Підпис / alt (ru)', max_length=160, blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активний', default=True)

    class Meta:
        verbose_name = 'Hero слайд'
        verbose_name_plural = 'Hero слайди'
        ordering = ('sort', 'id')

    def __str__(self):
        return self.image_alt_uk or f'Слайд {self.sort + 1}'

    @property
    def image_alt(self):
        return localized(self, 'image_alt')
