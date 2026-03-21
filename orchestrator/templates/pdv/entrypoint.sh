#!/bin/sh
sed \
  -e "s|{{SUPABASE_URL}}|${SUPABASE_URL}|g" \
  -e "s|{{SUPABASE_KEY}}|${SUPABASE_KEY}|g" \
  -e "s|{{CLIENTE_ID}}|${CLIENTE_ID}|g" \
  -e "s|{{PLANO}}|${PLANO}|g" \
  /tmp/app.html > /usr/share/nginx/html/index.html
nginx -g "daemon off;"
