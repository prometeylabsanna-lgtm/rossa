from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from core.images_webp import convert_bytes_to_webp, convert_upload_to_webp, needs_webp_convert
from core.models import HeroSlide, HomePage


def _png_bytes(size=(40, 30), color=(200, 40, 40)) -> bytes:
    buf = BytesIO()
    Image.new('RGB', size, color).save(buf, format='PNG')
    return buf.getvalue()


def _gif_bytes() -> bytes:
    buf = BytesIO()
    Image.new('P', (16, 16)).save(buf, format='GIF')
    return buf.getvalue()


class WebPConvertUtilsTests(TestCase):
    def test_needs_convert(self):
        self.assertTrue(needs_webp_convert('photo.jpg'))
        self.assertTrue(needs_webp_convert('photo.PNG'))
        self.assertFalse(needs_webp_convert('photo.webp'))
        self.assertFalse(needs_webp_convert('anim.gif'))

    def test_convert_png_bytes(self):
        data = convert_bytes_to_webp(_png_bytes(), source_name='a.png')
        self.assertIsNotNone(data)
        img = Image.open(BytesIO(data))
        self.assertEqual(img.format, 'WEBP')

    def test_skip_gif_bytes(self):
        self.assertIsNone(convert_bytes_to_webp(_gif_bytes(), source_name='a.gif'))

    def test_convert_upload_renames(self):
        upload = SimpleUploadedFile('hero.png', _png_bytes(), content_type='image/png')
        result = convert_upload_to_webp('home/slides/hero.png', upload)
        self.assertIsNotNone(result)
        name, content = result
        self.assertTrue(name.endswith('.webp'))
        self.assertTrue(content.name.endswith('.webp'))


class WebPImageFieldTests(TestCase):
    def test_hero_slide_saves_as_webp(self):
        page = HomePage.load()
        slide = HeroSlide(page=page, sort=0, is_active=True)
        slide.image.save(
            'slide-test.png',
            ContentFile(_png_bytes(), name='slide-test.png'),
            save=True,
        )
        self.assertTrue(slide.image.name.endswith('.webp'))
        with slide.image.open('rb') as fh:
            img = Image.open(fh)
            self.assertEqual(img.format, 'WEBP')

    def test_gif_kept(self):
        page = HomePage.load()
        slide = HeroSlide(page=page, sort=1, is_active=True)
        slide.image.save(
            'slide.gif',
            ContentFile(_gif_bytes(), name='slide.gif'),
            save=True,
        )
        self.assertTrue(slide.image.name.endswith('.gif'))


@override_settings(ROOT_URLCONF='config.urls')
class CmsUploadWebPTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_superuser('admin', 'a@a.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

    def test_cms_upload_converts_to_webp(self):
        url = reverse('cms_upload')
        response = self.client.post(
            url,
            {
                'upload_to': 'about/evolution/',
                'file': SimpleUploadedFile('evo.png', _png_bytes(), content_type='image/png'),
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.assertTrue(payload['path'].endswith('.webp'))
        self.assertTrue(Path(payload['path']).suffix.lower() == '.webp')
