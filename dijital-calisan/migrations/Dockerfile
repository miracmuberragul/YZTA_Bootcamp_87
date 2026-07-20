FROM python:3.11-slim
WORKDIR /app
COPY migrations/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini .
COPY migrations ./migrations
CMD ["alembic", "upgrade", "head"]
