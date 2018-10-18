#!/bin/bash

echo "---- Modifying ODK Aggregate server conf template ----"
envsubst < /etc/nginx/sites-available/app_https.template | tee /etc/nginx/sites-available/app_https && echo

echo "---- Creating symlinks ----"
mkdir -p /etc/nginx/sites-enabled
ln -s /etc/nginx/sites-available/app_http /etc/nginx/sites-enabled/app_http
ln -s /etc/nginx/sites-available/app_https /etc/nginx/sites-enabled/app_https


nginx -g 'daemon off;'
