from django.db import models

from core.mixins import TimeStampedModel


class LeadStatus(models.TextChoices):
    NEW = 'new', 'Нове'
    IN_PROGRESS = 'in_progress', 'В обробці'
    AGREED = 'agreed', 'Узгоджено'
    DONE = 'done', 'Виконано'
    CANCELLED = 'cancelled', 'Скасовано'


class Fulfillment(models.TextChoices):
    PICKUP = 'pickup', 'Самовивіз / завантаження'
    OWN_CAR = 'own_car', 'Власним авто'


class OrderRequest(TimeStampedModel):
    status = models.CharField('Статус', max_length=20, choices=LeadStatus.choices, default=LeadStatus.NEW)
    product_name = models.CharField('Модель', max_length=255)
    product_slug = models.SlugField('Slug моделі', max_length=128, blank=True)
    fabric_name = models.CharField('Тканина', max_length=128, blank=True)
    shade_name = models.CharField('Відтінок', max_length=128, blank=True)
    sku = models.CharField('Артикул', max_length=64, blank=True)
    price = models.PositiveIntegerField('Ціна на момент заявки')
    name = models.CharField('ПІБ', max_length=128)
    phone = models.CharField('Телефон', max_length=32)
    email = models.EmailField('E-mail', blank=True)
    comment = models.TextField('Коментар', blank=True)
    fulfillment = models.CharField(
        'Отримання',
        max_length=20,
        choices=Fulfillment.choices,
        default=Fulfillment.PICKUP,
    )
    consent = models.BooleanField('Згода на ПД')
    language = models.CharField('Мова', max_length=2, default='uk')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення товарів'

    def __str__(self):
        return f'{self.product_name} — {self.phone}'


class PartnershipLead(TimeStampedModel):
    class CollabType(models.TextChoices):
        DEALER = 'dealer', 'Дилер'
        SALON = 'salon', 'Салон'
        DESIGNER = 'designer', 'Дизайнер'
        WHOLESALE = 'wholesale', 'Гурт'

    status = models.CharField('Статус', max_length=20, choices=LeadStatus.choices, default=LeadStatus.NEW)
    company = models.CharField('Компанія / ПІБ', max_length=255)
    name = models.CharField('Контактна особа', max_length=128, blank=True)
    phone = models.CharField('Телефон', max_length=32)
    email = models.EmailField('E-mail')
    city = models.CharField('Місто', max_length=128, blank=True)
    collab_type = models.CharField('Тип співпраці', max_length=20, choices=CollabType.choices, blank=True)
    message = models.TextField('Повідомлення', blank=True)
    consent = models.BooleanField('Згода на ПД')
    language = models.CharField('Мова', max_length=2, default='uk')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка на співпрацю'
        verbose_name_plural = 'Заявки «Співпраця»'

    def __str__(self):
        return f'{self.company} — {self.phone}'


class ContactLead(TimeStampedModel):
    status = models.CharField('Статус', max_length=20, choices=LeadStatus.choices, default=LeadStatus.NEW)
    name = models.CharField('Ім’я', max_length=128)
    phone = models.CharField('Телефон', max_length=32)
    message = models.TextField('Повідомлення')
    consent = models.BooleanField('Згода на ПД')
    language = models.CharField('Мова', max_length=2, default='uk')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Звернення'
        verbose_name_plural = 'Звернення «Контакти»'

    def __str__(self):
        return f'{self.name} — {self.phone}'
