import os

JWT_SECRET = os.getenv("SECRET_KEY", "development-only-change-me")
JWT_ALGORITHM = "HS256"
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_EMBEDDING_PROVIDER = os.getenv("HF_EMBEDDING_PROVIDER", "hf-inference")
HF_LLM_PROVIDER = os.getenv("HF_LLM_PROVIDER", "auto")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-3-12b-it")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "400"))
HF_TIMEOUT_SECONDS = float(os.getenv("HF_TIMEOUT_SECONDS", "60"))
RETRIEVAL_DEFAULT_LIMIT = int(os.getenv("RETRIEVAL_DEFAULT_LIMIT", "3"))
