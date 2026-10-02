import django.db.models.deletion
from django.db import migrations, models


DEFAULT_CHARACTERISTICS = (
    ('frame', 'Каркас', 'Каркас', 0),
    ('filling', 'Наповнення', 'Наполнение', 1),
    ('mechanism', 'Механізм трансформації', 'Механизм трансформации', 2),
    ('textile', 'Тканина', 'Ткань', 3),
    ('storage', 'Ніші для білизни', 'Ниши для белья', 4),
)

SPEC_FIELD_MAP = {
    'frame': ('spec_frame_uk', 'spec_frame_ru'),
    'filling': ('spec_filling_uk', 'spec_filling_ru'),
    'mechanism': ('spec_mechanism_uk', 'spec_mechanism_ru'),
    'textile': ('spec_textile_uk', 'spec_textile_ru'),
    'storage': ('spec_storage_uk', 'spec_storage_ru'),
}


def migrate_specs_forward(apps, schema_editor):
    Characteristic = apps.get_model('catalog', 'Characteristic')
    Product = apps.get_model('catalog', 'Product')
    ProductCharacteristic = apps.get_model('catalog', 'ProductCharacteristic')

    char_by_key = {}
    sort_by_key = {key: sort for key, _uk, _ru, sort in DEFAULT_CHARACTERISTICS}
    for key, name_uk, name_ru, sort in DEFAULT_CHARACTERISTICS:
        obj, _ = Characteristic.objects.get_or_create(
            name_uk=name_uk,
            defaults={
                'name_ru': name_ru,
                'sort': sort,
                'is_active': True,
            },
        )
        if obj.name_ru != name_ru or obj.sort != sort or not obj.is_active:
            obj.name_ru = name_ru
            obj.sort = sort
            obj.is_active = True
            obj.save(update_fields=['name_ru', 'sort', 'is_active', 'updated_at'])
        char_by_key[key] = obj

    for product in Product.objects.all().iterator():
        for key, (uk_field, ru_field) in SPEC_FIELD_MAP.items():
            value_uk = (getattr(product, uk_field, '') or '').strip()
            value_ru = (getattr(product, ru_field, '') or '').strip()
            if not value_uk and not value_ru:
                continue
            ProductCharacteristic.objects.update_or_create(
                product=product,
                characteristic=char_by_key[key],
                defaults={
                    'value_uk': value_uk or value_ru,
                    'value_ru': value_ru,
                    'sort': sort_by_key[key],
                },
            )


def migrate_specs_backward(apps, schema_editor):
    Characteristic = apps.get_model('catalog', 'Characteristic')
    Product = apps.get_model('catalog', 'Product')
    ProductCharacteristic = apps.get_model('catalog', 'ProductCharacteristic')

    name_to_key = {row[1]: row[0] for row in DEFAULT_CHARACTERISTICS}
    for item in ProductCharacteristic.objects.select_related('characteristic', 'product'):
        key = name_to_key.get(item.characteristic.name_uk)
        if not key:
            continue
        uk_field, ru_field = SPEC_FIELD_MAP[key]
        product = item.product
        setattr(product, uk_field, item.value_uk)
        setattr(product, ru_field, item.value_ru)
        product.save(update_fields=[uk_field, ru_field])

    ProductCharacteristic.objects.all().delete()
    Characteristic.objects.filter(
        name_uk__in=[row[1] for row in DEFAULT_CHARACTERISTICS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_product_color_option_drop_shade_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Characteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('name_uk', models.CharField(max_length=128, verbose_name='Назва (ukr)')),
                ('name_ru', models.CharField(blank=True, max_length=128, verbose_name='Назва (ru)')),
                ('sort', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
            ],
            options={
                'verbose_name': 'Характеристика',
                'verbose_name_plural': 'Характеристики',
                'ordering': ['sort', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ProductCharacteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('value_uk', models.CharField(max_length=255, verbose_name='Значення (ukr)')),
                ('value_ru', models.CharField(blank=True, max_length=255, verbose_name='Значення (ru)')),
                ('sort', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                (
                    'characteristic',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='product_values',
                        to='catalog.characteristic',
                        verbose_name='Характеристика',
                    ),
                ),
                (
                    'product',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='characteristics',
                        to='catalog.product',
                        verbose_name='Товар',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Характеристика товару',
                'verbose_name_plural': 'Характеристики товару',
                'ordering': ['characteristic__sort', 'sort', 'id'],
                'unique_together': {('product', 'characteristic')},
            },
        ),
        migrations.RunPython(migrate_specs_forward, migrate_specs_backward),
        migrations.RemoveField(
            model_name='product',
            name='spec_filling_ru',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_filling_uk',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_frame_ru',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_frame_uk',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_mechanism_ru',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_mechanism_uk',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_storage_ru',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_storage_uk',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_textile_ru',
        ),
        migrations.RemoveField(
            model_name='product',
            name='spec_textile_uk',
        ),
    ]
