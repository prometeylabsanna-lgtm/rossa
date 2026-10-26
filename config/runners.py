"""Пошук тестів у додатках з src/, коли лейбли не передані."""
from django.test.runner import DiscoverRunner

# Пакети лежать у src/, а src додається в sys.path у manage.py.
DEFAULT_TEST_LABELS = ('core', 'catalog', 'leads')


class RossaDiscoverRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            test_labels = list(DEFAULT_TEST_LABELS)
        return super().build_suite(test_labels, **kwargs)
