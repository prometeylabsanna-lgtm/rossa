from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_imagefield_to_webp'),
    ]

    operations = [
        migrations.CreateModel(
            name='CookiesPage',
            fields=[],
            options={
                'verbose_name': 'Cookies',
                'verbose_name_plural': 'Cookies',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.legalpage',),
        ),
        migrations.AlterField(
            model_name='pagestyle',
            name='page',
            field=models.CharField(
                choices=[
                    ('home', 'Головна'),
                    ('about', 'Про нас'),
                    ('collab', 'Співпраця'),
                    ('contacts', 'Контакти'),
                    ('delivery', 'Доставка'),
                    ('offer', 'Оферта'),
                    ('privacy', 'Політика конфіденційності'),
                    ('cookies', 'Cookies'),
                    ('catalog', 'Каталог'),
                ],
                max_length=32,
                unique=True,
                verbose_name='Сторінка',
            ),
        ),
    ]
