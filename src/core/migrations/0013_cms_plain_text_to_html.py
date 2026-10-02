"""Data migration: plain CMS text → HTML paragraphs."""

from django.db import migrations

RICH_MODEL_FIELDS = (
    ('core', 'AboutPage', ('body_uk', 'body_ru')),
    ('core', 'HomePage', ('about_body_uk', 'about_body_ru', 'craft_body_uk', 'craft_body_ru')),
    ('core', 'ContactsPage', ('intro_uk', 'intro_ru')),
    ('core', 'CollabPage', ('sub_uk', 'sub_ru')),
    ('core', 'LegalPage', ('body_uk', 'body_ru')),
    ('core', 'ValueProp', ('body_uk', 'body_ru')),
)


def _convert_forward(apps, schema_editor):
    from core.cms_text import ensure_cms_html, ensure_cms_html_in_mapping

    for app_label, model_name, fields in RICH_MODEL_FIELDS:
        Model = apps.get_model(app_label, model_name)
        for obj in Model.objects.all().iterator():
            changed = False
            for field in fields:
                raw = getattr(obj, field, '') or ''
                html = ensure_cms_html(raw)
                if html != raw:
                    setattr(obj, field, html)
                    changed = True
            if model_name == 'AboutPage':
                milestones = list(getattr(obj, 'milestones', None) or [])
                new_milestones = [
                    ensure_cms_html_in_mapping(item, 'body_uk', 'body_ru')
                    for item in milestones
                ]
                if new_milestones != milestones:
                    obj.milestones = new_milestones
                    changed = True
            if model_name == 'CollabPage':
                support = list(getattr(obj, 'dealer_support', None) or [])
                new_support = [
                    ensure_cms_html_in_mapping(item, 'body_uk', 'body_ru')
                    for item in support
                ]
                if new_support != support:
                    obj.dealer_support = new_support
                    changed = True
            if changed:
                obj.save()


def _convert_noop(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0012_humanize_homepage_cms_labels'),
    ]

    operations = [
        migrations.RunPython(_convert_forward, _convert_noop),
    ]
