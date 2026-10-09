#!/bin/sh
set -e

DOMAIN="${SSL_DOMAIN:-rossamebel.com.ua}"
LIVE="/etc/letsencrypt/live/${DOMAIN}"

if [ ! -f "${LIVE}/fullchain.pem" ] || [ ! -f "${LIVE}/privkey.pem" ]; then
  echo "SSL: тимчасовий self-signed для ${DOMAIN} (замінить certbot)"
  mkdir -p "${LIVE}"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "${LIVE}/privkey.pem" \
    -out "${LIVE}/fullchain.pem" \
    -subj "/CN=${DOMAIN}"
fi

exec nginx -g 'daemon off;'
