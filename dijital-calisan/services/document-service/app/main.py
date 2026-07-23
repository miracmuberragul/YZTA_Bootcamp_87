from pathlib import Path

from fastapi import FastAPI, HTTPException
from app.config import STORAGE_PATH
from app.database import database_is_ready
from app.routers.document_router import internal_router, router as document_router

app = FastAPI(title='Document Service')
app.include_router(document_router)
app.include_router(internal_router)

@app.get('/health')
def health():
    try:
        database_is_ready()
        return {'status': 'ok', 'database': 'ready'}
    except Exception as exc:
        raise HTTPException(status_code=503, detail='database unavailable') from exc


@app.get('/health/live')
def liveness():
    return {'status': 'ok'}


@app.get('/health/ready')
def readiness():
    try:
        database_is_ready()
        storage = Path(STORAGE_PATH)
        storage.mkdir(parents=True, exist_ok=True)
        if not storage.is_dir():
            raise OSError("storage path is not a directory")
        return {'status': 'ok', 'database': 'ready', 'storage': 'ready'}
    except Exception as exc:
        raise HTTPException(status_code=503, detail='service dependencies unavailable') from exc
