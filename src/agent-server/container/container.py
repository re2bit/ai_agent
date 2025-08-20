from dependency_injector import containers, providers
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGEngine
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from ..ai.prompts import sql_agent as sql_agent_prompt
from ..ai.agents.sql_agent import SQLAgent


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
    vectorSize = providers.Object(config.ollama_embedding_vector_size)

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
        llm=ollamaLLM,
        prompt=sql_agent_prompt,
        langfuse_config=langfuse_config
    )

