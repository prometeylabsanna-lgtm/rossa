FROM nginx:1.27-alpine

RUN apk add --no-cache openssl \
  && mkdir -p /etc/nginx/snippets /var/www/certbot \
  && rm -f /etc/nginx/conf.d/default.conf

COPY ./deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./deploy/nginx/ssl-params.conf /etc/nginx/snippets/ssl-params.conf
COPY ./deploy/nginx/docker-entrypoint.sh /docker-entrypoint-ssl.sh
RUN chmod +x /docker-entrypoint-ssl.sh

EXPOSE 80 443
ENTRYPOINT ["/docker-entrypoint-ssl.sh"]
