FROM python:3.6
MAINTAINER Me

ENV APP_DIR /app

RUN mkdir -p ${APP_DIR}

WORKDIR ${APP_DIR}

ADD requirements.txt .

RUN apt-get update && \
    apt-get -y upgrade && \
    pip install -r requirements.txt
