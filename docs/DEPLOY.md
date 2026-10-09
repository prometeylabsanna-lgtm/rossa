# Деплой ROSSA на DigitalOcean Droplet

## 1. Сервер
- Ubuntu 24.04, Docker + Docker Compose plugin
- DNS A-запис домену → IP дроплета

## 2. Репозиторій на сервері
```bash
git clone <repo> /var/www/rossa && cd /var/www/rossa
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

## 4. HTTPS (Let's Encrypt) — rossamebel.com.ua

Перед цим:
- DNS A: `rossamebel.com.ua` і `www.rossamebel.com.ua` → IP дроплета
- у DO Firewall відкриті **80** і **443**

```bash
cd /var/www/rossa
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# перший сертифікат (email: hello@rossamebel.com.ua)
bash scripts/init-letsencrypt.sh
```

Потім у `.env`:

```env
ALLOWED_HOSTS=rossamebel.com.ua,www.rossamebel.com.ua
CSRF_TRUSTED_ORIGINS=https://rossamebel.com.ua,https://www.rossamebel.com.ua
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate backend
```

Перевірка: `curl -sI https://rossamebel.com.ua/healthz/`

Адмінка: `https://rossamebel.com.ua/rossa-panel/`

Опційно — щотижневий reload nginx після renew (cron на хості):

```bash
0 4 * * 1 cd /var/www/rossa && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T nginx nginx -s reload
```

## 5. Статика / медіа
nginx віддає `/static/` і `/media/` з томів `static_volume` / `media_volume`.
`collectstatic` виконується в `deploy/backend/entrypoint.sh`.

## 6. Оновлення
```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
При старті backend сам виконує `ensure_about_media` (craft-фото «Про нас» → `media_volume`).
seed_demo ідемпотентний і не перезаписує вже змінений контент.

Якщо медіа все одно порожні:
```bash
docker compose exec backend python manage.py ensure_about_media --force
docker compose exec backend python manage.py seed_demo
```

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

