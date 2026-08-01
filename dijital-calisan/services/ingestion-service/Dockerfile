FROM python:3.11-slim
WORKDIR /app
ENV TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p "$TIKTOKEN_CACHE_DIR" && python -c "import tiktoken; tiktoken.encoding_for_model('text-embedding-3-small')"
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
