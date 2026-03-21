FROM nginx:alpine
COPY hub.html /tmp/hub.html
COPY lista-compras-saas.html /tmp/listafacil.html
COPY contagem.html /tmp/contagem.html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
