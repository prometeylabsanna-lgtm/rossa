from __future__ import annotations

from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin, TabularInline

from core.admin_mixins import (
    STYLE_TAB,
    CmsWidgetsAdminMixin,
    PageStyleFieldsMixin,
    SingletonAdminMixin,
)
from core.models import (
    AboutPage,
    CollabPage,
    ContactsPage,
    DeliveryPage,
    HeroSlide,
    HomePage,
    OfferPage,
    PrivacyPage,
    ValueProp,
)
from core.models_styles import PageStyle
from core.page_styles import LEGAL_PAGE_DEFAULTS, ensure_legal_pages


class HeroSlideInline(TabularInline):
    model = HeroSlide
    extra = 0
    fields = (
        'image',
        'image_alt_uk', 'image_alt_ru',
        'sort', 'is_active',
    )
    ordering = ('sort', 'id')
    tab = True
    verbose_name = 'Слайд банера'
    verbose_name_plural = 'Слайди банера'


class HomePageForm(PageStyleFieldsMixin, forms.ModelForm):
    style_page_key = PageStyle.PAGE_HOME

    class Meta:
        model = HomePage
        fields = '__all__'


class AboutPageForm(PageStyleFieldsMixin, forms.ModelForm):
    style_page_key = PageStyle.PAGE_ABOUT

    class Meta:
        model = AboutPage
        fields = '__all__'

    def clean_evolution_images(self):
        items = self.cleaned_data.get('evolution_images') or []
        return [i for i in items if str(i.get('image') or '').strip()]

    def clean_craft_images(self):
        items = self.cleaned_data.get('craft_images') or []
        return [i for i in items if str(i.get('image') or '').strip()]

    def clean_logo_images(self):
        items = self.cleaned_data.get('logo_images') or []
        return [i for i in items if str(i.get('image') or '').strip()]

    def clean_milestones(self):
        from core.cms_text import ensure_cms_html_in_mapping
        items = self.cleaned_data.get('milestones') or []
        out = []
        for item in items:
            year = str(item.get('year') or '').strip()
            if not year and not str(item.get('body_uk') or '').strip() and not str(item.get('body_ru') or '').strip():
                continue
            cleaned = ensure_cms_html_in_mapping(item, 'body_uk', 'body_ru')
            cleaned['year'] = year
            out.append(cleaned)
        return out


class CollabPageForm(PageStyleFieldsMixin, forms.ModelForm):
    style_page_key = PageStyle.PAGE_COLLAB

    class Meta:
        model = CollabPage
        fields = '__all__'


class ContactsPageForm(PageStyleFieldsMixin, forms.ModelForm):
    style_page_key = PageStyle.PAGE_CONTACTS

    class Meta:
        model = ContactsPage
        fields = '__all__'


class DeliveryPageForm(PageStyleFieldsMixin, forms.ModelForm):
    style_page_key = PageStyle.PAGE_DELIVERY

    class Meta:
        model = DeliveryPage
        fields = '__all__'


class OfferPageForm(PageStyleFieldsMixin, forms.ModelForm):
    style_page_key = PageStyle.PAGE_OFFER

    class Meta:
        model = OfferPage
        fields = '__all__'


class PrivacyPageForm(PageStyleFieldsMixin, forms.ModelForm):
    style_page_key = PageStyle.PAGE_PRIVACY

    class Meta:
        model = PrivacyPage
        fields = '__all__'


@admin.register(HomePage)
class HomePageAdmin(CmsWidgetsAdminMixin, SingletonAdminMixin, ModelAdmin):
    form = HomePageForm
    inlines = (HeroSlideInline,)
    fieldsets = (
        ('Контент (укр)', {
            'classes': ('tab',),
            'fields': (
                'section_categories_uk',
                'section_bestsellers_uk',
                'about_title_uk',
                'about_body_uk',
                'about_video',
                'craft_title_uk',
                'craft_body_uk',
                'craft_link_uk',
                'craft_image',
                'cta_banner_title_uk',
                'seo_title_uk',
                'seo_description_uk',
            ),
        }),
        ('Контент (ру)', {
            'classes': ('tab',),
            'fields': (
                'section_categories_ru',
                'section_bestsellers_ru',
                'about_title_ru',
                'about_body_ru',
                'craft_title_ru',
                'craft_body_ru',
                'craft_link_ru',
                'cta_banner_title_ru',
                'seo_title_ru',
                'seo_description_ru',
            ),
        }),
        ('Оформлення', STYLE_TAB),
    )

    def changelist_view(self, request, extra_context=None):
        obj = HomePage.load()
        return HttpResponseRedirect(reverse('admin:core_homepage_change', args=[obj.pk]))


@admin.register(AboutPage)
class AboutPageAdmin(CmsWidgetsAdminMixin, SingletonAdminMixin, ModelAdmin):
    form = AboutPageForm
    fieldsets = (
        ('Контент (укр)', {
            'classes': ('tab',),
            'fields': (
                'title_uk',
                'subtitle_uk',
                'body_uk',
                'milestones_title_uk',
                'milestones',
                'craft_images',
                'logo_images',
                'evolution_title_uk',
                'evolution_images',
                'seo_title_uk',
                'seo_description_uk',
            ),
        }),
        ('Контент (ру)', {
            'classes': ('tab',),
            'fields': (
                'title_ru',
                'subtitle_ru',
                'body_ru',
                'milestones_title_ru',
                'evolution_title_ru',
                'seo_title_ru',
                'seo_description_ru',
            ),
        }),
        ('Оформлення', STYLE_TAB),
    )

    def changelist_view(self, request, extra_context=None):
        obj = AboutPage.load()
        return HttpResponseRedirect(reverse('admin:core_aboutpage_change', args=[obj.pk]))


@admin.register(CollabPage)
class CollabPageAdmin(CmsWidgetsAdminMixin, SingletonAdminMixin, ModelAdmin):
    form = CollabPageForm
    fieldsets = (
        ('Контент (укр)', {
            'classes': ('tab',),
            'fields': (
                'title_uk',
                'sub_uk',
                'hero_image',
                'advantages_title_uk',
                'benefits',
                'dealer_support_title_uk',
                'dealer_support',
                'form_title_uk',
                'form_fields',
                'form_image',
                'seo_title_uk',
                'seo_description_uk',
            ),
        }),
        ('Контент (ру)', {
            'classes': ('tab',),
            'fields': (
                'title_ru',
                'sub_ru',
                'advantages_title_ru',
                'dealer_support_title_ru',
                'form_title_ru',
                'seo_title_ru',
                'seo_description_ru',
            ),
        }),
        ('Оформлення', STYLE_TAB),
    )

    def changelist_view(self, request, extra_context=None):
        obj = CollabPage.load()
        return HttpResponseRedirect(reverse('admin:core_collabpage_change', args=[obj.pk]))


@admin.register(ContactsPage)
class ContactsPageAdmin(CmsWidgetsAdminMixin, SingletonAdminMixin, ModelAdmin):
    form = ContactsPageForm
    fieldsets = (
        ('Контент (укр)', {
            'classes': ('tab',),
            'fields': (
                'title_uk',
                'intro_uk',
                'form_title_uk',
                'seo_title_uk',
                'seo_description_uk',
            ),
        }),
        ('Контент (ру)', {
            'classes': ('tab',),
            'fields': (
                'title_ru',
                'intro_ru',
                'form_title_ru',
                'seo_title_ru',
                'seo_description_ru',
            ),
        }),
        ('Оформлення', STYLE_TAB),
    )

    def changelist_view(self, request, extra_context=None):
        obj = ContactsPage.load()
        return HttpResponseRedirect(reverse('admin:core_contactspage_change', args=[obj.pk]))


class LegalSlugAdmin(CmsWidgetsAdminMixin, ModelAdmin):
    page_key = ''
    slug = ''

    fieldsets = (
        ('Контент (укр)', {
            'classes': ('tab',),
            'fields': (
                'title_uk',
                'body_uk',
                'is_active',
                'seo_title_uk',
                'seo_description_uk',
            ),
        }),
        ('Контент (ру)', {
            'classes': ('tab',),
            'fields': (
                'title_ru',
                'body_ru',
                'seo_title_ru',
                'seo_description_ru',
            ),
        }),
        ('Оформлення', STYLE_TAB),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ('slug',)

    def _ensure(self):
        ensure_legal_pages()
        defaults = LEGAL_PAGE_DEFAULTS[self.page_key]
        from core.models_content import LegalPage
        obj, _ = LegalPage.objects.get_or_create(
            slug=defaults['slug'],
            defaults={
                'title_uk': defaults['title_uk'],
                'title_ru': defaults.get('title_ru', ''),
                'body_uk': defaults.get('body_uk', ''),
                'is_active': True,
            },
        )
        return obj

    def changelist_view(self, request, extra_context=None):
        obj = self._ensure()
        return HttpResponseRedirect(
            reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change', args=[obj.pk]),
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(slug=self.slug)


@admin.register(DeliveryPage)
class DeliveryPageAdmin(LegalSlugAdmin):
    page_key = PageStyle.PAGE_DELIVERY
    slug = 'otrymannya'
    form = DeliveryPageForm


@admin.register(OfferPage)
class OfferPageAdmin(LegalSlugAdmin):
    page_key = PageStyle.PAGE_OFFER
    slug = 'oferta'
    form = OfferPageForm


@admin.register(PrivacyPage)
class PrivacyPageAdmin(LegalSlugAdmin):
    page_key = PageStyle.PAGE_PRIVACY
    slug = 'privacy'
    form = PrivacyPageForm


@admin.register(ValueProp)
class ValuePropAdmin(CmsWidgetsAdminMixin, ModelAdmin):
    list_display = ('number', 'title_uk', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')
    fieldsets = (
        ('Контент (укр)', {
            'classes': ('tab',),
            'fields': (
                'number',
                'title_uk',
                'body_uk',
                'sort',
                'is_active',
            ),
        }),
        ('Контент (ру)', {
            'classes': ('tab',),
            'fields': (
                'title_ru',
                'body_ru',
            ),
        }),
    )
