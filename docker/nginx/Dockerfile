from nginx

RUN apt-get update \
 && apt-get install -y gettext

COPY docker/nginx/config /etc/nginx/
COPY docker/nginx/run.sh /bin/run.sh
RUN chmod +x /bin/run.sh

CMD /bin/run.sh
