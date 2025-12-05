import logging

from dependency_injector import containers, providers
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGEngine
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from sqlmodel import create_engine
from sqlalchemy import Engine
from ..ai.prompts.sql_agent import SqlAgent
from ..ai.agents.sql_agent import SQLAgent
from ..ai.agents.internet_archive import AgentFactory
from ..renderer.open_webui import OpenWebUiRenderer
from ..log.factory import LoggerFactory

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    ########################
    # 🚀 Logger
    ########################
    logger = providers.Singleton(
        LoggerFactory()
    )

    ########################
    # 🧠 Ollama LLM
    ########################
    config.ollama.model.from_env("OLLAMA_MODEL", default="llama3.2:3b")
    config.ollama.url.from_env("OLLAMA_URL", default="http://localhost:11434")
    config.openai.model.from_env("OPENAI_MODEL", default="gpt-4.1")
    config.openai.api_key.from_env("OPENAI_KEY", required=False)

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
    langchain_postgres: SQLDatabase = providers.Singleton(
        SQLDatabase.from_uri,
        database_uri=config.pgvector.url,
    )
    sqlmodel_engine_postgres: Engine = providers.Singleton(
        create_engine,
        config.pgvector.url
    )

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
            except Exception as e:
                logging.error(f"Langfuse authentication failed: {e}")
                return None

    langfuse_config = providers.Singleton(
        _MakeLangfuseConfig(),
        langfuseClass
     )

    ################################################
    #  📚 Internet Archive Agent
    ################################################
    internet_archive_agent = providers.Singleton(
        lambda factory: factory.create(),
        factory=providers.Singleton(
            AgentFactory,
            engine=sqlmodel_engine_postgres,
            llm=llm,
            logger=logger,
            langfuse_config=langfuse_config,
            k=40,
        )
    )

    internet_archive_graph = providers.Singleton(
        lambda factory: factory.create_graph(),
        factory=providers.Singleton(
            AgentFactory,
            llm=llm,
            logger=logger,
            engine=sqlmodel_engine_postgres,
            langfuse_config=langfuse_config,
            k=40,
            cache_dir="/data/ia/cache",
            data_dir = "/data/ia/data",
        )
    )

    ########################
    # 🧠 Ollama Embeddings
    ########################
    config.ollama.embedding.model.from_env("OLLAMA_EMBEDDING_MODEL", default="nomic-embed-text:latest")
    config.ollama.embedding.vector_size.from_env("OLLAMA_EMBEDDING_VECTOR_SIZE", as_=int, default=768)
    ollamaEmbeddings = providers.Singleton(
        OllamaEmbeddings,
        model=config.ollama_embedding_model,
        base_url=config.ollama_url,
    )
    vectorSize = providers.Object(config.ollama_embedding_vector_size)

    ########################
    # 🚀 FastAPI Server
    ########################
    config.fastapi.host.from_env("FASTAPI_HOST", default="0.0.0.0")
    config.fastapi.port.from_env("FASTAPI_PORT", as_=int, default=8000)
    fastapi_host = providers.Object(config.fastapi.host)
    fastapi_port = providers.Object(config.fastapi.port)

    ########################
    #  🤖 SQL Agent
    ########################
    sql_agent_prompt = providers.Singleton(
        SqlAgent.create,
        dialect=langchain_postgres.provided.dialect,
        top_k="5"
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
