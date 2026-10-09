from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Product
from core.admin_help import (
    apply_admin_field_hints,
    hint_chars,
    hint_image_mb,
    text_char_limit,
    validate_image_max_size,
    validate_plain_text_max_length,
)
from core.models import HomePage, ValueProp


class AdminHelpUtilsTests(TestCase):
    def test_hint_wording(self):
        self.assertEqual(hint_chars(128), 'Не більше 128 символів.')
        self.assertEqual(hint_image_mb(8), 'Не більше 8 МБ.')

    def test_text_limits_by_block(self):
        self.assertEqual(text_char_limit(HomePage, 'craft_body_uk'), 220)
        self.assertEqual(text_char_limit(HomePage, 'about_body_uk'), 280)
        self.assertEqual(text_char_limit(ValueProp, 'body_uk'), 150)
        self.assertEqual(text_char_limit(Product, 'description_uk'), 500)
        self.assertEqual(text_char_limit(Product, 'seo_description_uk'), 160)

    def test_plain_text_validator(self):
        validate_plain_text_max_length(5)('abcd')
        with self.assertRaises(ValidationError):
            validate_plain_text_max_length(5)('abcdef')

    def test_image_size_validator(self):
        class _Fake:
            size = 9 * 1024 * 1024

        with self.assertRaises(ValidationError):
            validate_image_max_size(_Fake())


class AdminHelpFormfieldTests(TestCase):
    def test_char_and_image_hints_on_admin_form(self):
        User = get_user_model()
        user = User.objects.create_superuser('admin2', 'b@b.com', 'pass')
        from django.test import RequestFactory
        from catalog.admin import ProductAdmin
        from django.contrib.admin.sites import AdminSite

        request = RequestFactory().get('/')
        request.user = user
        admin = ProductAdmin(Product, AdminSite())

        name_field = Product._meta.get_field('name_uk')
        formfield = admin.formfield_for_dbfield(name_field, request)
        self.assertIn('Не більше 128 символів.', str(formfield.help_text))

        image_field = Product._meta.get_field('default_image')
        image_form = admin.formfield_for_dbfield(image_field, request)
        self.assertIn('Не більше 8 МБ.', str(image_form.help_text))

        desc_field = Product._meta.get_field('description_uk')
        desc_form = admin.formfield_for_dbfield(desc_field, request)
        self.assertIn('Не більше 500 символів.', str(desc_form.help_text))

    def test_apply_preserves_existing_help(self):
        field = Product._meta.get_field('name_uk')
        formfield = field.formfield()
        formfield.help_text = 'Існуюча підказка.'
        apply_admin_field_hints(field, formfield, model=Product)
        self.assertIn('Існуюча підказка.', str(formfield.help_text))
        self.assertIn('Не більше 128 символів.', str(formfield.help_text))
