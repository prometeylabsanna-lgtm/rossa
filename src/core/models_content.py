from django.db import models

from core.collab_form_copy import default_collab_form_copy, resolve_form_field_copy
from core.fields import WebPImageField
from core.mixins import SeoFieldsMixin, TimeStampedModel
from core.utils import localized


class ValueProp(TimeStampedModel):
    number = models.CharField('Номер', max_length=8)
    title_uk = models.CharField('Заголовок (ukr)', max_length=128)
    title_ru = models.CharField('Заголовок (ru)', max_length=128, blank=True)
    body_uk = models.TextField('Текст (ukr)')
    body_ru = models.TextField('Текст (ru)', blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видимий', default=True)

    class Meta:
        ordering = ['sort', 'id']
        verbose_name = 'Перевага'
        verbose_name_plural = 'Переваги (головна)'

    def __str__(self):
        return self.title_uk

    @property
    def title(self):
        return localized(self, 'title')

    @property
    def body(self):
        return localized(self, 'body')


class AboutPage(SeoFieldsMixin, TimeStampedModel):
    title_uk = models.CharField('Заголовок (ukr)', max_length=255)
    title_ru = models.CharField('Заголовок (ru)', max_length=255, blank=True)
    subtitle_uk = models.CharField('Підзаголовок (ukr)', max_length=255, blank=True)
    subtitle_ru = models.CharField('Підзаголовок (ru)', max_length=255, blank=True)
    body_uk = models.TextField('Текст (ukr)')
    body_ru = models.TextField('Текст (ru)', blank=True)
    milestones_title_uk = models.CharField(
        'Заголовок віх (ukr)',
        max_length=128,
        blank=True,
        default='Ключові віхи нашої історії',
    )
    milestones_title_ru = models.CharField('Заголовок віх (ru)', max_length=128, blank=True)
    milestones = models.JSONField('Віхи', default=list, blank=True)
    craft_images = models.JSONField('Фото виробництва', default=list, blank=True)
    logo_images = models.JSONField(
        'Логотипи (галерея)',
        default=list,
        blank=True,
        help_text='Рядки: фото, рік, підписи. Без JSON.',
    )
    evolution_title_uk = models.CharField(
        'Заголовок еволюції (ukr)',
        max_length=128,
        blank=True,
        default='Еволюція наших диванів',
    )
    evolution_title_ru = models.CharField('Заголовок еволюції (ru)', max_length=128, blank=True)
    evolution_images = models.JSONField(
        'Еволюція диванів',
        default=list,
        blank=True,
        help_text='Галерея фото. Порядок = порядок показу.',
    )

    class Meta:
        verbose_name = 'Про нас'
        verbose_name_plural = 'Про нас'

    def __str__(self):
        return self.title_uk

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={'title_uk': 'Про ROSSA', 'body_uk': ''},
        )
        return obj

    @property
    def title(self):
        return localized(self, 'title')

    @property
    def subtitle(self):
        return localized(self, 'subtitle')

    @property
    def body(self):
        return localized(self, 'body')

    @property
    def milestones_title(self):
        return localized(self, 'milestones_title') or 'Ключові віхи нашої історії'

    @property
    def logos_by_year(self):
        out = {}
        for item in self.logo_images or []:
            year = str(item.get('year') or '').strip()
            if year:
                out[year] = item
        return out

    @property
    def milestone_rows(self):
        logos = self.logos_by_year
        rows = []
        for item in self.milestones or []:
            year = str(item.get('year') or '').strip()
            rows.append({
                'year': year,
                'body_uk': item.get('body_uk', ''),
                'body_ru': item.get('body_ru', ''),
                'logo': logos.get(year),
            })
        return rows

    @property
    def evolution_title(self):
        return localized(self, 'evolution_title') or 'Еволюція наших диванів'

    @property
    def seo_title(self):
        return localized(self, 'seo_title')

    @property
    def seo_description(self):
        return localized(self, 'seo_description')


class CollabPage(SeoFieldsMixin, TimeStampedModel):
    title_uk = models.CharField('Заголовок (ukr)', max_length=255)
    title_ru = models.CharField('Заголовок (ru)', max_length=255, blank=True)
    form_title_uk = models.CharField('Заголовок форми (ukr)', max_length=128, blank=True)
    form_title_ru = models.CharField('Заголовок форми (ru)', max_length=128, blank=True)
    form_fields = models.JSONField(
        'Поля форми',
        default=default_collab_form_copy,
        blank=True,
        help_text='Підписи та підказки полів заявки (укр / рос).',
    )
    hero_image = WebPImageField('Hero фото', upload_to='collab/', blank=True)
    form_image = WebPImageField('Фото біля форми', upload_to='collab/', blank=True)
    advantages_title_uk = models.CharField('Заголовок переваг (ukr)', max_length=128, blank=True, default='Наші переваги')
    advantages_title_ru = models.CharField('Заголовок переваг (ru)', max_length=128, blank=True)
    benefits = models.JSONField(
        'Переваги',
        default=list,
        blank=True,
        help_text='Додавайте рядки кнопкою нижче. Іконку обирайте зі списку.',
    )
    dealer_support_title_uk = models.CharField(
        'Заголовок підтримки дилера (ukr)',
        max_length=128,
        blank=True,
        default='Підтримка нашого дилера:',
    )
    dealer_support_title_ru = models.CharField('Заголовок підтримки дилера (ru)', max_length=128, blank=True)
    dealer_support = models.JSONField(
        'Підтримка дилера',
        default=list,
        blank=True,
        help_text='Додавайте пункти кнопкою нижче — без JSON.',
    )

    class Meta:
        verbose_name = 'Співпраця'
        verbose_name_plural = 'Співпраця'

    def __str__(self):
        return self.title_uk

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={'title_uk': 'Співпраця з ROSSA'},
        )
        return obj

    @property
    def title(self):
        return localized(self, 'title')

    @property
    def form_title(self):
        return localized(self, 'form_title')

    def field_copy(self, field_key: str) -> dict[str, str]:
        return resolve_form_field_copy(self.form_fields, field_key)

    @property
    def form_submit_label(self) -> str:
        return self.field_copy('submit')['label'] or 'Надіслати'

    @property
    def advantages_title(self):
        return localized(self, 'advantages_title') or 'Наші переваги'

    @property
    def dealer_support_title(self):
        return localized(self, 'dealer_support_title') or 'Підтримка нашого дилера:'

    @property
    def seo_title(self):
        return localized(self, 'seo_title')

    @property
    def seo_description(self):
        return localized(self, 'seo_description')


class ContactsPage(SeoFieldsMixin, TimeStampedModel):
    title_uk = models.CharField('Заголовок (ukr)', max_length=255, default='Контакти')
    title_ru = models.CharField('Заголовок (ru)', max_length=255, blank=True)
    form_title_uk = models.CharField(
        'Заголовок форми (ukr)',
        max_length=128,
        blank=True,
        default='Напишіть нам',
    )
    form_title_ru = models.CharField('Заголовок форми (ru)', max_length=128, blank=True)

    class Meta:
        verbose_name = 'Контакти'
        verbose_name_plural = 'Контакти'

    def __str__(self):
        return self.title_uk

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'title_uk': 'Контакти',
                'title_ru': 'Контакты',
                'form_title_uk': 'Напишіть нам',
                'form_title_ru': 'Напишите нам',
            },
        )
        return obj

    @property
    def title(self):
        return localized(self, 'title')

    @property
    def form_title(self):
        return localized(self, 'form_title')

    @property
    def seo_title(self):
        return localized(self, 'seo_title')

    @property
    def seo_description(self):
        return localized(self, 'seo_description')


class LegalPage(SeoFieldsMixin, TimeStampedModel):
    slug = models.SlugField('URL', unique=True)
    title_uk = models.CharField('Заголовок (ukr)', max_length=255)
    title_ru = models.CharField('Заголовок (ru)', max_length=255, blank=True)
    body_uk = models.TextField('Текст (ukr)')
    body_ru = models.TextField('Текст (ru)', blank=True)
    is_active = models.BooleanField('Видима', default=True)

    class Meta:
        verbose_name = 'Юридична сторінка'
        verbose_name_plural = 'Юридичні сторінки'

    def __str__(self):
        return self.title_uk

    @property
    def title(self):
        return localized(self, 'title')

    @property
    def body(self):
        return localized(self, 'body')

    @property
    def seo_title(self):
        return localized(self, 'seo_title')

    @property
    def seo_description(self):
        return localized(self, 'seo_description')


class DeliveryPage(LegalPage):
    class Meta:
        proxy = True
        verbose_name = 'Доставка'
        verbose_name_plural = 'Доставка'


class OfferPage(LegalPage):
    class Meta:
        proxy = True
        verbose_name = 'Оферта'
        verbose_name_plural = 'Оферта'


class PrivacyPage(LegalPage):
    class Meta:
        proxy = True
        verbose_name = 'Політика конфіденційності'
        verbose_name_plural = 'Політика конфіденційності'
