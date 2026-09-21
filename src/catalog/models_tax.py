from django.db import models
from django.urls import reverse

from core.mixins import SeoFieldsMixin, TimeStampedModel
from core.utils import localized


class Category(SeoFieldsMixin, TimeStampedModel):
    parent = models.ForeignKey(
        'self',
        verbose_name='Батьківська',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
    )
    slug = models.SlugField('Slug', max_length=64)
    name_uk = models.CharField('Назва (UK)', max_length=128)
    name_ru = models.CharField('Назва (RU)', max_length=128, blank=True)
    intro_uk = models.TextField('Вступ (UK)', blank=True)
    intro_ru = models.TextField('Вступ (RU)', blank=True)
    image = models.ImageField('Фото плитки', upload_to='categories/', blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видима', default=True)

    class Meta:
        ordering = ['sort', 'id']
        unique_together = [('parent', 'slug')]
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'

    def __str__(self):
        return self.name_uk

    @property
    def name(self):
        return localized(self, 'name')

    @property
    def intro(self):
        return localized(self, 'intro')

    @property
    def seo_title(self):
        return localized(self, 'seo_title')

    @property
    def seo_description(self):
        return localized(self, 'seo_description')

    def get_absolute_url(self):
        parts = [self.slug]
        node = self.parent
        while node:
            parts.append(node.slug)
            node = node.parent
        path = '/'.join(reversed(parts))
        return f'/katalog/{path}/'

    @property
    def label_path(self):
        names = [self.name]
        node = self.parent
        while node:
            names.append(node.name)
            node = node.parent
        return ' · '.join(reversed(names))


class Fabric(TimeStampedModel):
    slug = models.SlugField('Slug', unique=True)
    name_uk = models.CharField('Назва (UK)', max_length=128)
    name_ru = models.CharField('Назва (RU)', max_length=128, blank=True)
    surcharge = models.PositiveIntegerField('Націнка, грн', default=0)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видима', default=True)

    class Meta:
        ordering = ['sort', 'id']
        verbose_name = 'Тканина'
        verbose_name_plural = 'Тканини'

    def __str__(self):
        return self.name_uk

    @property
    def name(self):
        return localized(self, 'name')


class Shade(TimeStampedModel):
    fabric = models.ForeignKey(
        Fabric,
        verbose_name='Тканина',
        on_delete=models.CASCADE,
        related_name='shades',
    )
    slug = models.SlugField('Slug', max_length=64)
    name_uk = models.CharField('Назва (UK)', max_length=128)
    name_ru = models.CharField('Назва (RU)', max_length=128, blank=True)
    hex_color = models.CharField('HEX', max_length=7)
    swatch = models.ImageField('Міні-фото кружечка', upload_to='shades/', blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видимий', default=True)

    class Meta:
        ordering = ['sort', 'id']
        unique_together = [('fabric', 'slug')]
        verbose_name = 'Відтінок'
        verbose_name_plural = 'Відтінки'

    def __str__(self):
        return f'{self.fabric.name_uk} / {self.name_uk}'

    @property
    def name(self):
        return localized(self, 'name')
