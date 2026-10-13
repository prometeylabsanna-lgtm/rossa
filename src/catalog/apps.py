from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
    verbose_name = 'Каталог'

    def ready(self):
        from django.db.models.signals import post_delete

        from catalog.models import ProductColor, ProductColorImage

        def _cleanup_color_gallery(sender, instance, **kwargs):
            ProductColorImage.objects.filter(
                product_id=instance.product_id,
                color_id=instance.color_id,
            ).delete()

        post_delete.connect(
            _cleanup_color_gallery,
            sender=ProductColor,
            dispatch_uid='product_color_gallery_cleanup',
        )
