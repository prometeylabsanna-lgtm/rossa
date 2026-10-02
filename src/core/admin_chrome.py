from __future__ import annotations

from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin

from core.admin_mixins import CmsWidgetsAdminMixin, SingletonAdminMixin, clean_color
from core.admin_widgets import CmsAdminColorWidget
from core.models import FooterSettings, HeaderSettings, SiteSettings
from core.models_styles import ChromeStyle


class HeaderSettingsForm(forms.ModelForm):
    style_header_bg = forms.CharField(required=False, label='Шапка — фон')
    style_header_text = forms.CharField(required=False, label='Шапка — текст')

    class Meta:
        model = HeaderSettings
        fields = (
            'logo',
            'phone', 'phone_2', 'phone_3',
            'telegram_url', 'telegram_handle',
            'instagram_url', 'facebook_url', 'tiktok_url',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome = ChromeStyle.load()
        specs = (
            ('style_header_bg', ChromeStyle.DEFAULT_HEADER_BG, 'Шапка — фон', chrome.header_bg),
            ('style_header_text', ChromeStyle.DEFAULT_HEADER_TEXT, 'Шапка — текст', chrome.header_text),
        )
        for name, default, label, current in specs:
            field = self.fields[name]
            field.widget = CmsAdminColorWidget(default_color=default)
            field.label = label
            field.initial = (current or '').strip() or default
            field.help_text = f'За замовчуванням: {default}'

    def clean_style_header_bg(self):
        return clean_color(self.cleaned_data.get('style_header_bg', ''), default=ChromeStyle.DEFAULT_HEADER_BG)

    def clean_style_header_text(self):
        return clean_color(self.cleaned_data.get('style_header_text', ''), default=ChromeStyle.DEFAULT_HEADER_TEXT)

    def save(self, commit=True):
        obj = super().save(commit=commit)
        chrome = ChromeStyle.load()
        chrome.header_bg = self.cleaned_data.get('style_header_bg', '')
        chrome.header_text = self.cleaned_data.get('style_header_text', '')
        chrome.save()
        return obj


class FooterSettingsForm(forms.ModelForm):
    style_footer_top_bg = forms.CharField(required=False, label='Підвал (верх) — фон')
    style_footer_top_text = forms.CharField(required=False, label='Підвал (верх) — текст')
    style_footer_bottom_bg = forms.CharField(required=False, label='Підвал (низ) — фон')
    style_footer_bottom_text = forms.CharField(required=False, label='Підвал (низ) — текст')

    class Meta:
        model = FooterSettings
        fields = (
            'logo',
            'phone', 'phone_2', 'phone_3',
            'email',
            'address_uk', 'address_ru',
            'hours_uk', 'hours_ru',
            'footer_tagline_uk', 'footer_tagline_ru',
            'telegram_url', 'telegram_handle',
            'instagram_url', 'facebook_url', 'tiktok_url',
            'map_image',
            'guarantee_uk', 'guarantee_ru',
            'delivery_label_uk', 'delivery_label_ru',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome = ChromeStyle.load()
        specs = (
            ('style_footer_top_bg', ChromeStyle.DEFAULT_FOOTER_TOP_BG, 'Підвал (верх) — фон', chrome.footer_top_bg),
            ('style_footer_top_text', ChromeStyle.DEFAULT_FOOTER_TOP_TEXT, 'Підвал (верх) — текст', chrome.footer_top_text),
            ('style_footer_bottom_bg', ChromeStyle.DEFAULT_FOOTER_BOTTOM_BG, 'Підвал (низ) — фон', chrome.footer_bottom_bg),
            ('style_footer_bottom_text', ChromeStyle.DEFAULT_FOOTER_BOTTOM_TEXT, 'Підвал (низ) — текст', chrome.footer_bottom_text),
        )
        for name, default, label, current in specs:
            field = self.fields[name]
            field.widget = CmsAdminColorWidget(default_color=default)
            field.label = label
            field.initial = (current or '').strip() or default
            field.help_text = f'За замовчуванням: {default}'

    def clean_style_footer_top_bg(self):
        return clean_color(self.cleaned_data.get('style_footer_top_bg', ''), default=ChromeStyle.DEFAULT_FOOTER_TOP_BG)

    def clean_style_footer_top_text(self):
        return clean_color(self.cleaned_data.get('style_footer_top_text', ''), default=ChromeStyle.DEFAULT_FOOTER_TOP_TEXT)

    def clean_style_footer_bottom_bg(self):
        return clean_color(
            self.cleaned_data.get('style_footer_bottom_bg', ''),
            default=ChromeStyle.DEFAULT_FOOTER_BOTTOM_BG,
        )

    def clean_style_footer_bottom_text(self):
        return clean_color(
            self.cleaned_data.get('style_footer_bottom_text', ''),
            default=ChromeStyle.DEFAULT_FOOTER_BOTTOM_TEXT,
        )

    def save(self, commit=True):
        obj = super().save(commit=commit)
        chrome = ChromeStyle.load()
        chrome.footer_top_bg = self.cleaned_data.get('style_footer_top_bg', '')
        chrome.footer_top_text = self.cleaned_data.get('style_footer_top_text', '')
        chrome.footer_bottom_bg = self.cleaned_data.get('style_footer_bottom_bg', '')
        chrome.footer_bottom_text = self.cleaned_data.get('style_footer_bottom_text', '')
        chrome.save()
        return obj


@admin.register(HeaderSettings)
class HeaderSettingsAdmin(CmsWidgetsAdminMixin, SingletonAdminMixin, ModelAdmin):
    form = HeaderSettingsForm
    fieldsets = (
        ('Контент', {
            'classes': ('tab',),
            'fields': (
                'logo',
                'phone', 'phone_2', 'phone_3',
                'telegram_url', 'telegram_handle',
                'instagram_url', 'facebook_url', 'tiktok_url',
            ),
        }),
        ('Оформлення', {
            'classes': ('tab',),
            'fields': ('style_header_bg', 'style_header_text'),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return HttpResponseRedirect(reverse('admin:core_headersettings_change', args=[obj.pk]))


@admin.register(FooterSettings)
class FooterSettingsAdmin(CmsWidgetsAdminMixin, SingletonAdminMixin, ModelAdmin):
    form = FooterSettingsForm
    fieldsets = (
        ('Контент', {
            'classes': ('tab',),
            'fields': (
                'logo',
                'phone', 'phone_2', 'phone_3',
                'email',
                'address_uk', 'address_ru',
                'hours_uk', 'hours_ru',
                'footer_tagline_uk', 'footer_tagline_ru',
                'telegram_url', 'telegram_handle',
                'instagram_url', 'facebook_url', 'tiktok_url',
                'map_image',
                'guarantee_uk', 'guarantee_ru',
                'delivery_label_uk', 'delivery_label_ru',
            ),
        }),
        ('Оформлення', {
            'classes': ('tab',),
            'fields': (
                'style_footer_top_bg', 'style_footer_top_text',
                'style_footer_bottom_bg', 'style_footer_bottom_text',
            ),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return HttpResponseRedirect(reverse('admin:core_footersettings_change', args=[obj.pk]))
