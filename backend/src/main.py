from fastapi import FastAPI

from backend.src.api.health import router as health_router

app = FastAPI(title="TcyberChat")

app.include_router(health_router)
