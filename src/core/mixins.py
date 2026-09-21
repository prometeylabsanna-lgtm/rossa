from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        abstract = True


class SeoFieldsMixin(models.Model):
    seo_title_uk = models.CharField('SEO title (UK)', max_length=512, blank=True)
    seo_title_ru = models.CharField('SEO title (RU)', max_length=512, blank=True)
    seo_description_uk = models.TextField('SEO description (UK)', blank=True)
    seo_description_ru = models.TextField('SEO description (RU)', blank=True)

    class Meta:
        abstract = True
