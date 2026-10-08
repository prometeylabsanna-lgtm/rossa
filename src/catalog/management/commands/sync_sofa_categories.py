from django.core.management.base import BaseCommand

from catalog.sofa_categories import ensure_sofa_subcategories


class Command(BaseCommand):
    help = (
        'Синхронізує підкатегорії диванів: '
        'модульні, кутові, прямі, єврокнижки.'
    )

    def handle(self, *args, **options):
        children = ensure_sofa_subcategories()
        names = ', '.join(c.name_uk for c in children.values())
        self.stdout.write(self.style.SUCCESS(f'Підкатегорії диванів: {names}.'))
