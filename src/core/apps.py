from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Сайт'

    def ready(self):
        from django.db.models.signals import post_migrate

        def _seed_cms(sender, **kwargs):
            if sender.name != 'core':
                return
            try:
                from core.page_styles import ensure_legal_pages, ensure_page_styles
                ensure_page_styles()
                ensure_legal_pages()
            except Exception:
                pass

        post_migrate.connect(_seed_cms, sender=self)
