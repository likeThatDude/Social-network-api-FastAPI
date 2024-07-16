FROM nginx:latest

RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY client/static /app/static

COPY client/nginx.conf /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]