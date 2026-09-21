import re

from django import forms
from django.utils.translation import gettext_lazy as _

from leads.models import ContactLead, Fulfillment, OrderRequest, PartnershipLead

PHONE_RE = re.compile(r'^\+?[0-9\s\-()]{10,20}$')


class PhoneField(forms.CharField):
    def clean(self, value):
        value = super().clean(value)
        if value and not PHONE_RE.match(value):
            raise forms.ValidationError(_('Вкажіть коректний телефон.'))
        return value


class OrderForm(forms.ModelForm):
    name = forms.CharField(label=_('ПІБ'), max_length=128, widget=forms.TextInput(attrs={
        'placeholder': _('ПІБ'),
        'autocomplete': 'name',
        'required': True,
    }))
    phone = PhoneField(label=_('Телефон'), widget=forms.TextInput(attrs={
        'placeholder': _('Телефон'),
        'type': 'tel',
        'autocomplete': 'tel',
        'required': True,
    }))
    email = forms.EmailField(label=_('E-mail'), required=False, widget=forms.EmailInput(attrs={
        'placeholder': _('E-mail'),
        'autocomplete': 'email',
    }))
    comment = forms.CharField(label=_('Коментар'), required=False, widget=forms.Textarea(attrs={
        'placeholder': _('Коментар'),
        'rows': 3,
    }))
    fulfillment = forms.ChoiceField(
        label=_('Спосіб отримання'),
        choices=Fulfillment.choices,
        widget=forms.RadioSelect,
    )
    consent = forms.BooleanField(label=_('Згода на обробку персональних даних'), required=True)

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


class PartnershipForm(forms.ModelForm):
    company = forms.CharField(label=_('Назва компанії / ПІБ'), widget=forms.TextInput(attrs={
        'placeholder': _('Назва компанії'),
        'required': True,
    }))
    name = forms.CharField(label=_('Ім’я'), required=False, widget=forms.TextInput(attrs={
        'placeholder': _('Ім’я'),
    }))
    phone = PhoneField(label=_('Телефон'), widget=forms.TextInput(attrs={
        'placeholder': _('Телефон'),
        'type': 'tel',
        'required': True,
    }))
    email = forms.EmailField(label=_('E-mail'), widget=forms.EmailInput(attrs={
        'placeholder': _('E-mail'),
        'required': True,
    }))
    city = forms.CharField(label=_('Місто'), required=False, widget=forms.TextInput(attrs={
        'placeholder': _('Місто'),
    }))
    message = forms.CharField(label=_('Повідомлення'), required=False, widget=forms.Textarea(attrs={
        'placeholder': _('Повідомлення'),
        'rows': 4,
    }))
    consent = forms.BooleanField(label=_('Згода на обробку персональних даних'), required=True)
    collab_type = forms.ChoiceField(
        label=_('Тип співпраці'),
        required=False,
        choices=[('', _('Тип співпраці'))] + list(PartnershipLead.CollabType.choices),
    )

    class Meta:
        model = PartnershipLead
        fields = ['company', 'name', 'phone', 'email', 'city', 'collab_type', 'message', 'consent']


class ContactForm(forms.ModelForm):
    name = forms.CharField(label=_('Ім’я'), widget=forms.TextInput(attrs={
        'placeholder': _('Ім’я'),
        'required': True,
    }))
    phone = PhoneField(label=_('Телефон'), widget=forms.TextInput(attrs={
        'placeholder': _('Телефон'),
        'type': 'tel',
        'required': True,
    }))
    message = forms.CharField(label=_('Повідомлення'), widget=forms.Textarea(attrs={
        'placeholder': _('Повідомлення'),
        'rows': 4,
        'required': True,
    }))
    consent = forms.BooleanField(label=_('Згода на обробку персональних даних'), required=True)

    class Meta:
        model = ContactLead
        fields = ['name', 'phone', 'message', 'consent']
