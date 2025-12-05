ARG BASE_IMAGE=clickhouse/clickhouse-server
ARG CLICKHOUSE_VERSION=latest
FROM ${BASE_IMAGE}:${CLICKHOUSE_VERSION}

# This Dockerfile extends the base clickhouse image

# Disable Metric Collection, which causes high cpu load on local dev.
COPY docker/clickhouse/conf.d/disable_metric_log.xml /etc/clickhouse-server/config.d/disable_metric_log.xml