from django.db import models

from core.mixins import SeoFieldsMixin, TimeStampedModel
from core.utils import localized


class ValueProp(TimeStampedModel):
    number = models.CharField('Номер', max_length=8)
    title_uk = models.CharField('Заголовок (UK)', max_length=128)
    title_ru = models.CharField('Заголовок (RU)', max_length=128, blank=True)
    body_uk = models.TextField('Текст (UK)')
    body_ru = models.TextField('Текст (RU)', blank=True)
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
    title_uk = models.CharField('Заголовок (UK)', max_length=255)
    title_ru = models.CharField('Заголовок (RU)', max_length=255, blank=True)
    subtitle_uk = models.CharField('Підзаголовок (UK)', max_length=255, blank=True)
    subtitle_ru = models.CharField('Підзаголовок (RU)', max_length=255, blank=True)
    body_uk = models.TextField('Текст (UK)')
    body_ru = models.TextField('Текст (RU)', blank=True)
    hero_image = models.ImageField('Головне фото', upload_to='about/', blank=True)
    milestones_title_uk = models.CharField(
        'Заголовок віх (UK)',
        max_length=128,
        blank=True,
        default='Ключові віхи нашої історії',
    )
    milestones_title_ru = models.CharField('Заголовок віх (RU)', max_length=128, blank=True)
    milestones = models.JSONField('Віхи', default=list, blank=True)
    values = models.JSONField('Цінності', default=list, blank=True)
    craft_images = models.JSONField('Фото виробництва', default=list, blank=True)
    logo_title_uk = models.CharField(
        'Заголовок логотипів (UK)',
        max_length=128,
        blank=True,
        default='Еволюція логотипу',
    )
    logo_title_ru = models.CharField('Заголовок логотипів (RU)', max_length=128, blank=True)
    logo_images = models.JSONField(
        'Логотипи (галерея)',
        default=list,
        blank=True,
        help_text='Список: image, year, label_uk, label_ru.',
    )
    evolution_title_uk = models.CharField(
        'Заголовок еволюції (UK)',
        max_length=128,
        blank=True,
        default='Еволюція наших диванів',
    )
    evolution_title_ru = models.CharField('Заголовок еволюції (RU)', max_length=128, blank=True)
    evolution_images = models.JSONField(
        'Еволюція диванів',
        default=list,
        blank=True,
        help_text='Список: image (URL). Порядок = порядок показу.',
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
    def logo_title(self):
        return localized(self, 'logo_title') or 'Еволюція логотипу'

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
    title_uk = models.CharField('Заголовок (UK)', max_length=255)
    title_ru = models.CharField('Заголовок (RU)', max_length=255, blank=True)
    sub_uk = models.TextField('Вступ (UK)', blank=True)
    sub_ru = models.TextField('Вступ (RU)', blank=True)
    form_title_uk = models.CharField('Заголовок форми (UK)', max_length=128, blank=True)
    form_title_ru = models.CharField('Заголовок форми (RU)', max_length=128, blank=True)
    hero_image = models.ImageField('Hero фото', upload_to='collab/', blank=True)
    form_image = models.ImageField('Фото біля форми', upload_to='collab/', blank=True)
    advantages_title_uk = models.CharField('Заголовок переваг (UK)', max_length=128, blank=True, default='Наші переваги')
    advantages_title_ru = models.CharField('Заголовок переваг (RU)', max_length=128, blank=True)
    benefits = models.JSONField(
        'Переваги',
        default=list,
        blank=True,
        help_text='Список: icon (years|production|guarantee|collections|design), title_uk, title_ru',
    )
    dealer_support_title_uk = models.CharField(
        'Заголовок підтримки дилера (UK)',
        max_length=128,
        blank=True,
        default='Підтримка нашого дилера:',
    )
    dealer_support_title_ru = models.CharField('Заголовок підтримки дилера (RU)', max_length=128, blank=True)
    dealer_support = models.JSONField(
        'Підтримка дилера',
        default=list,
        blank=True,
        help_text='Список: title_uk, title_ru, body_uk, body_ru',
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
            defaults={'title_uk': 'Співпраця з ROSSA', 'sub_uk': ''},
        )
        return obj

    @property
    def title(self):
        return localized(self, 'title')

    @property
    def sub(self):
        return localized(self, 'sub')

    @property
    def form_title(self):
        return localized(self, 'form_title')

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


class LegalPage(SeoFieldsMixin, TimeStampedModel):
    slug = models.SlugField('URL', unique=True)
    title_uk = models.CharField('Заголовок (UK)', max_length=255)
    title_ru = models.CharField('Заголовок (RU)', max_length=255, blank=True)
    body_uk = models.TextField('Текст (UK)')
    body_ru = models.TextField('Текст (RU)', blank=True)
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
