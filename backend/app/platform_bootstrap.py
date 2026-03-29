"""
Registers extended ET PharmAI backend capabilities on the single FastAPI app:
REST routes under /api, knowledge WebSocket, health checks, and startup/shutdown hooks.
"""

from datetime import datetime
import os
import traceback

from fastapi import FastAPI, Request, WebSocket, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.repurpose_settings import settings
from app.schemas.repurpose_api import HealthResponse
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("platform.bootstrap")


async def platform_startup() -> None:
    logger.info("=" * 50)
    logger.info("ET PharmAI backend: extended features starting")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info("=" * 50)

    if settings.USE_MONGODB:
        try:
            from app.services.repurpose.database import get_database

            db = await get_database()
            if db and db.is_connected:
                logger.info("Connected to MongoDB")
            else:
                logger.warning("MongoDB connection failed - some features will be unavailable")
        except Exception as e:
            logger.warning(f"MongoDB connection skipped: {e}")

    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            from app.services.repurpose.database.supabase_client import get_supabase_client

            if get_supabase_client():
                logger.info("Supabase client initialized (see database/supabase/*.sql for schema)")
            else:
                logger.warning("Supabase URL/key set but client failed; check pip install supabase")
        except Exception as e:
            logger.warning(f"Supabase startup skipped: {e}")

    try:
        from app.services.repurpose.vector_store import get_knowledge_base
        from app.services.repurpose.vector_store.init_knowledge_base import populate_knowledge_base

        kb = get_knowledge_base()
        if not kb.is_populated():
            logger.info("Initializing knowledge base with pharmaceutical documents...")
            results = populate_knowledge_base(kb)
            total = sum(results.values())
            logger.info(f"Knowledge base initialized with {total} documents")
        else:
            stats = kb.get_stats()
            total = sum(s.get("document_count", 0) for s in stats.values() if isinstance(s, dict))
            logger.info(f"Knowledge base already populated with {total} documents")
    except Exception as e:
        logger.warning(f"Knowledge base initialization skipped: {e}")

    try:
        from app.services.repurpose.vector_store import get_knowledge_base

        kb = get_knowledge_base()
        root = os.path.dirname(os.path.dirname(__file__))
        docs_dir = os.path.join(root, "data", "internal_docs")
        if os.path.exists(docs_dir):
            doc_files = [f for f in os.listdir(docs_dir) if f.endswith(".txt")]
            if doc_files:
                docs = []
                metas = []
                ids = []
                for fname in doc_files:
                    fpath = os.path.join(docs_dir, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    words = content.split()
                    for i in range(0, len(words), 450):
                        chunk = " ".join(words[i : i + 500])
                        docs.append(chunk)
                        metas.append({"source": fname, "type": "internal_document"})
                        ids.append(f"internal_{fname}_{i}")

                if docs:
                    kb.add_documents("repurposing_cases", docs, metas, ids)
                    logger.info(f"Loaded {len(docs)} chunks from {len(doc_files)} internal documents")
    except Exception as e:
        logger.warning(f"Internal document loading skipped: {e}")


async def platform_shutdown() -> None:
    if settings.USE_MONGODB:
        try:
            from app.services.repurpose.database.mongodb import close_database

            await close_database()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.warning(f"Error closing MongoDB: {e}")

    logger.info("ET PharmAI backend: extended features shutdown complete")


def register_platform_routes(host_app: FastAPI) -> None:
    """Register shared exception handlers, lifecycle hooks, REST routers, and WebSocket on host_app."""

    @host_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "message": "Invalid request data"},
        )

    @host_app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {str(exc)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            },
        )

    @host_app.on_event("startup")
    async def _platform_on_startup():
        await platform_startup()

    @host_app.on_event("shutdown")
    async def _platform_on_shutdown():
        await platform_shutdown()

    @host_app.get("/platform", tags=["Root"])
    async def platform_info():
        return {
            "message": "ET PharmAI analysis platform API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    @host_app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        return HealthResponse(
            status="ok",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
        )

    from app.routes.repurpose import (
        auth,
        chat,
        compare,
        data,
        drug_info,
        export,
        files,
        integrations,
        knowledge,
        market,
        reports,
        search,
    )
    from app.routes.repurpose.websocket import websocket_endpoint

    host_app.include_router(search.router, prefix="/api", tags=["Search"])
    host_app.include_router(chat.router, prefix="/api", tags=["Chat"])
    host_app.include_router(export.router, prefix="/api", tags=["Export"])
    host_app.include_router(files.router, prefix="/api", tags=["Files"])
    host_app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])
    host_app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    host_app.include_router(market.router, prefix="/api", tags=["Market Analysis"])
    host_app.include_router(integrations.router, prefix="/api", tags=["Integrations"])
    host_app.include_router(reports.router, prefix="/api", tags=["Reports"])
    host_app.include_router(drug_info.router, prefix="/api", tags=["Drug Info"])
    host_app.include_router(compare.router, prefix="/api", tags=["Compare"])
    host_app.include_router(data.router, prefix="/api", tags=["Data Management"])

    @host_app.websocket("/ws/{session_id}")
    async def websocket_route(websocket: WebSocket, session_id: str):
        await websocket_endpoint(websocket, session_id)
