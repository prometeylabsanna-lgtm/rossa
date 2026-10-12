from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Сайт'

    def ready(self):
        from django.db.models.signals import post_delete, post_migrate, pre_save

        from core import media_cleanup
        from core.models import AboutPage

        pre_save.connect(media_cleanup.gallery_pre_save, sender=AboutPage, dispatch_uid='gallery_pre_save')
        post_delete.connect(media_cleanup.gallery_post_delete, sender=AboutPage, dispatch_uid='gallery_post_delete')

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
