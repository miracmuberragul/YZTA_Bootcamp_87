from fastapi import FastAPI, HTTPException
from app.database import database_is_ready

app = FastAPI(title='Auth Service')

@app.get('/health')
def health():
    try:
        database_is_ready()
        return {'status': 'ok', 'database': 'ready'}
    except Exception as exc:
        raise HTTPException(status_code=503, detail='database unavailable') from exc
