# Деплой ROSSA на DigitalOcean Droplet

## 1. Сервер
- Ubuntu 24.04, Docker + Docker Compose plugin
- DNS A-запис домену → IP дроплета

## 2. Репозиторій на сервері
```bash
git clone <repo> /opt/rossa && cd /opt/rossa
cp .env.example .env
# заповнити SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, POSTGRES_*, MANAGER_EMAIL
```

## 3. Перший запуск (HTTP)
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose exec backend python manage.py seed_demo
docker compose exec backend python manage.py createsuperuser
```

Перевірка: `curl http://127.0.0.1/healthz/`

## 4. HTTPS
Після DNS:
- `SECURE_SSL_REDIRECT=True` у `.env`
- сертифікат через certbot / `django-docker-ssl` (nginx 443 + Let's Encrypt)

## 5. Статика / медіа
nginx віддає `/static/` і `/media/` з томів `static_volume` / `media_volume`.
`collectstatic` виконується в `deploy/backend/entrypoint.sh`.

## 6. Оновлення
```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
seed_demo ідемпотентний і не перезаписує вже змінений контент.

---

## Тестовий деплой на Vercel (Hobby, без env)

Підготовлено для безкоштовного Vercel **без змінних середовища** на дашборді.

### Що всередині
- `config.settings.vercel` — демо `SECRET_KEY`, SQLite, WhiteNoise
- `api/index.py` — WSGI entrypoint
- `scripts/build_vercel.sh` — migrate + seed_demo + collectstatic
- `requirements-vercel.txt` — без Postgres/gunicorn

### Обмеження демо
- Дані заявок/сесій у `/tmp` — губляться після cold start
- Адмінку підключимо пізніше (createsuperuser)
- Медіа лише з seed зі `static/images` (папка `media/` у git не їде)
- Hobby: cold start + перший seed можуть бути повільними

### Кроки в Vercel
1. Import репо `prometeylabsanna-lgtm/rossa`
2. Framework Preset: **Other** (або Django, якщо підхопить `manage.py`)
3. Root Directory: `.`
4. **Не додавати** Environment Variables
5. Deploy — entrypoint: `config.wsgi:application` (`pyproject.toml` → `[tool.vercel]`)

Локальна перевірка збірки:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-vercel.txt
bash scripts/build_vercel.sh
DJANGO_SETTINGS_MODULE=config.settings.vercel python3 manage.py runserver
```

