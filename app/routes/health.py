from fastapi import APIRouter
from sqlalchemy import text

from app.database import engine

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():

    db_status = "connected"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status,
        "api": "running"
    }