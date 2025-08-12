ARG BASE_IMAGE=ghcr.io/open-webui/pipelines
ARG PIPELINES_VERSION=main
FROM ${BASE_IMAGE}:${PIPELINES_VERSION}

RUN mkdir -p /app/pipelines

COPY src/pipelines/requirements.txt /app/pipelines

RUN cd /app/pipelines && pip install --no-cache-dir -r requirements.txt && cd /

COPY src/pipelines/agent-pipeline.py /app/pipelines