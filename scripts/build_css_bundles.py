#!/usr/bin/env python3
"""Збирає CSS-бандли для швидшого FCP (менше render-blocking запитів)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / 'src' / 'core' / 'static' / 'css'

CORE_PARTS = [
    'fonts.css',
    'variables.css',
    'reset.css',
    'base.css',
    'layout.css',
    'components/buttons.css',
    'components/header.css',
    'components/mobile-nav.css',
    'components/footer.css',
    'components/cards.css',
    'components/forms.css',
    'components/scroll-top.css',
    'animations.css',
]


def concat(parts: list[str], out_name: str) -> Path:
    chunks = [f'/* auto-generated: {out_name} — run scripts/build_css_bundles.py */\n']
    for rel in parts:
        path = CSS / rel
        if not path.is_file():
            raise SystemExit(f'Missing CSS part: {path}')
        chunks.append(f'\n/* --- {rel} --- */\n')
        text = path.read_text(encoding='utf-8')
        chunks.append(text if text.endswith('\n') else text + '\n')
    out = CSS / out_name
    out.write_text(''.join(chunks), encoding='utf-8')
    return out


def main() -> None:
    out = concat(CORE_PARTS, 'bundle-core.css')
    print(f'OK {out.relative_to(ROOT)} ({out.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
