import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from app.database import database_is_ready
from app.routers.ingestion_router import router as ingestion_router
from app.services.ingestion_service import process_pending_jobs

logger = logging.getLogger(__name__)


async def queued_job_worker() -> None:
    while True:
        try:
            processed = await asyncio.to_thread(process_pending_jobs)
            await asyncio.sleep(0.25 if processed else 2.0)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Queued ingestion worker iteration failed")
            await asyncio.sleep(2.0)


@asynccontextmanager
async def lifespan(_: FastAPI):
    worker = asyncio.create_task(queued_job_worker())
    try:
        yield
    finally:
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)


app = FastAPI(title='Ingestion Service', lifespan=lifespan)
app.include_router(ingestion_router)

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
        return {'status': 'ok', 'database': 'ready'}
    except Exception as exc:
        raise HTTPException(status_code=503, detail='database unavailable') from exc
