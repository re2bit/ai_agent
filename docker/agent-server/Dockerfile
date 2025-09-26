ARG BASE_IMAGE=python
ARG PYTHON_VERSION=3.13.7-alpine3.22
FROM ${BASE_IMAGE}:${PYTHON_VERSION}

WORKDIR /app

RUN apk add --no-cache \
    build-base musl-dev openssl-dev libffi-dev pkgconfig curl
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --default-toolchain nightly && \
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> /etc/profile.d/rust.sh
ENV PATH="/root/.cargo/bin:${PATH}"
RUN python -m pip install -U pip setuptools wheel setuptools-rust

COPY src/agent-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/agent-server .

RUN mkdir -p /app/data
VOLUME /app/data

WORKDIR /
EXPOSE 8000

ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8000

ENV CHINOOK_DB_URL=https://github.com/laxmimerit/All-CSV-ML-Data-Files-Download/raw/refs/heads/master/db_samples/Chinook.db

ENV OLLAMA_MODEL=qwen2.5
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434

ENV OPENAI_MODEL=gpt-4.1
ENV OPENAI_KEY=CHANGE_ME

ENV SEARX_HOST=http://host.docker.internal:9080
ENV LANGFUSE_HOST=http://host.docker.internal:3000

CMD ["python", "-m", "app.main", "/app/main.py"]