@echo off
cd d:\codemindai
mkdir app
mkdir alembic\versions
mkdir tests

REM Create app files
(
echo.
) > app\__init__.py

REM Create database.py
(
echo from sqlalchemy import create_engine
echo from sqlalchemy.orm import sessionmaker, declarative_base
echo from app.config import get_settings
echo.
echo settings = get_settings^(^)
echo.
echo engine = create_engine^(settings.DATABASE_URL, echo=settings.DEBUG^)
echo SessionLocal = sessionmaker^(autocommit=False, autoflush=False, bind=engine^)
echo Base = declarative_base^(^)
echo.
echo.
echo def get_db^(^):
echo     db = SessionLocal^(^)
echo     try:
echo         yield db
echo     finally:
echo         db.close^(^)
) > app\database.py

echo Directories and files created successfully!
