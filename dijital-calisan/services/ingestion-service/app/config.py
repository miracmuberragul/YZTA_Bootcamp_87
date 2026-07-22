import os

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "development-internal-key")
