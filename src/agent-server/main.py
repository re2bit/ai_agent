"""
title: Agent API Server
description: FastAPI server for the agent
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import logging
from .logging.logfilter import apply_log_filter

from .container.container import container

container.wire(modules=[__name__], packages=[".routers.chat", "app.routers.test", "app.routers.root"])

from .routers import test, healthcheck, chat, root

load_dotenv('.env')
apply_log_filter(["/healthcheck"])

debug_port_env = os.getenv("AGENT_SERVER_PYDEVD_DEBUG_PORT")
if debug_port_env.isnumeric():
    debug_port = int(debug_port_env)
    debug_host = os.getenv("AGENT_SERVER_PYDEVD_DEBUG_HOST", "host.docker.internal")
    print(f"Starting in debug mode on port {debug_port} and Host {debug_host}")
    try:
        import pydevd_pycharm
        pydevd_pycharm.settrace(
            debug_host,
            port=debug_port,
            stdoutToServer=True,
            stderrToServer=True,
        )
    except Exception:
        print(f"Failed to start debug on port {debug_port} and Host {debug_host}")


app = FastAPI(
    title="Agent API Server",
    description="FastAPI server for the SQL and search agent",
)

def main() -> None:
    # app.include_router(rag.Routes()())
    app.include_router(root.Routes()())
    app.include_router(chat.Routes()())
    app.include_router(healthcheck.Routes()())
    # TODO: add the internet Archive Search here.
    app.include_router(test.Routes()())
    fastapi_port = container.config.fastapi.port()
    fastapi_host = container.config.fastapi.host()
    uvicorn.run(app, host=fastapi_host, port=fastapi_port, log_level=logging.DEBUG)

if __name__ == "__main__":
    main()