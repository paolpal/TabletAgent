FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html app.js suggestions.js marked.min.js style.css *.svg *.png manifest.webmanifest /usr/share/nginx/html/
