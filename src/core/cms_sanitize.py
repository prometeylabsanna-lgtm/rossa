"""Allowlist-санітизація HTML з CMS перед mark_safe."""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlparse

ALLOWED_TAGS = frozenset({
    'p', 'br', 'strong', 'em', 'b', 'i', 'u', 'ul', 'ol', 'li', 'a', 'span',
})
# void / self-closing у нашому allowlist
_VOID = frozenset({'br'})
_ALLOWED_ATTRS = {
    'a': frozenset({'href', 'title', 'rel', 'target'}),
    'span': frozenset({'class'}),
}
_SAFE_LINK_SCHEMES = frozenset({'http', 'https', 'mailto', ''})


def _safe_href(value: str) -> str | None:
    raw = (value or '').strip()
    if not raw or raw.startswith('#'):
        return raw or None
    parsed = urlparse(raw)
    scheme = (parsed.scheme or '').lower()
    if scheme not in _SAFE_LINK_SCHEMES:
        return None
    if scheme in {'http', 'https', 'mailto'}:
        return raw
    # relative path /query
    if raw.startswith('/') or raw.startswith('?'):
        return raw
    if not scheme and '//' not in raw:
        return raw
    return None


class _AllowlistParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._out: list[str] = []
        self._stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            return
        allowed = _ALLOWED_ATTRS.get(tag, frozenset())
        parts = [tag]
        for name, value in attrs:
            name = (name or '').lower()
            if name not in allowed:
                continue
            if tag == 'a' and name == 'href':
                href = _safe_href(value or '')
                if href is None:
                    continue
                value = href
                parts.append(f'href="{_escape_attr(value)}"')
                continue
            if tag == 'a' and name == 'target':
                if (value or '') != '_blank':
                    continue
                parts.append('target="_blank"')
                parts.append('rel="noopener noreferrer"')
                continue
            if tag == 'a' and name == 'rel':
                continue  # виставляємо самі для _blank
            if value is None:
                parts.append(name)
            else:
                parts.append(f'{name}="{_escape_attr(value)}"')
        if tag in _VOID:
            self._out.append('<' + ' '.join(parts) + '>')
            return
        self._stack.append(tag)
        self._out.append('<' + ' '.join(parts) + '>')

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag not in ALLOWED_TAGS or tag in _VOID:
            return
        if tag in self._stack:
            while self._stack:
                open_tag = self._stack.pop()
                self._out.append(f'</{open_tag}>')
                if open_tag == tag:
                    break

    def handle_data(self, data):
        self._out.append(_escape_text(data))

    def handle_entityref(self, name):
        self._out.append(f'&{name};')

    def handle_charref(self, name):
        self._out.append(f'&#{name};')

    def get_html(self) -> str:
        while self._stack:
            self._out.append(f'</{self._stack.pop()}>')
        return ''.join(self._out)


def _escape_text(value: str) -> str:
    return (
        value.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def _escape_attr(value: str) -> str:
    return (
        value.replace('&', '&amp;')
        .replace('"', '&quot;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def sanitize_cms_html(value: str) -> str:
    """Прибирає script/style/handlers; лишає базове форматування TinyMCE."""
    text = (value or '').strip()
    if not text:
        return ''
    parser = _AllowlistParser()
    parser.feed(text)
    parser.close()
    return parser.get_html()
