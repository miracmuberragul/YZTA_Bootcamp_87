from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database import database_is_ready
from app.routers.auth_router import router as auth_router

app = FastAPI(title="OfficeIQ — Auth Service", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/health")
def health():
    try:
        database_is_ready()
        return {"status": "ok", "database": "ready"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc