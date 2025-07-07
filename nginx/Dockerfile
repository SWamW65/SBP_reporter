FROM nginx:alpine

COPY sbpreport.conf /etc/nginx/conf.d/default.conf

WORKDIR /static
COPY ../static/ .

EXPOSE 80
