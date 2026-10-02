"""Нормалізація CMS-текстів: plain text ↔ HTML для TinyMCE / сайту."""

from __future__ import annotations

import html as html_lib
import re

from django.utils.html import strip_tags

_TAG_RE = re.compile(r'<[a-zA-Z/!?]')


def looks_like_html(value: str) -> bool:
    text = value or ''
    if not text:
        return False
    if '&lt;' in text and '<' not in text:
        return True
    return bool(_TAG_RE.search(text))


def unescape_cms_html(value: str) -> str:
    text = value or ''
    if '&lt;' in text and '<' not in text:
        return html_lib.unescape(text)
    return text


def plain_text_to_cms_html(value: str) -> str:
    """Перетворює текст з \\n\\n на <p>…</p>. HTML лишає як є."""
    text = (value or '').strip()
    if not text:
        return ''
    text = unescape_cms_html(text)
    if looks_like_html(text):
        return text

    blocks = re.split(r'\n\s*\n', text)
    parts: list[str] = []
    for block in blocks:
        chunk = block.strip()
        if not chunk:
            continue
        inner = html_lib.escape(chunk).replace('\n', '<br>\n')
        parts.append(f'<p>{inner}</p>')
    return '\n'.join(parts)


def ensure_cms_html(value: str) -> str:
    """Ідемпотентно: plain → HTML, HTML без змін."""
    return plain_text_to_cms_html(value or '')


def ensure_cms_html_in_mapping(item: dict, *keys: str) -> dict:
    out = dict(item or {})
    for key in keys:
        if key in out and out[key]:
            out[key] = ensure_cms_html(str(out[key]))
    return out


def is_plain_cms_text(value: str) -> bool:
    """True, якщо текст ще не HTML (потрібна конвертація)."""
    text = (value or '').strip()
    if not text:
        return False
    text = unescape_cms_html(text)
    if looks_like_html(text):
        stripped = strip_tags(text).replace('\xa0', ' ').strip()
        normalized = text.replace('&nbsp;', ' ').strip()
        return stripped == normalized and '<' not in text
    return True
