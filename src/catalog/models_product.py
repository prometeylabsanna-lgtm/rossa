import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from catalog.models_tax import Category, Fabric
from core.fields import WebPImageField
from core.mixins import SeoFieldsMixin, TimeStampedModel
from core.slug import AutoSlugMixin
from core.utils import localized

_HEX_RE = re.compile(r'^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$')


class Product(AutoSlugMixin, SeoFieldsMixin, TimeStampedModel):
    class Badge(models.TextChoices):
        NEW = 'NEW', 'NEW'
        TOP = 'TOP', 'TOP'
        HIT = 'HIT', 'Хіт'

    slug = models.SlugField('URL-адреса', unique=True)
    sku = models.CharField('Артикул', max_length=64, blank=True)
    name_uk = models.CharField('Назва (ukr)', max_length=128)
    name_ru = models.CharField('Назва (ru)', max_length=128, blank=True)
    type_uk = models.CharField('Тип (ukr)', max_length=128, blank=True)
    type_ru = models.CharField('Тип (ru)', max_length=128, blank=True)
    category = models.ForeignKey(
        Category,
        verbose_name='Категорія',
        on_delete=models.PROTECT,
        related_name='products',
    )
    base_price = models.PositiveIntegerField('Базова ціна, грн')
    badge = models.CharField('Бейдж', max_length=8, choices=Badge.choices, blank=True)
    is_available = models.BooleanField('В наявності', default=True)
    is_active = models.BooleanField('Видимий', default=True)
    description_uk = models.TextField('Опис (ukr)', blank=True)
    description_ru = models.TextField('Опис (ru)', blank=True)
    care_uk = models.TextField('Догляд (ukr)', blank=True)
    care_ru = models.TextField('Догляд (ru)', blank=True)
    dims_uk = models.CharField('Розміри (ukr)', max_length=255, blank=True)
    dims_ru = models.CharField('Розміри (ru)', max_length=255, blank=True)
    default_image = WebPImageField('Основне фото', upload_to='products/', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        indexes = [
            models.Index(fields=['is_active', 'is_available']),
            models.Index(fields=['name_uk']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return self.name_uk

    @property
    def name(self):
        return localized(self, 'name')

    @property
    def type_label(self):
        return localized(self, 'type')

    @property
    def description(self):
        return localized(self, 'description')

    @property
    def care(self):
        return localized(self, 'care')

    @property
    def dims(self):
        return localized(self, 'dims')

    @property
    def spec_rows(self):
        rows = []
        for item in self.characteristics.all():
            value = item.value
            if not value:
                continue
            char = item.characteristic
            if char and not char.is_active:
                continue
            label = char.name if char else ''
            if label:
                rows.append((label, value))
        return rows

    @property
    def seo_title(self):
        return localized(self, 'seo_title')

    @property
    def seo_description(self):
        return localized(self, 'seo_description')

    def get_absolute_url(self):
        return reverse('catalog:product', kwargs={'slug': self.slug})

    @property
    def min_price(self):
        prices = [fp.price for fp in self.fabric_prices.all()]
        if prices:
            return min(prices)
        return self.base_price

    def price_for_fabric(self, fabric):
        match = next((fp for fp in self.fabric_prices.all() if fp.fabric_id == fabric.id), None)
        if match:
            return match.price
        return self.base_price + (fabric.surcharge or 0)

    def preview_shades(self):
        """Кружечки на картці: кольори товару (ціна від кольору не залежить)."""
        seen = []
        for color in self.colors.all():
            if not color.is_active:
                continue
            image = color.image or self.default_image
            if not image:
                continue
            seen.append({
                'shade': color,
                'image': image,
                'hex': color.hex_color,
            })
            if len(seen) >= 8:
                break
        return seen


class ProductFabricPrice(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='fabric_prices',
    )
    fabric = models.ForeignKey(
        Fabric,
        verbose_name='Тканина',
        on_delete=models.CASCADE,
        related_name='product_prices',
    )
    price = models.PositiveIntegerField('Ціна, грн')
    sku = models.CharField('Артикул варіанта', max_length=64, blank=True)

    class Meta:
        unique_together = [('product', 'fabric')]
        verbose_name = 'Ціна тканини'
        verbose_name_plural = 'Ціни тканин'


class ProductColorOption(AutoSlugMixin, TimeStampedModel):
    """Стандартний колір для кружечків (беж, зелений, коричневий…)."""

    slug = models.SlugField('URL-адреса', max_length=64, unique=True)
    name_uk = models.CharField('Назва (ukr)', max_length=64)
    name_ru = models.CharField('Назва (ru)', max_length=64, blank=True)
    hex_color = models.CharField('HEX', max_length=7)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видимий', default=True)

    class Meta:
        ordering = ['sort', 'id']
        verbose_name = 'Стандартний колір'
        verbose_name_plural = 'Стандартні кольори'

    def __str__(self):
        return f'{self.name_uk} ({self.hex_color})'

    @property
    def name(self):
        return localized(self, 'name')

    def clean(self):
        super().clean()
        value = (self.hex_color or '').strip()
        if not _HEX_RE.fullmatch(value):
            raise ValidationError({'hex_color': 'Очікується HEX у форматі #RGB або #RRGGBB'})
        self.hex_color = value


class ProductColor(TimeStampedModel):
    """Колір товару: стандартний кружечок + фото товару цього кольору."""

    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='colors',
    )
    color = models.ForeignKey(
        ProductColorOption,
        verbose_name='Колір',
        on_delete=models.PROTECT,
        related_name='product_colors',
    )
    image = WebPImageField(
        'Фото товару цього кольору',
        upload_to='products/colors/',
        blank=True,
    )
    sort = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Видимий', default=True)

    class Meta:
        ordering = ['sort', 'id']
        unique_together = [('product', 'color')]
        verbose_name = 'Колір товару'
        verbose_name_plural = 'Кольори товару'

    def __str__(self):
        return f'{self.product.name_uk} / {self.color.name_uk}'

    @property
    def name(self):
        return self.color.name

    @property
    def name_uk(self):
        return self.color.name_uk

    @property
    def name_ru(self):
        return self.color.name_ru

    @property
    def hex_color(self):
        return self.color.hex_color

    @property
    def slug(self):
        return self.color.slug


class ProductCharacteristic(TimeStampedModel):
    """Значення характеристики для конкретного товару."""

    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='characteristics',
    )
    characteristic = models.ForeignKey(
        'catalog.Characteristic',
        verbose_name='Характеристика',
        on_delete=models.PROTECT,
        related_name='product_values',
    )
    value_uk = models.CharField('Значення (ukr)', max_length=255)
    value_ru = models.CharField('Значення (ru)', max_length=255, blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['characteristic__sort', 'sort', 'id']
        unique_together = [('product', 'characteristic')]
        verbose_name = 'Характеристика товару'
        verbose_name_plural = 'Характеристики товару'

    def __str__(self):
        return f'{self.product.name_uk} / {self.characteristic.name_uk}'

    @property
    def value(self):
        return localized(self, 'value')
