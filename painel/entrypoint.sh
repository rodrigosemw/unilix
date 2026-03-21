#!/bin/sh
sed \
  -e "s|__MASTER_URL__|${MASTER_URL}|g" \
  -e "s|__MASTER_KEY__|${MASTER_KEY}|g" \
  -e "s|__MASTER_PASS__|${MASTER_PASS}|g" \
  -e "s|__ORCH_URL__|${ORCH_URL}|g" \
  /tmp/painel.html > /usr/share/nginx/html/index.html
nginx -g "daemon off;"
