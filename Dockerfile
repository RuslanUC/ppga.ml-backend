FROM python:3.9-alpine as python

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /links

RUN python -m pip install --upgrade pip && pip install --upgrade wheel setuptools

COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

COPY . .
