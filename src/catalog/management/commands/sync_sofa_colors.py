from django.core.management.base import BaseCommand

from catalog.sofa_colors import sync_all_sofa_colors


class Command(BaseCommand):
    help = (
        'Синхронізує палітру відтінків диванів: '
        'світло-сірий, зелений, оранжевий, графіт (+ беж, коричневий). '
        'Нові кольори — лише HEX-кружечки без заміни наявних фото.'
    )

    def handle(self, *args, **options):
        options_count, linked = sync_all_sofa_colors()
        self.stdout.write(
            self.style.SUCCESS(
                f'Оновлено {options_count} стандартних кольорів, '
                f'привʼязок до диванів: {linked}.'
            )
        )
