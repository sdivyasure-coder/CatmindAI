# Smart AI-Based Programming Learning System

A FastAPI-based web application that teaches programming languages using AI guidance with topic-based learning cycles, testing, performance analytics, and a leaderboard system.

## Project Structure

```
codemindai/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── database.py            # Database setup & connection
│   ├── models.py              # SQLAlchemy ORM models
│   ├── main.py                # FastAPI app initialization
│   ├── routes/                # API endpoints
│   ├── schemas/               # Pydantic request/response models
│   ├── services/              # Business logic
│   └── utils/                 # Helper functions
├── alembic/                   # Database migrations
├── tests/                     # Test files
├── .env.example               # Environment variables template
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── plan.md                    # Implementation plan
```

## Database Schema

### Core Tables
- **users**: User authentication and metadata
- **languages**: Programming languages
- **topics**: Learning topics per language
- **tests**: Test configurations per topic
- **user_progress**: User progress tracking
- **test_results**: Test scores and analysis
- **leaderboard**: User rankings by completion time

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database and API credentials
   ```

3. **Set up database**:
   ```bash
   alembic upgrade head
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Features (Planned)

- User authentication with JWT
- Topic-based learning with AI teaching
- Theory and practical tests
- AI hint generation during tests
- Performance analytics and reporting
- Leaderboard system based on completion time
- Admin panel for content management
- Comprehensive error handling and logging

## Implementation Phases

See `plan.md` for detailed implementation phases and tasks.

## Technologies

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **AI Integration**: OpenAI GPT-4
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Testing**: pytest
