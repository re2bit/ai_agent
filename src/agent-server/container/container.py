from typing import Any

from dependency_injector import containers, providers
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGEngine
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
import logging
import sys
from pprint import pformat

from ..ai.prompts import sql_agent as sql_agent_prompt
from ..ai.agents.sql_agent import SQLAgent
from ..renderer.open_webui import OpenWebUiRenderer


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    ########################
    # 🔑 Langfuse
    ########################
    config.langfuse.public_key.from_env("LANGFUSE_PUBLIC_KEY", required=False)
    config.langfuse.secret_key.from_env("LANGFUSE_SECRET_KEY", required=False)
    config.langfuse.host.from_env("LANGFUSE_HOST", default="http://localhost:3000")

    langfuseClass = providers.Singleton(
        Langfuse,
        public_key=config.langfuse_public_key,
        secret_key=config.langfuse_secret_key,
        host=config.langfuse_host,
    )

    class _MakeLangfuseConfig:
        def __call__(self, lf: Langfuse):
            try:
                lf.auth_check()
                return RunnableConfig(
                    callbacks=[CallbackHandler()]
                )
            except Exception:
                return None

    langfuse_config = providers.Singleton(
        _MakeLangfuseConfig(),
        langfuseClass
     )

    ########################
    # 🐘 Postgres / PGVector
    ########################
    config.pgvector.url.from_env(
        "PGVECTOR_PGENGINE_URL",
        default="postgresql+psycopg://agent-server:agent-server@pgvector:5432/agent-server",
    )
    pgengine = providers.Singleton(
        PGEngine.from_connection_string,
        url=config.pgvector.url
    )
    langchain_postgres = providers.Singleton(
        SQLDatabase.from_uri,
        database_uri=config.pgvector.url,
    )


    ########################
    # 🧠 Ollama Embeddings
    ########################
    config.ollama.model.from_env("OLLAMA_MODEL", default="llama3.2:3b")
    config.ollama.embedding.model.from_env("OLLAMA_EMBEDDING_MODEL", default="nomic-embed-text:latest")
    config.ollama.url.from_env("OLLAMA_URL", default="http://localhost:11434")
    config.ollama.embedding.vector_size.from_env("OLLAMA_EMBEDDING_VECTOR_SIZE", as_=int, default=768)
    config.openai.model.from_env("OPENAI_MODEL", default="gpt-4.1")
    config.openai.api_key.from_env("OPENAI_KEY", required=False)
    ollamaEmbeddings = providers.Singleton(
        OllamaEmbeddings,
        model=config.ollama_embedding_model,
        base_url=config.ollama_url,
    )

    ollamaLLM = providers.Singleton(
        ChatOllama,
        model=config.ollama.model,
        base_url=config.ollama.url
    )

    if config.openai.api_key:
        openAiLLM = providers.Singleton(
            ChatOpenAI,
            model=config.openai.model,
            api_key=config.openai.api_key,
        )

    llm = ollamaLLM
    #llm = openAiLLM

    vectorSize = providers.Object(config.ollama_embedding_vector_size)

    ########################
    # 🚀 Logger
    ########################
    class _MakeLogger:
        def __call__(self):
            try:
                logger = logging.getLogger(__name__)
                logger.setLevel(logging.DEBUG)
                formatter = logging.Formatter(
                    "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")

                stream_handler = logging.StreamHandler(sys.stdout)
                stream_handler.setFormatter(formatter)
                logger.addHandler(stream_handler)

                #file_handler = logging.FileHandler("info.log")
                #file_handler.setFormatter(formatter)
                #logger.addHandler(file_handler)

                def _debug_var(obj: Any,
                               name: str = "var",
                               level: int = logging.DEBUG,
                               *,
                               width: int = 100,
                               compact: bool = True,
                               sort_dicts: bool = True,
                               ) -> None:
                    if not logger.isEnabledFor(level):
                        return
                    logger.log(level, "%s:\n%s", name, pformat(obj, width=width, compact=compact, sort_dicts=sort_dicts))

                logger.debug_var = _debug_var

                return logger
            except Exception:
                return None

    logger = providers.Singleton(
        _MakeLogger()
    )

    ########################
    # 🚀 FastAPI Server
    ########################
    config.fastapi.host.from_env("FASTAPI_HOST", default="0.0.0.0")
    config.fastapi.port.from_env("FASTAPI_PORT", as_=int, default=8000)
    fastapi_host = providers.Object(config.fastapi.host)
    fastapi_port = providers.Object(config.fastapi.port)

    ########################
    #  🤖 Prompts
    ########################
    sql_agent_prompt = providers.Singleton(
        sql_agent_prompt.create,
       dialect=langchain_postgres.provided.dialect,
       top_k=5
    )
    sql_agent = providers.Singleton(
        SQLAgent,
        db=langchain_postgres,
        llm=llm,
        prompt=sql_agent_prompt,
        langfuse_config=langfuse_config,
        logger=logger,
    )

    ########################
    #  ⚡️ Open Web UI
    ########################
    renderer = providers.Singleton(
        OpenWebUiRenderer,
        logger=logger
    )

container = Container()
