import os

STORAGE_PATH = os.getenv("STORAGE_PATH", "/storage")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(15 * 1024 * 1024)))
INGESTION_SERVICE_URL = os.getenv("INGESTION_SERVICE_URL", "http://ingestion-service:8002")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "development-internal-key")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
