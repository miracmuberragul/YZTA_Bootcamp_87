from fastapi import FastAPI, HTTPException
from app.database import database_is_ready
from app.routers.ingestion_router import router as ingestion_router

app = FastAPI(title='Ingestion Service')
app.include_router(ingestion_router)

@app.get('/health')
def health():
    try:
        database_is_ready()
        return {'status': 'ok', 'database': 'ready'}
    except Exception as exc:
        raise HTTPException(status_code=503, detail='database unavailable') from exc
