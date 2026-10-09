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

echo "==> Чекаю, поки nginx слухає :80"
i=0
until curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1/" | grep -Eq '301|302|200'; do
  i=$((i + 1))
  if [ "$i" -gt 60 ]; then
    echo "ERROR: nginx не відповідає на :80. Перевір: docker compose ps && docker compose logs nginx --tail=80"
    exit 1
  fi
  sleep 2
done

echo "==> Перевірка ACME webroot з хоста"
${COMPOSE} exec -T nginx sh -c 'mkdir -p /var/www/certbot/.well-known/acme-challenge && echo ok > /var/www/certbot/.well-known/acme-challenge/ping'
code="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1/.well-known/acme-challenge/ping" || true)"
if [ "$code" != "200" ]; then
  echo "ERROR: ACME шлях недоступний локально (HTTP ${code})."
  echo "Перевір firewall: ufw status; DO Cloud Firewall — порти 80/443"
  ${COMPOSE} logs nginx --tail=50
  exit 1
fi

echo "==> Зовнішня перевірка DNS → цей сервер"
echo "    dig +short ${DOMAIN} A"
dig +short "${DOMAIN}" A || true

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
