from __future__ import annotations

from typing import Any, Optional

from django.contrib.admin.widgets import AdminTextInputWidget, AdminTextareaWidget
from django.forms.widgets import ClearableFileInput
from tinymce.widgets import TinyMCE
from unfold.widgets import INPUT_CLASSES, TEXTAREA_CLASSES

from core.cms_text import ensure_cms_html

TINYMCE_SIMPLE = {
    'height': 360,
    'menubar': False,
    'plugins': 'link lists',
    'toolbar': 'undo redo | bold italic underline | bullist numlist | link | removeformat',
    'branding': False,
    'promotion': False,
    'forced_root_block': 'p',
    'newline_behavior': 'block',
    'content_style': (
        'body { font-family: system-ui, -apple-system, sans-serif; font-size: 16px; '
        'line-height: 1.55; padding: 8px 12px; }'
        'p { margin: 0 0 0.9em; }'
        'p:last-child { margin-bottom: 0; }'
    ),
}


class CmsTinyMCE(TinyMCE):
    """TinyMCE: plain text з \\n\\n відкривається вже як абзаци."""

    def format_value(self, value):
        raw = super().format_value(value)
        if raw in (None, ''):
            return ''
        return ensure_cms_html(str(raw))


def cms_control_classes(base_classes: list[str], extra_class: str = '') -> str:
    classes = list(base_classes)
    if extra_class:
        for token in extra_class.split():
            if token and token not in classes:
                classes.append(token)
    return ' '.join(classes)


class CmsAdminTextInputWidget(AdminTextInputWidget):
    def __init__(self, attrs: Optional[dict[str, Any]] = None) -> None:
        merged = dict(attrs or {})
        extra_class = merged.pop('class', '')
        super().__init__(attrs={
            **merged,
            'class': cms_control_classes(INPUT_CLASSES, extra_class),
        })


class CmsAdminTextareaWidget(AdminTextareaWidget):
    def __init__(self, attrs: Optional[dict[str, Any]] = None) -> None:
        merged = dict(attrs or {})
        extra_class = merged.pop('class', '')
        super().__init__(attrs={
            **merged,
            'class': cms_control_classes(TEXTAREA_CLASSES, extra_class),
        })


class CmsAdminImageWidget(ClearableFileInput):
    template_name = 'django/forms/widgets/cms_image.html'

    def __init__(self, attrs: Optional[dict[str, Any]] = None) -> None:
        merged = dict(attrs or {})
        extra_class = merged.pop('class', '')
        merged.setdefault('accept', 'image/*')
        classes = cms_control_classes(
            [c for c in INPUT_CLASSES if c != 'max-w-2xl'] + ['rs-cms-image-input'],
            extra_class,
        )
        super().__init__(attrs={**merged, 'class': classes})

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        preview_url = ''
        if value:
            try:
                preview_url = getattr(value, 'url', '') or ''
            except ValueError:
                preview_url = ''
        context['widget']['preview_url'] = preview_url
        context['widget']['preview_is_fallback'] = False
        context['widget']['preview_variant'] = 'photo'
        return context


class CmsAdminColorWidget(AdminTextInputWidget):
    input_type = 'color'
    template_name = 'django/forms/widgets/cms_color.html'

    class Media:
        css = {'all': ('css/admin/site_content.css',)}
        js = ('js/admin/cms_color_picker.js',)

    def __init__(
        self,
        attrs: Optional[dict[str, Any]] = None,
        *,
        default_color: str = '#f8f8f8',
    ) -> None:
        self.default_color = self._normalize_hex(default_color) or '#f8f8f8'
        merged = dict(attrs or {})
        extra_class = merged.pop('class', '')
        super().__init__(attrs={
            **merged,
            'class': cms_control_classes(['rs-cms-colorpick__native'], extra_class),
        })

    @staticmethod
    def _normalize_hex(value: str) -> str:
        raw = (value or '').strip()
        if not raw:
            return ''
        if len(raw) == 4 and raw.startswith('#'):
            return f'#{raw[1] * 2}{raw[2] * 2}{raw[3] * 2}'.lower()
        return raw.lower()

    def format_value(self, value):
        raw = self._normalize_hex(str(value or ''))
        return raw or self.default_color

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['default_color'] = self.default_color
        context['widget']['value'] = self.format_value(value)
        return context


def tinymce_widget() -> CmsTinyMCE:
    return CmsTinyMCE(mce_attrs=TINYMCE_SIMPLE)
