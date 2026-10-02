import django.db.models.deletion
from django.db import migrations, models


DEFAULT_COLORS = (
    ('beige', 'Беж', 'Беж', '#D4C4A8', 0),
    ('green', 'Зелений', 'Зелёный', '#7A8B6E', 1),
    ('brown', 'Коричневий', 'Коричневый', '#3C2415', 2),
)


def forwards_migrate_colors(apps, schema_editor):
    ProductColor = apps.get_model('catalog', 'ProductColor')
    ProductColorOption = apps.get_model('catalog', 'ProductColorOption')

    for slug, name_uk, name_ru, hex_color, sort in DEFAULT_COLORS:
        ProductColorOption.objects.update_or_create(
            slug=slug,
            defaults={
                'name_uk': name_uk,
                'name_ru': name_ru,
                'hex_color': hex_color,
                'sort': sort,
                'is_active': True,
            },
        )

    for row in ProductColor.objects.all():
        slug = (row.slug or '').strip() or f'color-{row.pk}'
        option = ProductColorOption.objects.filter(slug=slug).first()
        if option is None:
            option = ProductColorOption.objects.filter(hex_color__iexact=row.hex_color).first()
        if option is None:
            option = ProductColorOption.objects.create(
                slug=slug,
                name_uk=row.name_uk or slug,
                name_ru=row.name_ru or '',
                hex_color=row.hex_color or '#986030',
                sort=row.sort or 0,
                is_active=True,
            )
        row.color_id = option.pk
        row.save(update_fields=['color_id'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_fabric_surcharge_optional'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductColorOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('slug', models.SlugField(max_length=64, unique=True, verbose_name='URL-адреса')),
                ('name_uk', models.CharField(max_length=64, verbose_name='Назва (ukr)')),
                ('name_ru', models.CharField(blank=True, max_length=64, verbose_name='Назва (ru)')),
                ('hex_color', models.CharField(max_length=7, verbose_name='HEX')),
                ('sort', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Видимий')),
            ],
            options={
                'verbose_name': 'Стандартний колір',
                'verbose_name_plural': 'Стандартні кольори',
                'ordering': ['sort', 'id'],
            },
        ),
        migrations.AddField(
            model_name='productcolor',
            name='color',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='product_colors',
                to='catalog.productcoloroption',
                verbose_name='Колір',
            ),
        ),
        migrations.RunPython(forwards_migrate_colors, noop_reverse),
        migrations.AlterField(
            model_name='productcolor',
            name='color',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='product_colors',
                to='catalog.productcoloroption',
                verbose_name='Колір',
            ),
        ),
        migrations.AlterField(
            model_name='productcolor',
            name='image',
            field=models.ImageField(
                blank=True,
                upload_to='products/colors/',
                verbose_name='Фото товару цього кольору',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='productcolor',
            unique_together={('product', 'color')},
        ),
        migrations.RemoveField(model_name='productcolor', name='hex_color'),
        migrations.RemoveField(model_name='productcolor', name='name_ru'),
        migrations.RemoveField(model_name='productcolor', name='name_uk'),
        migrations.RemoveField(model_name='productcolor', name='slug'),
        migrations.DeleteModel(name='ProductShadeImage'),
    ]
