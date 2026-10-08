from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_rename_lang_labels_ukr_ru'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='homepage',
            name='about_video',
        ),
    ]
