"""Копіює craft-фото «Про нас» зі slots у MEDIA (Docker volume)."""

from django.core.management.base import BaseCommand

from core.management.seed_media import ensure_about_craft_media


class Command(BaseCommand):
    help = 'Гарантує about-fabric/frame/assembly (+ variants) у MEDIA_ROOT.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перезаписати існуючі файли зі slots.',
        )

    def handle(self, *args, **options):
        written = ensure_about_craft_media(force=options['force'])
        if written:
            self.stdout.write(self.style.SUCCESS(f'Записано {len(written)} файл(ів)'))
            for name in written:
                self.stdout.write(f'  {name}')
        else:
            self.stdout.write('Уже на місці (нічого не змінено)')
