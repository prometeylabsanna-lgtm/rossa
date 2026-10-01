from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_about_story_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='aboutpage',
            name='evolution_images',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Список: image (URL). Порядок = порядок показу.',
                verbose_name='Еволюція диванів',
            ),
        ),
        migrations.AddField(
            model_name='aboutpage',
            name='evolution_title_ru',
            field=models.CharField(
                blank=True,
                max_length=128,
                verbose_name='Заголовок еволюції (RU)',
            ),
        ),
        migrations.AddField(
            model_name='aboutpage',
            name='evolution_title_uk',
            field=models.CharField(
                blank=True,
                default='Еволюція наших диванів',
                max_length=128,
                verbose_name='Заголовок еволюції (UK)',
            ),
        ),
    ]
