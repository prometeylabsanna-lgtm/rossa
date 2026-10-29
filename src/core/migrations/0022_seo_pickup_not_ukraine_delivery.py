# SEO: прибрати «доставка по Україні» з meta-описів на користь самовивозу.

from django.db import migrations

_SEO_MODELS = (
    ('core', 'HomePage'),
    ('core', 'AboutPage'),
    ('core', 'CollabPage'),
    ('core', 'ContactsPage'),
    ('core', 'LegalPage'),
    ('catalog', 'Category'),
    ('catalog', 'Product'),
)

_SEO_FIELDS = ('seo_description_uk', 'seo_description_ru')


def _pairs(pickup_uk: str, pickup_ru: str) -> tuple[tuple[str, str], ...]:
    uk = pickup_uk or 'самовивіз'
    ru = pickup_ru or 'самовывоз'
    uk_mid = uk[:1].lower() + uk[1:] if uk else uk
    ru_mid = ru[:1].lower() + ru[1:] if ru else ru
    return (
        ('доставка по всій Україні', uk_mid),
        ('доставка по всей Украине', ru_mid),
        ('Доставка по всій Україні', uk),
        ('Доставка по всей Украине', ru),
        ('доставка по Україні', uk_mid),
        ('доставка по Украине', ru_mid),
        ('Доставка по Україні', uk),
        ('Доставка по Украине', ru),
        ('delivery across Ukraine', uk_mid),
        ('Delivery across Ukraine', uk),
    )


def forwards(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    settings = SiteSettings.objects.filter(pk=1).first()
    pickup_uk = ''
    pickup_ru = ''
    if settings is not None:
        pickup_uk = (getattr(settings, 'delivery_label_uk', '') or '').strip()
        pickup_ru = (getattr(settings, 'delivery_label_ru', '') or '').strip()

    pairs = _pairs(pickup_uk, pickup_ru)

    for app_label, model_name in _SEO_MODELS:
        Model = apps.get_model(app_label, model_name)
        field_names = {field.name for field in Model._meta.fields}
        fields = [name for name in _SEO_FIELDS if name in field_names]
        if not fields:
            continue
        for obj in Model.objects.all().iterator():
            changed = []
            for field in fields:
                raw = getattr(obj, field) or ''
                updated = raw
                for old, new in pairs:
                    if old in updated:
                        updated = updated.replace(old, new)
                if updated != raw:
                    setattr(obj, field, updated)
                    changed.append(field)
            if changed:
                obj.save(update_fields=changed)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_leads_forms_sale_prices'),
        ('catalog', '0013_leads_forms_sale_prices'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
