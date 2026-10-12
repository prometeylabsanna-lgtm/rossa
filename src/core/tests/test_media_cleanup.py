import shutil
import tempfile
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from PIL import Image

from core.media_cleanup import variant_names
from core.models import AboutPage, HeroSlide, HomePage

TMP_MEDIA = tempfile.mkdtemp(prefix='rossa_media_test_')


def _png(size=(2000, 100)) -> ContentFile:
    buf = BytesIO()
    Image.new('RGB', size, (10, 120, 200)).save(buf, format='PNG')
    return ContentFile(buf.getvalue(), name='qa.png')


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class WebPCleanupTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    def _slide(self):
        page = HomePage.objects.first() or HomePage.objects.create()
        slide = HeroSlide(page=page)
        slide.image.save('slide.png', _png(), save=True)
        return slide

    def _assert_all_exist(self, name, exists=True):
        for n in variant_names(name):
            self.assertEqual((Path(TMP_MEDIA) / n).exists(), exists, n)

    def test_variants_written(self):
        slide = self._slide()
        names = variant_names(slide.image.name)
        self.assertEqual(len(names), 4)
        self.assertTrue(all(n.endswith(s) for n, s in zip(names[1:], ('_w640.webp', '_w960.webp', '_w1600.webp'))))
        self._assert_all_exist(slide.image.name)

    def test_delete_removes_main_and_variants(self):
        slide = self._slide()
        name = slide.image.name
        with self.captureOnCommitCallbacks(execute=True):
            slide.delete()
        self._assert_all_exist(name, exists=False)

    def test_replace_removes_old_files(self):
        slide = self._slide()
        old = slide.image.name
        with self.captureOnCommitCallbacks(execute=True):
            slide.image.save('new.png', _png(), save=True)
        self.assertNotEqual(old, slide.image.name)
        self._assert_all_exist(old, exists=False)
        self._assert_all_exist(slide.image.name)

    def test_shared_file_is_kept(self):
        slide = self._slide()
        other = HeroSlide.objects.create(page=slide.page, image=slide.image.name)
        with self.captureOnCommitCallbacks(execute=True):
            slide.delete()
        self._assert_all_exist(other.image.name)

    def test_no_cleanup_without_commit(self):
        slide = self._slide()
        name = slide.image.name
        with self.captureOnCommitCallbacks(execute=False):
            slide.delete()
        self._assert_all_exist(name)


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class GalleryCleanupTests(TestCase):
    def _upload(self, prefix='about/evolution/'):
        from core.images_webp import write_variants_for_bytes
        data = _png().read()
        name = default_storage.save(f'{prefix}g.webp', ContentFile(data))
        write_variants_for_bytes(default_storage, name, data)
        return name

    def test_removed_gallery_image_deleted(self):
        page = AboutPage.objects.first() or AboutPage.objects.create(title_uk='t', body_uk='b')
        keep, drop = self._upload(), self._upload()
        page.evolution_images = [{'image': f'/media/{keep}'}, {'image': f'/media/{drop}'}]
        page.save()
        with self.captureOnCommitCallbacks(execute=True):
            page.evolution_images = [{'image': f'/media/{keep}'}]
            page.save()
        for n in variant_names(drop):
            self.assertFalse((Path(TMP_MEDIA) / n).exists(), n)
        for n in variant_names(keep):
            self.assertTrue((Path(TMP_MEDIA) / n).exists(), n)
