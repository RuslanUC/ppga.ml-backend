FROM python:3.9-alpine as python

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /rbot

RUN apk update && apk add python3-dev gcc libc-dev libffi-dev make build-base alpine-sdk mysql mysql-client mariadb-connector-c-dev ffmpeg
RUN python -m pip install --upgrade pip && pip install --upgrade wheel setuptools

COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

COPY . .
