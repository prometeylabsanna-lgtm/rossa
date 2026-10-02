"""Project Unfold ModelAdmin: top dropdown filters + sensible defaults."""

from django import forms
from django.contrib.admin.views.main import ChangeList
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from core.admin_filters import (
    FILTER_INIT_PARAM,
    default_param_for_field,
    resolve_list_filter_item,
)


class RossaChangeList(ChangeList):
    """Ігнорує службовий `_f` (маркер дефолтних фільтрів), щоб Django не шукав таке поле."""

    def get_filters_params(self, params=None):
        lookup_params = super().get_filters_params(params)
        lookup_params.pop(FILTER_INIT_PARAM, None)
        return lookup_params


class ModelAdmin(UnfoldModelAdmin):
    """Filters live in the top bar as dropdowns; booleans/status get defaults."""

    list_filter_sheet = True
    list_filter_submit = True
    # None → auto defaults for boolean/status; {} → no redirect defaults
    list_filter_defaults = None

    @property
    def media(self):
        return super().media + forms.Media(
            css={'all': ('css/admin/top_filters.css',)},
            js=('js/admin/cms_payload_guard.js',),
        )

    def get_changelist(self, request, **kwargs):
        return RossaChangeList

    def get_list_filter(self, request: HttpRequest):
        raw = list(super().get_list_filter(request) or [])
        return [resolve_list_filter_item(self.model, item) for item in raw]

    def get_list_filter_defaults(self) -> dict[str, str]:
        if self.list_filter_defaults is not None:
            return dict(self.list_filter_defaults)

        defaults: dict[str, str] = {}
        raw = list(getattr(self, 'list_filter', None) or [])
        for item in raw:
            field_name = item[0] if isinstance(item, (list, tuple)) else item
            if not isinstance(field_name, str):
                continue
            pair = default_param_for_field(self.model, field_name)
            if pair:
                defaults[pair[0]] = pair[1]
        return defaults

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict | None = None,
    ) -> HttpResponse:
        self.request = request
        defaults = self.get_list_filter_defaults()
        if defaults and FILTER_INIT_PARAM not in request.GET:
            params = request.GET.copy()
            params[FILTER_INIT_PARAM] = '1'
            for key, value in defaults.items():
                if key not in params:
                    params[key] = value
            return HttpResponseRedirect(f'{request.path}?{params.urlencode()}')
        return super().changelist_view(request, extra_context)
