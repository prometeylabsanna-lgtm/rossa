#!/usr/bin/env sh
# Перший випуск Let's Encrypt (webroot через nginx).
# На дроплеті:
#   cd /var/www/rossa && bash scripts/init-letsencrypt.sh
set -eu

DOMAIN="${SSL_DOMAIN:-rossamebel.com.ua}"
WWW_DOMAIN="${SSL_WWW_DOMAIN:-www.rossamebel.com.ua}"
EMAIL="${SSL_EMAIL:-hello@rossamebel.com.ua}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

cd "$(dirname "$0")/.."

echo "==> Прибираю тимчасовий self-signed (якщо був)"
${COMPOSE} run --rm --entrypoint sh certbot -c "\
  rm -rf /etc/letsencrypt/live/${DOMAIN} \
         /etc/letsencrypt/archive/${DOMAIN} \
         /etc/letsencrypt/renewal/${DOMAIN}.conf \
"

echo "==> Випуск сертифіката Let's Encrypt для ${DOMAIN} + ${WWW_DOMAIN}"
${COMPOSE} run --rm --entrypoint certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "${EMAIL}" \
  --agree-tos \
  --no-eff-email \
  -d "${DOMAIN}" \
  -d "${WWW_DOMAIN}"

echo "==> Перезапуск nginx"
${COMPOSE} restart nginx

echo "==> Готово: https://${DOMAIN}/"
echo "Оновіть .env: SECURE_SSL_REDIRECT=True, CSRF_TRUSTED_ORIGINS=https://${DOMAIN},https://${WWW_DOMAIN}"
echo "Потім: ${COMPOSE} up -d --force-recreate backend"
