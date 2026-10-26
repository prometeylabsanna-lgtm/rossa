# Тести

Повний прогін:

```bash
.venv/bin/python manage.py test
```

Якщо `DJANGO_SETTINGS_MODULE` не задано в оточенні, `manage.py` для команди `test` підставляє `config.settings.test`. У `develop` ліміт заявок 10/хв, і довгий прогін отримує 429; тестові налаштування піднімають ліміт, вмикають locmem-кеш і швидкий хеш паролів. Змінна оточення або `--settings` лишаються як є.

Без лейблів раннер збирає тести додатків `core`, `catalog` і `leads` (`src` уже в `sys.path`). Явний лейбл працює як завжди:

```bash
.venv/bin/python manage.py test catalog.tests.test_google_feed
```
