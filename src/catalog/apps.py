from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
    verbose_name = 'Каталог'

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from catalog.google_feed import invalidate_google_merchant_feed_cache
        from catalog.models import (
            Category,
            Product,
            ProductColor,
            ProductColorImage,
            ProductFabricPrice,
        )

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

        # Ціна, фото кольору, галерея й категорія входять у XML фіда.
        feed_senders = (
            Product,
            ProductFabricPrice,
            ProductColor,
            ProductColorImage,
            Category,
        )
        for model in feed_senders:
            label = model._meta.label_lower
            post_save.connect(
                invalidate_google_merchant_feed_cache,
                sender=model,
                dispatch_uid=f'google_feed_save:{label}',
                weak=False,
            )
            post_delete.connect(
                invalidate_google_merchant_feed_cache,
                sender=model,
                dispatch_uid=f'google_feed_delete:{label}',
                weak=False,
            )
