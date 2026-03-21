#!/bin/sh
mkdir -p /usr/share/nginx/html/estoque /usr/share/nginx/html/pdv

# Hub principal
sed -e "s|{{SUPABASE_URL}}|${SUPABASE_URL}|g" \
    -e "s|{{SUPABASE_KEY}}|${SUPABASE_KEY}|g" \
    -e "s|{{CLIENTE_ID}}|${CLIENTE_ID}|g" \
    -e "s|{{PLANO}}|${PLANO}|g" \
    /tmp/hub.html > /usr/share/nginx/html/index.html

# Módulo Estoque — ListaFácil
sed -e "s|__SUPABASE_URL__|${SUPABASE_URL}|g" \
    -e "s|__SUPABASE_KEY__|${SUPABASE_KEY}|g" \
    -e "s|__CLIENTE_ID__|${CLIENTE_ID}|g" \
    -e "s|__PLANO__|${PLANO}|g" \
    /tmp/listafacil.html > /usr/share/nginx/html/estoque/listafacil.html

# Módulo Estoque — ContagemFácil
if [ -f /tmp/contagem.html ]; then
  sed -e "s|__SUPABASE_URL__|${SUPABASE_URL}|g" \
      -e "s|__SUPABASE_KEY__|${SUPABASE_KEY}|g" \
      -e "s|__CLIENTE_ID__|${CLIENTE_ID}|g" \
      -e "s|__PLANO__|${PLANO}|g" \
      /tmp/contagem.html > /usr/share/nginx/html/estoque/contagem.html
fi

# Módulo PDV — só se o arquivo existir
if [ -f /tmp/comandafacil.html ]; then
  sed -e "s|{{SUPABASE_URL}}|${SUPABASE_URL}|g" \
      -e "s|{{SUPABASE_KEY}}|${SUPABASE_KEY}|g" \
      -e "s|{{CLIENTE_ID}}|${CLIENTE_ID}|g" \
      -e "s|{{PLANO}}|${PLANO}|g" \
      /tmp/comandafacil.html > /usr/share/nginx/html/pdv/comandafacil.html
fi

nginx -g "daemon off;"
