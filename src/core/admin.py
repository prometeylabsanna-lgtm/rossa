from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

# Імпорт реєструє ModelAdmin сторінок / шапки / підвалу.
import core.admin_chrome  # noqa: F401
import core.admin_pages  # noqa: F401


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
