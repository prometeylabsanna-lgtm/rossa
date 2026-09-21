from django.db import models
from django.urls import reverse

from catalog.models_tax import Category, Fabric, Shade
from core.mixins import SeoFieldsMixin, TimeStampedModel
from core.utils import localized


class Product(SeoFieldsMixin, TimeStampedModel):
    class Badge(models.TextChoices):
        NEW = 'NEW', 'NEW'
        TOP = 'TOP', 'TOP'
        HIT = 'HIT', 'Хіт'

    slug = models.SlugField('Slug', unique=True)
    sku = models.CharField('Артикул', max_length=64, blank=True)
    name_uk = models.CharField('Назва (UK)', max_length=128)
    name_ru = models.CharField('Назва (RU)', max_length=128, blank=True)
    type_uk = models.CharField('Тип (UK)', max_length=128, blank=True)
    type_ru = models.CharField('Тип (RU)', max_length=128, blank=True)
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
    description_uk = models.TextField('Опис (UK)', blank=True)
    description_ru = models.TextField('Опис (RU)', blank=True)
    care_uk = models.TextField('Догляд (UK)', blank=True)
    care_ru = models.TextField('Догляд (RU)', blank=True)
    dims_uk = models.CharField('Розміри (UK)', max_length=255, blank=True)
    dims_ru = models.CharField('Розміри (RU)', max_length=255, blank=True)
    default_image = models.ImageField('Основне фото', upload_to='products/', blank=True)

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
        return self.base_price + fabric.surcharge

    def preview_shades(self):
        prices = list(self.fabric_prices.all())
        fabric_id = None
        if prices:
            fabric_id = min(prices, key=lambda fp: fp.price).fabric_id
        seen = []
        ids = set()
        for img in self.shade_images.all():
            if not img.shade.is_active:
                continue
            if fabric_id and img.shade.fabric_id != fabric_id:
                continue
            if img.shade_id in ids:
                continue
            ids.add(img.shade_id)
            image = img.image or self.default_image
            if not image:
                continue
            seen.append({'shade': img.shade, 'image': image})
        return seen[:5]


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


class ProductShadeImage(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='shade_images',
    )
    shade = models.ForeignKey(
        Shade,
        verbose_name='Відтінок',
        on_delete=models.CASCADE,
        related_name='product_images',
    )
    image = models.ImageField('Фото', upload_to='products/shades/', blank=True)
    sort = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['sort', 'id']
        unique_together = [('product', 'shade', 'sort')]
        verbose_name = 'Фото відтінку'
        verbose_name_plural = 'Фото відтінків'
