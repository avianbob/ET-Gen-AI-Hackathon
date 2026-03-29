import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import agent_routes
from app.repurpose_settings import settings as repurpose_settings
from app.platform_bootstrap import register_platform_routes
from app.services.repurpose.llm.llm_factory import LLMFactory
from app.graph.workflow import reset_workflow

load_dotenv()


@asynccontextmanager
async def _app_lifespan(_app: FastAPI):
    # Avoid stale LLM singletons and LangGraph definition surviving reloads
    LLMFactory.reset()
    reset_workflow()
    yield
    LLMFactory.reset()
    reset_workflow()


app = FastAPI(
    title="ET PharmAI Backend",
    description="Unified FastAPI service: classic analysis agents (/api/run-agent) plus search, chat, exports, knowledge, and real-time updates.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=_app_lifespan,
)

_default_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:4173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:4173",
    "http://127.0.0.1:3000",
]
_raw = os.getenv("FRONTEND_URLS") or os.getenv("FRONTEND_URL", "http://localhost:5173")
CORS_ORIGINS = [o.strip() for o in _raw.split(",") if o.strip()] or _default_origins
for o in _default_origins:
    if o not in CORS_ORIGINS:
        CORS_ORIGINS.append(o)
for o in repurpose_settings.CORS_ORIGINS:
    if o not in CORS_ORIGINS:
        CORS_ORIGINS.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(agent_routes.router, prefix="/api")
register_platform_routes(app)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "ET PharmAI Backend",
        "run_agent": "/api/run-agent",
        "docs": "/docs",
        "health": "/health",
        "platform": "/platform",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
