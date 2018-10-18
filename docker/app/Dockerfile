FROM debian:jessie

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8
ENV MINICONDA_PACKAGE Miniconda3-4.3.11-Linux-x86_64.sh
ENV PYT_VERSION python3.6

RUN apt-get update &&\
    apt-get -y install tk-dev curl postgresql-client libpq-dev libgeos-c1 &&\
    apt-get clean

ENV PATH=/miniconda/bin:${PATH}
ENV PYTHONPATH=/miniconda/lib/${PYT_VERSION}/site-packages

RUN curl -LO https://repo.continuum.io/miniconda/${MINICONDA_PACKAGE} &&\
    bash ${MINICONDA_PACKAGE} -p /miniconda -b &&\
    rm ${MINICONDA_PACKAGE} &&\
    conda update -y conda &&\
    conda install -y pandas scipy &&\
    pip install uwsgi

RUN mkdir -p /var/www/ebola_prediction
WORKDIR /var/www

# Install pip requirements. Add requirements list to bust-cache if any changes.
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Add all above dependancies to the python path.  Do it late in the process so it is easy to change without breaking cache.
ADD docker/app/uwsgi/app.ini /var/www/uwsgi/app.ini
ADD docker/app/run /usr/bin/run
WORKDIR /var/www/ebola_prediction

CMD ["run"]
