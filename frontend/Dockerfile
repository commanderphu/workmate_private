FROM ghcr.io/cirruslabs/flutter:stable AS build

WORKDIR /app

ARG API_URL=https://api.workmate-private.intern.phudevelopement.xyz/api/v1

COPY pubspec.yaml pubspec.lock* ./
RUN flutter pub get

COPY . .

RUN echo "API_URL=${API_URL}" > .env

RUN flutter build web --release

FROM nginx:alpine

COPY --from=build /app/build/web /usr/share/nginx/html
# Explizit sicherstellen dass der FCM Service Worker vorhanden ist
COPY web/firebase-messaging-sw.js /usr/share/nginx/html/firebase-messaging-sw.js
RUN chmod -R 755 /usr/share/nginx/html

RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
