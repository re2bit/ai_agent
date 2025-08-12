FROM pgvector/pgvector:pg17-bookworm

RUN mkdir -p /docker-entrypoint-initdb.d
COPY config/pgvector/docker-entrypoint-initdb.d/ /docker-entrypoint-initdb.d/

