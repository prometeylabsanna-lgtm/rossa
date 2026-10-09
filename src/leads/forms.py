from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from leads.catalog_sync import resolve_order_catalog_snapshot
from leads.idempotency import new_idempotency_key
from leads.models import ContactLead, Fulfillment, OrderRequest, PartnershipLead
from leads.validators import (
    MSG_EMAIL_INVALID,
    MSG_REQUIRED,
    validate_person_name,
    validate_ua_phone,
)

PHONE_PLACEHOLDER = '+38 (___) ___ - __ - __'
# Без autofill-токенів website/url — інакше Safari може «заспамити» пастку.
HONEYPOT_FIELD = 'rossa_hp'


def _attrs(*extra_classes: str, **attrs) -> dict:
    classes = ['form__control', *extra_classes]
    existing = attrs.pop('class', '')
    if existing:
        classes.extend(str(existing).split())
    attrs['class'] = ' '.join(dict.fromkeys(classes))
    return attrs


class PersonNameField(forms.CharField):
    default_error_messages = {
        'required': MSG_REQUIRED,
    }

    def clean(self, value):
        value = super().clean(value)
        if value in (None, ''):
            return value
        return validate_person_name(value)


class UaPhoneField(forms.CharField):
    default_error_messages = {
        'required': MSG_REQUIRED,
    }

    def clean(self, value):
        value = super().clean(value)
        if value in (None, ''):
            return value
        return validate_ua_phone(value)


class LeadFormMixin:
    """Класи is-invalid / is-valid після перевірки + attrs для JS."""

    def _mark_validity(self):
        if not self.is_bound:
            return
        for name, field in self.fields.items():
            classes = [
                c for c in str(field.widget.attrs.get('class', '')).split()
                if c and c not in {'is-invalid', 'is-valid'}
            ]
            if name in self.errors:
                classes.append('is-invalid')
            elif name in getattr(self, 'cleaned_data', {}):
                if name == HONEYPOT_FIELD:
                    continue
                if not isinstance(field.widget, (forms.HiddenInput, forms.CheckboxInput, forms.RadioSelect)):
                    classes.append('is-valid')
            field.widget.attrs['class'] = ' '.join(classes)

    def is_valid(self):
        valid = super().is_valid()
        self._mark_validity()
        return valid


class IdempotencyKeyMixin:
    """Hidden idempotency_key (через __init__ — ModelForm не збирає Field з не-Form міксінів)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['idempotency_key'] = forms.CharField(
            max_length=64,
            widget=forms.HiddenInput,
            required=True,
            error_messages={'required': MSG_REQUIRED},
        )
        if not self.is_bound and not self.initial.get('idempotency_key'):
            self.fields['idempotency_key'].initial = new_idempotency_key()


class HoneypotMixin:
    """Поле-пастка для ботів (має лишатися порожнім)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[HONEYPOT_FIELD] = forms.CharField(
            required=False,
            label='Leave blank',
            widget=forms.TextInput(attrs={
                'class': 'form__hp-control',
                'tabindex': '-1',
                'autocomplete': 'new-password',
                'autocapitalize': 'off',
                'spellcheck': 'false',
                'aria-hidden': 'true',
            }),
        )

    def honeypot_tripped(self) -> bool:
        if not hasattr(self, 'cleaned_data'):
            return bool((self.data.get(HONEYPOT_FIELD) or '').strip())
        return bool((self.cleaned_data.get(HONEYPOT_FIELD) or '').strip())


class OrderForm(HoneypotMixin, IdempotencyKeyMixin, LeadFormMixin, forms.ModelForm):
    name = PersonNameField(label=_('ПІБ'), max_length=128, widget=forms.TextInput(attrs=_attrs(
        placeholder=_('ПІБ'),
        autocomplete='name',
        required=True,
        **{'data-validate': 'name'},
    )))
    phone = UaPhoneField(label=_('Телефон'), max_length=32, widget=forms.TextInput(attrs=_attrs(
        placeholder=PHONE_PLACEHOLDER,
        type='tel',
        inputmode='tel',
        autocomplete='tel',
        required=True,
        **{'data-validate': 'phone'},
    )))
    email = forms.EmailField(
        label=_('E-mail'),
        required=False,
        error_messages={'invalid': MSG_EMAIL_INVALID},
        widget=forms.EmailInput(attrs=_attrs(
            placeholder=_('E-mail'),
            autocomplete='email',
            **{'data-validate': 'email'},
        )),
    )
    comment = forms.CharField(label=_('Коментар'), required=False, widget=forms.Textarea(attrs=_attrs(
        placeholder=_('Коментар'),
        rows=2,
    )))
    fulfillment = forms.ChoiceField(
        label=_('Спосіб отримання'),
        choices=Fulfillment.choices,
        widget=forms.RadioSelect,
        error_messages={'required': MSG_REQUIRED},
    )
    consent = forms.BooleanField(
        label=_('Згода на обробку персональних даних'),
        required=True,
        error_messages={'required': MSG_REQUIRED},
    )

    class Meta:
        model = OrderRequest
        fields = [
            'product_name', 'product_slug', 'fabric_name', 'shade_name',
            'sku', 'price', 'name', 'phone', 'email', 'comment',
            'fulfillment', 'consent',
        ]
        widgets = {
            'product_name': forms.HiddenInput(),
            'product_slug': forms.HiddenInput(),
            'fabric_name': forms.HiddenInput(),
            'shade_name': forms.HiddenInput(),
            'sku': forms.HiddenInput(),
            'price': forms.HiddenInput(),
        }

    def clean(self):
        cleaned = super().clean()
        slug = cleaned.get('product_slug') or self.data.get('product_slug', '')
        fabric_name = cleaned.get('fabric_name') or self.data.get('fabric_name', '')
        try:
            snapshot = resolve_order_catalog_snapshot(
                product_slug=slug,
                fabric_name=fabric_name,
            )
        except DjangoValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc
        cleaned.update(snapshot)
        return cleaned


class PartnershipForm(HoneypotMixin, IdempotencyKeyMixin, LeadFormMixin, forms.ModelForm):
    name = PersonNameField(label=_('Ім’я'), max_length=128, widget=forms.TextInput(attrs=_attrs(
        placeholder=_('введіть ім’я'),
        required=True,
        autocomplete='name',
        **{'data-validate': 'name'},
    )))
    phone = UaPhoneField(label=_('Телефон'), max_length=32, widget=forms.TextInput(attrs=_attrs(
        placeholder=PHONE_PLACEHOLDER,
        type='tel',
        inputmode='tel',
        required=True,
        autocomplete='tel',
        **{'data-validate': 'phone'},
    )))
    email = forms.EmailField(
        label=_('Електронна адреса'),
        error_messages={
            'required': MSG_REQUIRED,
            'invalid': MSG_EMAIL_INVALID,
        },
        widget=forms.EmailInput(attrs=_attrs(
            placeholder=_('введіть електронну адресу'),
            required=True,
            autocomplete='email',
            **{'data-validate': 'email'},
        )),
    )
    city = forms.CharField(
        label=_('Місто'),
        max_length=128,
        error_messages={'required': MSG_REQUIRED},
        widget=forms.TextInput(attrs=_attrs(
            placeholder=_('введіть місто'),
            required=True,
            autocomplete='address-level2',
            **{'data-validate': 'required'},
        )),
    )
    message = forms.CharField(label=_('Повідомлення'), required=False, widget=forms.Textarea(attrs=_attrs(
        placeholder=_('введіть повідомлення'),
        rows=4,
    )))

    class Meta:
        model = PartnershipLead
        fields = ['name', 'phone', 'email', 'city', 'message']

    def __init__(self, *args, page=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = page
        self.submit_label = _('Надіслати')
        if page is None:
            return
        self.submit_label = getattr(page, 'form_submit_label', None) or self.submit_label
        for key in ('name', 'phone', 'email', 'city', 'message'):
            copy = page.field_copy(key) if hasattr(page, 'field_copy') else {}
            label = (copy.get('label') or '').strip()
            placeholder = (copy.get('placeholder') or '').strip()
            if label:
                self.fields[key].label = label
            if placeholder and key != 'phone':
                self.fields[key].widget.attrs['placeholder'] = placeholder

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.company = instance.company or instance.name
        instance.consent = True
        if commit:
            instance.save()
        return instance


class ContactForm(HoneypotMixin, IdempotencyKeyMixin, LeadFormMixin, forms.ModelForm):
    name = PersonNameField(label=_('Ім’я'), max_length=128, widget=forms.TextInput(attrs=_attrs(
        placeholder=_('Ім’я'),
        required=True,
        autocomplete='name',
        **{'data-validate': 'name'},
    )))
    phone = UaPhoneField(label=_('Телефон'), max_length=32, widget=forms.TextInput(attrs=_attrs(
        placeholder=PHONE_PLACEHOLDER,
        type='tel',
        inputmode='tel',
        required=True,
        autocomplete='tel',
        **{'data-validate': 'phone'},
    )))
    message = forms.CharField(
        label=_('Повідомлення'),
        error_messages={'required': MSG_REQUIRED},
        widget=forms.Textarea(attrs=_attrs(
            placeholder=_('Повідомлення'),
            rows=4,
            required=True,
            **{'data-validate': 'required'},
        )),
    )
    consent = forms.BooleanField(
        label=_('Згода на обробку персональних даних'),
        required=True,
        error_messages={'required': MSG_REQUIRED},
    )

    class Meta:
        model = ContactLead
        fields = ['name', 'phone', 'message', 'consent']

