import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://officeiq:officeiq_password@localhost:5432/officeiq")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def database_is_ready() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
