# pull official base image
FROM tiangolo/uwsgi-nginx:python3.8-alpine

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV IS_DOCKER_CONTAINER Yes

ENV LOG_LEVEL INFO
ENV APP_METRICS_PORT 9531
ENV NGINX_METRICS_PORT 9532
ENV UWSGI_STATS_PORT 1717
ENV prometheus_multiproc_dir /tmp
ENV ENCOPUS 1

# set work directory
WORKDIR /usr/src/app/

#RUN apk --no-cache add --virtual bash mariadb-connector-c
RUN apk --no-cache add bash \
	curl  \
	git \
	py3-magic \
	opus-tools

# RUN apk add --no-cache --virtual .build-deps \
# 		gcc \
# 		musl-dev \
# 		libmagic

# install dependencies
RUN pip install --upgrade pip
RUN pip install pipenv
COPY ./Pipfile /usr/src/app/Pipfile
RUN pipenv install --skip-lock --system

# copy project
COPY kzdroe /usr/src/app/kzdroe/
COPY *.md /usr/src/app/kzdroe/
COPY conf/uwsgi.ini /app/
COPY conf/nginx/ /etc/nginx/conf.d/

WORKDIR /usr/src/app/kzdroe/
RUN python setup.py install
# CMD python kzdroe/app.py

# run entrypoint.sh
# ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
# RUN apk del .build-deps
