"""Транслітерація UA/RU → латиниця та унікальні slug для CMS."""
from __future__ import annotations

from django.utils.text import slugify

_TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ye',
    'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'i', 'к': 'k', 'л': 'l',
    'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ь': '',
    'ю': 'yu', 'я': 'ya', 'ы': 'y', 'э': 'e', 'ё': 'yo', 'ъ': '',
}


def transliterate(value: str) -> str:
    out = []
    for ch in (value or '').strip().lower():
        out.append(_TRANSLIT.get(ch, ch))
    return ''.join(out)


def make_slug(value: str, *, max_length: int = 64) -> str:
    base = slugify(transliterate(value)) or slugify(value) or 'item'
    return base[:max_length].strip('-') or 'item'


def ensure_unique_slug(instance, base: str, *, slug_field: str = 'slug', max_length: int = 64) -> str:
    qs = instance.get_slug_unique_queryset()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    candidate = base[:max_length]
    if not qs.filter(**{slug_field: candidate}).exists():
        return candidate
    n = 2
    while True:
        suffix = f'-{n}'
        candidate = f'{base[: max_length - len(suffix)]}{suffix}'
        if not qs.filter(**{slug_field: candidate}).exists():
            return candidate
        n += 1


class AutoSlugMixin:
    """Генерує slug з джерела при створенні / зміні назви. Поле лише для читання в адмінці."""

    slug_source_field = 'name_uk'
    slug_field_name = 'slug'
    slug_max_length = 64

    def get_slug_unique_queryset(self):
        return type(self).objects.all()

    def _sync_slug_from_source(self) -> None:
        source = getattr(self, self.slug_source_field, '') or ''
        current = getattr(self, self.slug_field_name, '') or ''
        if self.pk:
            old = (
                type(self)
                .objects
                .filter(pk=self.pk)
                .values_list(self.slug_source_field, self.slug_field_name)
                .first()
            )
            if old is None:
                should_update = not current
            else:
                old_source, old_slug = old
                should_update = (old_source != source) or (not old_slug)
        else:
            should_update = not current
        if not should_update:
            return
        base = make_slug(source, max_length=self.slug_max_length)
        setattr(
            self,
            self.slug_field_name,
            ensure_unique_slug(
                self,
                base,
                slug_field=self.slug_field_name,
                max_length=self.slug_max_length,
            ),
        )

    def save(self, *args, **kwargs):
        self._sync_slug_from_source()
        return super().save(*args, **kwargs)
