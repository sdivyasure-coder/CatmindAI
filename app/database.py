from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import get_settings

settings = get_settings()

database_url = settings.DATABASE_URL
engine_kwargs = {"echo": settings.DEBUG}

if database_url.startswith("sqlite"):
    # SQLite needs thread-check disable and StaticPool for local/dev compatibility.
    engine_kwargs.update(
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

try:
    engine = create_engine(database_url, **engine_kwargs)
except ModuleNotFoundError:
    # Fallback for environments missing optional PostgreSQL driver.
    fallback_url = "sqlite:///./smart_learning.db"
    engine = create_engine(
        fallback_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
