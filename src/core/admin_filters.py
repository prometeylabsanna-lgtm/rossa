"""Dropdown list filters for Unfold admin (top bar, short titles)."""

from collections.abc import Iterator
from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.validators import EMPTY_VALUES
from django.db.models import Field, Model, QuerySet
from django.http import HttpRequest
from unfold.contrib.filters.admin.mixins import DropdownMixin, ValueMixin
from unfold.widgets import UnfoldAdminSelectWidget

FILTER_INIT_PARAM = '_f'

# Short titles instead of Django/Unfold «By …» / «За …»
FILTER_TITLES = {
    'is_active': 'Активність',
    'is_available': 'Наявність',
    'created_at': 'Дата',
    'updated_at': 'Дата',
    'status': 'Статус',
    'category': 'Категорія',
    'parent': 'Батьківська',
    'fabric': 'Тканина',
    'badge': 'Бейдж',
    'fulfillment': 'Отримання',
    'collab_type': 'Тип співпраці',
}

ALL_OPTION = ('', 'Усі')


class TopDropdownForm(forms.Form):
    """Native select that submits the filter form on change."""

    def __init__(
        self,
        name: str,
        label: str,
        choices: tuple | list,
        multiple: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fields[name] = forms.ChoiceField(
            label=label,
            required=False,
            choices=choices,
            widget=UnfoldAdminSelectWidget(
                attrs={
                    'class': 'admin-top-filter__select',
                    'onchange': 'this.form.requestSubmit()',
                },
            ),
        )


def _filter_title(field_path: str, fallback: str) -> str:
    return FILTER_TITLES.get(field_path, fallback)


class BooleanDropdownFilter(ValueMixin, DropdownMixin, admin.BooleanFieldListFilter):
    form_class = TopDropdownForm
    all_option = ALL_OPTION

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = _filter_title(field_path, str(self.title))

    def choices(self, changelist: ChangeList) -> Iterator:
        choices = [
            self.all_option,
            ('1', 'Так'),
            ('0', 'Ні'),
        ]
        yield {
            'form': self.form_class(
                label=self.title,
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value()},
            ),
        }


class ChoicesDropdownFilter(ValueMixin, DropdownMixin, admin.ChoicesFieldListFilter):
    form_class = TopDropdownForm
    all_option = ALL_OPTION

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = _filter_title(field_path, str(self.title))

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        if self.value() not in EMPTY_VALUES:
            return super().queryset(request, queryset)
        return queryset

    def choices(self, changelist: ChangeList) -> Iterator:
        choices = [self.all_option, *list(self.field.flatchoices)]
        yield {
            'form': self.form_class(
                label=self.title,
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value()},
            ),
        }


class RelatedDropdownFilter(ValueMixin, DropdownMixin, admin.RelatedFieldListFilter):
    form_class = TopDropdownForm
    all_option = ALL_OPTION

    def __init__(
        self,
        field: Field,
        request: HttpRequest,
        params: dict[str, str],
        model: type[Model],
        model_admin: admin.options.ModelAdmin,
        field_path: str,
    ) -> None:
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = _filter_title(field_path, str(self.title))

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        if self.value() not in EMPTY_VALUES:
            return super().queryset(request, queryset)
        return queryset

    def choices(self, changelist: ChangeList) -> Iterator:
        choices = [self.all_option, *self.lookup_choices]
        yield {
            'form': self.form_class(
                label=self.title,
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value()},
            ),
        }


def resolve_list_filter_item(model: type[Model], item: Any) -> Any:
    """Turn a field name into a dropdown filter tuple when possible."""
    if isinstance(item, (list, tuple)) or not isinstance(item, str):
        return item
    try:
        field = model._meta.get_field(item)
    except Exception:
        return item
    if getattr(field, 'choices', None):
        return (item, ChoicesDropdownFilter)
    if field.get_internal_type() == 'BooleanField':
        return (item, BooleanDropdownFilter)
    if field.is_relation and not field.many_to_many and field.related_model is not None:
        return (item, RelatedDropdownFilter)
    return item


BOOLEAN_DEFAULT_TRUE = frozenset({'is_active', 'is_available'})


def default_param_for_field(model: type[Model], field_name: str) -> tuple[str, str] | None:
    """Return (lookup, value) default for a list_filter field, if any."""
    try:
        field = model._meta.get_field(field_name)
    except Exception:
        return None
    if field.get_internal_type() == 'BooleanField' and field_name in BOOLEAN_DEFAULT_TRUE:
        return (f'{field_name}__exact', '1')
    # Only status gets a concrete default (usually «Нове»); badge etc. stay «Усі»
    if field_name == 'status' and getattr(field, 'choices', None):
        for value, _label in field.flatchoices:
            if value not in EMPTY_VALUES:
                return (f'{field_name}__exact', str(value))
    return None
