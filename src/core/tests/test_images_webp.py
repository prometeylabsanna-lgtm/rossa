from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from core.images_webp import (
    convert_bytes_to_webp,
    convert_upload_to_webp,
    ensure_webp_beside,
    needs_webp_convert,
)
from core.models import AboutPage, HeroSlide, HomePage


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


class AboutGalleryWebPTests(TestCase):
    def test_json_gallery_serves_webp_picture_keeps_original(self):
        from django.core.files.storage import default_storage

        png_name = 'about/gallery-keep-original.png'
        if default_storage.exists(png_name):
            default_storage.delete(png_name)
        webp_name = 'about/gallery-keep-original.webp'
        if default_storage.exists(webp_name):
            default_storage.delete(webp_name)

        default_storage.save(png_name, ContentFile(_png_bytes((80, 60)), name='gallery-keep-original.png'))
        media_url = f'/media/{png_name}'

        page = AboutPage.load()
        page.title_uk = 'Про нас'
        page.body_uk = 'Текст'
        page.craft_images = [
            {'image': media_url, 'label_uk': 'Цех', 'label_ru': 'Цех'},
        ]
        page.logo_images = []
        page.evolution_images = []
        page.milestones = []
        page.save()

        client = Client()
        response = client.get(reverse('core:about'))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8')
        self.assertIn('type="image/webp"', body)
        self.assertIn('gallery-keep-original.webp', body)
        self.assertIn('gallery-keep-original.png', body)
        self.assertIn('width="1024"', body)
        self.assertIn('height="682"', body)
        self.assertTrue(default_storage.exists(png_name))
        self.assertTrue(default_storage.exists(webp_name))

        webp_url = ensure_webp_beside(media_url)
        self.assertTrue(webp_url.endswith('.webp'))
        # Повторний виклик не чіпає оригінал.
        with default_storage.open(png_name, 'rb') as fh:
            original = fh.read()
        ensure_webp_beside(media_url)
        with default_storage.open(png_name, 'rb') as fh:
            self.assertEqual(fh.read(), original)
