ARG BASE_IMAGE=ghcr.io/open-webui/open-webui
ARG OWUI_VERSION=latest
FROM ${BASE_IMAGE}:${OWUI_VERSION}

COPY docker/owui/start.sh /app/backend
COPY docker/owui/provision.sh /app/backend
