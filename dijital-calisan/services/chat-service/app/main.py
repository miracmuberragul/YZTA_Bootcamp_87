from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database import database_is_ready
from app.routers.chat_router import router

app = FastAPI(title='Chat Service')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.get('/health')
def health():
    try:
        database_is_ready()
        return {'status': 'ok', 'database': 'ready'}
    except Exception as exc:
        raise HTTPException(status_code=503, detail='database unavailable') from exc
