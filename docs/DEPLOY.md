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
