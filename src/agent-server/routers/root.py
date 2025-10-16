import json
import logging
from typing import Any

from dependency_injector.wiring import Provide
from fastapi import APIRouter
from starlette.responses import Response

from ..container.container import Container

class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")

class Routes:
    router: APIRouter
    logger:logging.Logger
    config:Any

    def __call__(self, *args, **kwargs):
        return self.router

    def __init__(
            self,
            logger:logging.Logger = Provide[Container.logger],
            config:Any = Provide[Container.config]
    ):
        self.config = config
        self.router = APIRouter()
        self.router.add_api_route(
            "/",
            self.root,
            methods=["GET"],
            response_class=PrettyJSONResponse
        )
        self.logger = logger


    async def root(self):
        # Zugriff auf Konfigurationswerte (providers.Configuration -> Aufruf mit ())
        conf = self.config
        try:
            ollama_model = conf['ollama']['model']
            ollama_url = conf['ollama']['url']
        except Exception as t:
            self.logger.error(t)
            ollama_model = None
            ollama_url = None

        try:
            embed_model = conf['ollama']['embedding']['model']
            embed_vec = conf['ollama']['embedding']['vector_size']
        except Exception:
            embed_model = None
            embed_vec = None

        try:
            openai_model = conf['openai']['model']
            openai_key = conf['openai']['api_key']
        except Exception:
            openai_model = None
            openai_key = None

        try:
            pg_url = conf['pgvector']['url']
        except Exception:
            pg_url = None

        try:
            lf_host = conf['langfuse']['host']
        except Exception:
            lf_host = None

        try:
            api_host = conf['fastapi']['host']
            api_port = conf['fastapi']['port']
        except Exception:
            api_host = None
            api_port = None

        status = {
            "status": "ok",
            "services": {
                "ollama": {
                    "configured": bool(ollama_model and ollama_url),
                    "model": ollama_model,
                    "url": ollama_url,
                    "embedding": {
                        "model": embed_model,
                        "vector_size": embed_vec,
                    },
                },
                "openai": {
                    "configured": bool(openai_key),
                    "model": openai_model,
                    "api_key_present": bool(openai_key),
                },
                "pgvector": {
                    "configured": bool(pg_url),
                    "url": pg_url,
                },
                "langfuse": {
                    "host": lf_host,
                },
                "fastapi": {
                    "host": api_host,
                    "port": api_port,
                },
            },
        }

        return status
