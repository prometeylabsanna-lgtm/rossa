from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from core.models import AboutPage, CollabPage, HomePage, LegalPage, SiteSettings, ValueProp


class SingletonAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Контакти', {'fields': ('phone', 'email', 'telegram_url', 'telegram_handle', 'logo', 'map_image')}),
        ('Адреса', {'fields': ('address_uk', 'address_ru', 'hours_uk', 'hours_ru')}),
        ('Підвал / PDP', {
            'fields': (
                'footer_tagline_uk', 'footer_tagline_ru',
                'guarantee_uk', 'guarantee_ru',
                'delivery_label_uk', 'delivery_label_ru',
            ),
        }),
    )


@admin.register(HomePage)
class HomePageAdmin(SingletonAdmin):
    fieldsets = (
        ('Hero', {
            'fields': (
                'hero_title_uk', 'hero_title_ru', 'hero_sub_uk', 'hero_sub_ru',
                'cta_catalog_uk', 'cta_catalog_ru', 'hero_poster', 'hero_video',
            ),
        }),
        ('Секції', {
            'fields': (
                'section_categories_uk', 'section_categories_ru',
                'section_bestsellers_uk', 'section_bestsellers_ru',
            ),
        }),
        ('Майстерня', {
            'fields': (
                'craft_title_uk', 'craft_title_ru', 'craft_body_uk', 'craft_body_ru',
                'craft_link_uk', 'craft_link_ru', 'craft_image',
                'cta_banner_title_uk', 'cta_banner_title_ru',
            ),
        }),
        ('SEO', {'fields': ('seo_title_uk', 'seo_title_ru', 'seo_description_uk', 'seo_description_ru')}),
    )


@admin.register(ValueProp)
class ValuePropAdmin(ModelAdmin):
    list_display = ('number', 'title_uk', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')


@admin.register(AboutPage)
class AboutPageAdmin(SingletonAdmin):
    fieldsets = (
        (None, {'fields': ('title_uk', 'title_ru', 'body_uk', 'body_ru', 'hero_image')}),
        ('Списки (JSON)', {'fields': ('milestones', 'values', 'craft_images')}),
        ('SEO', {'fields': ('seo_title_uk', 'seo_title_ru', 'seo_description_uk', 'seo_description_ru')}),
    )


@admin.register(CollabPage)
class CollabPageAdmin(SingletonAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'title_uk', 'title_ru', 'sub_uk', 'sub_ru',
                'form_title_uk', 'form_title_ru', 'hero_image', 'benefits',
            ),
        }),
        ('SEO', {'fields': ('seo_title_uk', 'seo_title_ru', 'seo_description_uk', 'seo_description_ru')}),
    )


@admin.register(LegalPage)
class LegalPageAdmin(ModelAdmin):
    list_display = ('title_uk', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('title_uk',)}


if admin.site.is_registered(User):
    admin.site.unregister(User)
if admin.site.is_registered(Group):
    admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    def delete_model(self, request, obj):
        if obj.pk == request.user.pk:
            raise PermissionDenied
        if obj.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
            messages.error(request, 'Не можна видалити останнього суперкористувача.')
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.filter(pk=request.user.pk).exists():
            raise PermissionDenied
        remaining = User.objects.filter(is_superuser=True).exclude(pk__in=queryset.values('pk')).count()
        if remaining < 1 and queryset.filter(is_superuser=True).exists():
            messages.error(request, 'Не можна видалити останнього суперкористувача.')
            return
        super().delete_queryset(request, queryset)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
