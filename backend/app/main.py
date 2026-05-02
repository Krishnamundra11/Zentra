"""
Zetra — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, recognition, agent, recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await init_db()
    yield


app = FastAPI(
    title="Zetra API",
    description="AI-powered tourist place recognition and travel planning",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,            prefix="/auth",         tags=["auth"])
app.include_router(recognition.router,     prefix="/recognition",  tags=["recognition"])
app.include_router(agent.router,           prefix="/agent",        tags=["agent"])
app.include_router(recommendations.router, prefix="/recommend",    tags=["recommendations"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Zetra-api"}
