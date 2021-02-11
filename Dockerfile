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
ENV S3 0

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

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="kzdroe" \
      org.label-schema.description="Here is a simple Python Flask for receiving a recording from doe.dialbox.cloud." \
      org.label-schema.url="https://www.sapian.cloud/droe" \
      org.label-schema.vcs-url="https://git.sapian.com.co/Sapian/kzdroe" \
      org.label-schema.maintainer="sebastian.rojo@sapian.com.co" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vendor1="Sapian" \
      org.label-schema.version=$VERSION \
      org.label-schema.vicidial-schema-version="1"