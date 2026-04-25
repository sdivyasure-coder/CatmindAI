#!/usr/bin/env python3
"""
SQLite Setup Script
Prepares the project for SQLite-based development
"""

from pathlib import Path
import shutil

def setup_sqlite():
    """Setup project for SQLite"""
    
    print("Setting up SQLite configuration...")
    
    # Ensure app directory exists
    app_dir = Path("app")
    if not app_dir.exists():
        print("Creating app directory...")
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        (app_dir / "__init__.py").touch()
    
    # Create or update config.py for SQLite
    config_sqlite_content = '''from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # SQLite for local development
    DATABASE_URL: str = "sqlite:///./smart_learning.db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    
    # Application
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
'''
    
    config_file = app_dir / "config.py"
    config_file.write_text(config_sqlite_content)
    print(f"✓ Created {config_file} for SQLite")
    
    # Create database.py for SQLite
    database_sqlite_content = '''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import get_settings

settings = get_settings()

# SQLite specific settings with StaticPool for compatibility
engine = create_engine(
    settings.DATABASE_URL,
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
'''
    
    db_file = app_dir / "database.py"
    db_file.write_text(database_sqlite_content)
    print(f"✓ Created {db_file} for SQLite")
    
    print("\n" + "="*60)
    print("✅ SQLite Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. python setup.py")
    print("2. alembic upgrade head")
    print("3. uvicorn app.main:app --reload")
    print("\nAPI will be at: http://localhost:8000/docs")

if __name__ == "__main__":
    setup_sqlite()
