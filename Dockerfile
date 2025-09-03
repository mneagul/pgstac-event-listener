ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y build-essential git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

FROM base AS builder
WORKDIR /app
COPY . /app

RUN python -m pip install -e .
CMD ["python", "app.py"]