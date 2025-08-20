ARG BASE_IMAGE=pgvector/pgvector
ARG PGVECTOR_VERSION=pg17-bookworm
FROM ${BASE_IMAGE}:${PGVECTOR_VERSION}

RUN mkdir -p /docker-entrypoint-initdb.d
COPY config/pgvector/docker-entrypoint-initdb.d/ /docker-entrypoint-initdb.d/

