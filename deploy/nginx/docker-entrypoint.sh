#!/bin/sh
set -e

DOMAIN="${SSL_DOMAIN:-rossamebel.com.ua}"
LIVE="/etc/letsencrypt/live/${DOMAIN}"
DHPARAM_SRC="/etc/letsencrypt/dhparam.pem"

if [ ! -f "${LIVE}/fullchain.pem" ] || [ ! -f "${LIVE}/privkey.pem" ]; then
  echo "SSL: тимчасовий self-signed для ${DOMAIN} (замінить certbot)"
  mkdir -p "${LIVE}"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "${LIVE}/privkey.pem" \
    -out "${LIVE}/fullchain.pem" \
    -subj "/CN=${DOMAIN}"
fi

if [ ! -f "${DHPARAM_SRC}" ]; then
  echo "SSL: генерую dhparam (один раз, ~1–2 хв)…"
  openssl dhparam -out "${DHPARAM_SRC}" 2048
fi
ln -sfn "${DHPARAM_SRC}" /etc/nginx/dhparam.pem

exec nginx -g 'daemon off;'
