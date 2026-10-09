from django.db import models
from django.urls import reverse

from core.fields import WebPImageField
from core.mixins import SeoFieldsMixin, TimeStampedModel
from core.slug import AutoSlugMixin
from core.utils import localized


class Category(AutoSlugMixin, SeoFieldsMixin, TimeStampedModel):
    # Статичні превʼю для меню / плиток (поле image прибрано).
    MENU_IMAGE_STATIC = {
        'divany': 'images/slots/cat-sofas.webp',
        'lizhka': 'images/slots/cat-beds.webp',
        'pufy': 'images/slots/cat-poufs.webp',
    }

    parent = models.ForeignKey(
        'self',
        verbose_name='Батьківська',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
    )
    slug = models.SlugField('URL-адреса', max_length=64)
    name_uk = models.CharField('Назва (ukr)', max_length=128)
    name_ru = models.CharField('Назва (ru)', max_length=128, blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видима', default=True)

    class Meta:
        ordering = ['sort', 'id']
        unique_together = [('parent', 'slug')]
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'

    def __str__(self):
        return self.name_uk

    def get_slug_unique_queryset(self):
        return type(self).objects.filter(parent=self.parent)

    @property
    def menu_image_static(self) -> str:
        return self.MENU_IMAGE_STATIC.get(self.slug, '')

    @property
    def name(self):
        return localized(self, 'name')

    @property
    def seo_title(self):
        return localized(self, 'seo_title')

    @property
    def seo_description(self):
        return localized(self, 'seo_description')

    def get_absolute_url(self):
        from django.urls import reverse

        parts = [self.slug]
        node = self.parent
        while node:
            parts.append(node.slug)
            node = node.parent
        path = '/'.join(reversed(parts))
        return reverse('catalog:category', kwargs={'path': path})

    @property
    def label_path(self):
        names = [self.name]
        node = self.parent
        while node:
            names.append(node.name)
            node = node.parent
        return ' · '.join(reversed(names))


class Fabric(AutoSlugMixin, TimeStampedModel):
    slug = models.SlugField('URL-адреса', unique=True)
    name_uk = models.CharField('Назва (ukr)', max_length=128)
    name_ru = models.CharField('Назва (ru)', max_length=128, blank=True)
    surcharge = models.PositiveIntegerField('Націнка, грн', default=0, blank=True, null=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видима', default=True)

    class Meta:
        ordering = ['sort', 'id']
        verbose_name = 'Тканина'
        verbose_name_plural = 'Тканини'

    def __str__(self):
        return self.name_uk

    def save(self, *args, **kwargs):
        if self.surcharge is None:
            self.surcharge = 0
        super().save(*args, **kwargs)

    @property
    def name(self):
        return localized(self, 'name')


class Shade(AutoSlugMixin, TimeStampedModel):
    fabric = models.ForeignKey(
        Fabric,
        verbose_name='Тканина',
        on_delete=models.CASCADE,
        related_name='shades',
    )
    slug = models.SlugField('URL-адреса', max_length=64)
    name_uk = models.CharField('Назва (ukr)', max_length=128)
    name_ru = models.CharField('Назва (ru)', max_length=128, blank=True)
    hex_color = models.CharField('HEX', max_length=7)
    swatch = WebPImageField('Міні-фото кружечка', upload_to='shades/', blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видимий', default=True)

    class Meta:
        ordering = ['sort', 'id']
        unique_together = [('fabric', 'slug')]
        verbose_name = 'Відтінок'
        verbose_name_plural = 'Відтінки'

    def __str__(self):
        return f'{self.fabric.name_uk} / {self.name_uk}'

    def get_slug_unique_queryset(self):
        return type(self).objects.filter(fabric_id=self.fabric_id)

    @property
    def name(self):
        return localized(self, 'name')


class Characteristic(TimeStampedModel):
    """Тип характеристики товару (каркас, наповнення…)."""

    name_uk = models.CharField('Назва (ukr)', max_length=128)
    name_ru = models.CharField('Назва (ru)', max_length=128, blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        ordering = ['sort', 'id']
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'

    def __str__(self):
        return self.name_uk

    @property
    def name(self):
        return localized(self, 'name')
