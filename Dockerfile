FROM python:3.5
MAINTAINER Me

ENV APP_HOME /var/app

RUN mkdir -p ${APP_HOME}
WORKDIR ${APP_DIR}
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD async_http_proxy.py .
CMD python async_http_proxy.py
