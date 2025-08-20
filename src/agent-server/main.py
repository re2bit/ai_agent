
"""
title: Agent API Server
description: FastAPI server for the agent
"""
import os, sys
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from dependency_injector.wiring import Provide, inject
from requests import packages

from .container.container import Container

container = Container()
container.wire(modules=[__name__], packages=["app.routers.test"])

#from .routers import rag, chat, test
from .routers import test

load_dotenv('.env')

if os.getenv("DEBUG").isnumeric():
    debug_port = os.getenv("DEBUG")
    import pydevd_pycharm
    pydevd_pycharm.settrace(
        os.getenv("DEBUG_HOST", "host.docker.internal"),
        port=int(debug_port),
        stdoutToServer=True,
        stderrToServer=True
    )

app = FastAPI(
    title="Agent API Server",
    description="FastAPI server for the SQL and search agent",
)



@app.get("/")
async def root():
    """Root endpoint that returns a welcome message"""
    return {"message": "Welcome to the Agent API Server"}



def main() -> None:
    # app.include_router(rag.Routes()())
    # app.include_router(chat.Routes()())
    app.include_router(test.Routes()())
    fastapi_port = container.config.fastapi.port()
    fastapi_host = container.config.fastapi.host()
    uvicorn.run(app, host=fastapi_host, port=fastapi_port, log_level=5)

if __name__ == "__main__":
    main()