from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from Presentation.FastApi.Controllers.ExampleAgentRuntime.ExampleAgentRuntimeController import ExampleAgentRuntimeController
from Presentation.FastApi.Middlewares.SecurityHeadersMiddleware import SecurityHeadersMiddleware
from Runtime.CoreRuntimeSetting import CoreRuntimeSetting
from Infrastructure.Tools.HttpClientHelper.HttpClientConnector import HttpClientConnector
from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

# ********************************************************************************************************
# * Copyright © 2026 Arify Labs - All rights reserved.
# *
# * Info                  : ASGI application entrypoint for Arify Agent Runtime.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991*14
# *
# * Creation date         : 01/01/2026
# *
# **********************************************************************************************************


# ----- Start Coroutine -----
@asynccontextmanager
async def lifespan(app: FastAPI):
    await CoreRuntimeSetting.add_services()
    try:
        yield
    finally:
        await Services.get_instance(HttpClientConnector).close()
        # await my_consumers.stop_services()


app = FastAPI(docs_url="/docs/openapi", redoc_url="/docs/reopenapi", lifespan=lifespan)
app.title = "Arify Agent Runtime Server"
app.version = "3.0"
app.add_middleware(SecurityHeadersMiddleware)

@app.get("/")
def default() -> dict[str, str]:
    return {"Info": "Arify Labs All rights reserved"}


@app.get("/health")
def health() -> dict[str, str]:
    # TODO:
    # Debe llamarse a un caso de uso que verifique la salud de las dependencias
    return {"status": "ok"}


app.include_router(ExampleAgentRuntimeController().ApiRouter, prefix="/business-api-b/v1/example-agent-runtime")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
