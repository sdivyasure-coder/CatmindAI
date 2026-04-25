#!/usr/bin/env python3
"""
Complete project setup including Phase 9-12
"""

from pathlib import Path

def create_complete_project():
    """Create complete project structure with all phases"""
    
    print("Setting up complete project structure...")
    
    directories = [
        "app", "app/routes", "app/schemas", "app/services", "app/utils",
        "alembic/versions", "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    init_files = [
        "app/__init__.py", "app/routes/__init__.py", "app/schemas/__init__.py",
        "app/services/__init__.py", "app/utils/__init__.py",
        "alembic/__init__.py", "tests/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
    
    files = {
        # Admin routes
        "app/routes/admin.py": '''from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Language, Topic, Test
from app.utils.security import decode_token

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Verify user has admin privileges"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return user


@router.post("/languages")
def create_language(name: str, description: str, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Create a new language"""
    language = Language(name=name, description=description)
    db.add(language)
    db.commit()
    db.refresh(language)
    return {"id": language.id, "name": language.name}


@router.get("/languages")
def get_all_languages(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get all languages"""
    languages = db.query(Language).all()
    return [{"id": l.id, "name": l.name, "description": l.description} for l in languages]


@router.delete("/languages/{language_id}")
def delete_language(language_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Delete a language"""
    language = db.query(Language).filter(Language.id == language_id).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    db.delete(language)
    db.commit()
    return {"message": "Deleted"}


@router.get("/topics")
def get_all_topics(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get all topics"""
    topics = db.query(Topic).all()
    return [{"id": t.id, "title": t.title, "language_id": t.language_id} for t in topics]


@router.put("/tests/{test_id}/passing-percentage")
def update_test_threshold(test_id: int, passing_percentage: float, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Update test passing percentage"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    test.passing_percentage = passing_percentage
    db.commit()
    return {"message": "Updated"}


@router.get("/users")
def list_users(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "is_admin": u.is_admin} for u in users]


@router.post("/users/{user_id}/admin")
def make_admin(user_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Make user an admin"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    db.commit()
    return {"message": "User promoted to admin"}


@router.get("/analytics/system")
def system_analytics(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get system statistics"""
    return {
        "total_users": db.query(User).count(),
        "total_languages": db.query(Language).count(),
        "total_topics": db.query(Topic).count(),
        "admins": db.query(User).filter(User.is_admin == True).count()
    }
''',

        # Error handling middleware
        "app/middleware/error_handler.py": '''from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
''',

        # Logging configuration
        "app/utils/logger.py": '''import logging
import logging.handlers
from app.config import get_settings

settings = get_settings()


def setup_logger():
    """Setup application logging"""
    logger = logging.getLogger("smart_ai_learning")
    logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    
    # File handler
    fh = logging.handlers.RotatingFileHandler(
        "logs/app.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger
''',

        # Test examples
        "tests/test_auth.py": '''import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register():
    """Test user registration"""
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login():
    """Test user login"""
    # First register
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    
    # Then login
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200


def test_invalid_login():
    """Test invalid login"""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrong"}
    )
    assert response.status_code == 401
''',

        "tests/test_courses.py": '''import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_languages():
    """Test getting languages"""
    response = client.get("/languages")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
''',

        # Docker setup
        "Dockerfile": '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',

        "docker-compose.yml": '''version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: smart_ai
      POSTGRES_PASSWORD: password
      POSTGRES_DB: smart_ai_learning
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://smart_ai:password@db:5432/smart_ai_learning
      SECRET_KEY: your-secret-key
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - db
    volumes:
      - .:/app

volumes:
  postgres_data:
''',

        ".dockerignore": '''__pycache__
*.pyc
.git
.gitignore
.env
.env.local
logs/
*.db
''',

        ".gitignore": '''__pycache__/
*.py[cod]
*$py.class
.env
.env.local
*.db
logs/
*.log
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.vscode/
.idea/
*.swp
*.swo
*~
''',

        "pyproject.toml": '''[project]
name = "smart-ai-learning"
version = "1.0.0"
description = "AI-powered programming learning system"
requires-python = ">=3.9"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.black]
line-length = 100

[tool.isort]
profile = "black"
''',
    }
    
    print("\n" + "="*60)
    print("Creating Phase 9-12 files...")
    print("="*60)
    
    for filepath, content in files.items():
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            Path(filepath).write_text(content)
            print(f"✓ {filepath}")
        except Exception as e:
            print(f"✗ {filepath}: {e}")
    
    print("\n" + "="*60)
    print("✅ Phases 9-12 setup complete!")
    print("="*60)
    print("\nPhase 9: Admin Panel - NEW ENDPOINTS:")
    print("  GET /admin/languages")
    print("  POST /admin/languages")
    print("  DELETE /admin/languages/{id}")
    print("  GET /admin/topics")
    print("  PUT /admin/tests/{id}/passing-percentage")
    print("  GET /admin/users")
    print("  POST /admin/users/{id}/admin")
    print("  GET /admin/analytics/system")
    print("\nPhase 10: Error Handling & Logging - SETUP:")
    print("  ✓ Global exception handlers")
    print("  ✓ Logging configuration")
    print("  ✓ Request validation")
    print("\nPhase 11: Testing - EXAMPLES:")
    print("  ✓ tests/test_auth.py")
    print("  ✓ tests/test_courses.py")
    print("\nPhase 12: Deployment - DOCKER:")
    print("  ✓ Dockerfile")
    print("  ✓ docker-compose.yml")
    print("  ✓ .gitignore")
    print("  ✓ pyproject.toml")

if __name__ == "__main__":
    create_complete_project()
