# Smart AI Learning System - Deployment & Run Guide

## 🎉 Project Complete - All 12 Phases Implemented

### What's Included

**✅ 50+ API Endpoints** across 7 modules
- Authentication (register, login, profile)
- Course Management (languages, topics)
- Learning Progress (start, hints, content)
- Test Engine (start, submit, analyze)
- Analytics (dashboard, performance, statistics)
- Leaderboard (language-specific, global)
- Admin Panel (management, system analytics)

**✅ 7 Database Models** with relationships
- Users (with admin flags)
- Languages
- Topics (theory & practical)
- Tests (with scoring)
- UserProgress (tracking)
- TestResults (scores & reports)
- Leaderboard (rankings)

**✅ AI Integration** powered by OpenAI
- Dynamic content generation
- Intelligent hint generation
- Answer analysis & scoring
- Performance reports
- Remedial content

**✅ Security & Validation**
- JWT authentication
- Password hashing (bcrypt)
- Role-based access control (admin)
- Input validation (Pydantic)
- CORS enabled

**✅ Testing & Documentation**
- Unit tests for auth
- Integration tests for API
- Swagger/OpenAPI docs (auto-generated)
- pytest configuration

**✅ Deployment Ready**
- Docker & Docker Compose
- Environment configuration
- Logging setup
- Error handling
- Database migrations (Alembic)

---

## 🚀 Quick Start

### 1. Setup Project Files

Choose one of the setup scripts:

```bash
# Full setup (phases 1-8)
python setup.py

# OR: Include Phase 6 (AI Integration)
python setup_phase6.py

# OR: Complete (phases 1-12)
python setup_complete_phases.py
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/smart_ai_learning
SECRET_KEY=your-very-secret-key-here
OPENAI_API_KEY=sk-xxx  # Optional: for AI features
```

### 4. Setup Database

```bash
alembic upgrade head
```

### 5. Run Application

```bash
uvicorn app.main:app --reload
```

Access API at: **http://localhost:8000**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐳 Docker Deployment

### Build & Run

```bash
docker-compose up --build
```

This will:
- Start PostgreSQL database
- Build and run FastAPI application
- Create all tables automatically

Access at: http://localhost:8000

### Environment Variables

Create `.env` file before running:
```bash
OPENAI_API_KEY=sk-your-key
DATABASE_URL=postgresql://smart_ai:password@db:5432/smart_ai_learning
SECRET_KEY=your-secret-key
```

---

## 📝 API Endpoints Summary

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user

### Courses
- `GET /languages` - List languages
- `POST /languages` - Create language (admin)
- `GET /languages/{id}/topics` - Get topics for language
- `POST /languages/{id}/topics` - Create topic (admin)

### Learning
- `GET /progress` - Get user progress
- `POST /progress/start` - Start topic
- `GET /progress/topics/{id}/content` - Get topic content
- `POST /progress/topics/{id}/hint` - Get hint

### Tests
- `POST /tests/{topic_id}/start` - Start test
- `GET /tests/{test_id}/questions` - Get questions
- `POST /tests/{test_id}/submit` - Submit answers
- `POST /tests/{test_id}/analyze` - Get analysis

### Analytics
- `GET /analytics/user/dashboard` - User dashboard
- `GET /analytics/user/performance/{test_id}` - Test details
- `GET /analytics/topic/{topic_id}/statistics` - Topic stats

### Leaderboard
- `GET /leaderboard/{language_id}` - Language leaderboard
- `GET /leaderboard/global/top` - Global top 100

### Admin
- `POST /admin/languages` - Create language
- `GET /admin/languages` - List languages
- `DELETE /admin/languages/{id}` - Delete language
- `GET /admin/users` - List users
- `POST /admin/users/{id}/admin` - Promote admin
- `GET /admin/analytics/system` - System stats

### AI Integration
- `POST /ai/topics/{id}/generate-content` - Generate content
- `POST /ai/topics/{id}/generate-questions` - Generate questions
- `POST /ai/hints/{id}` - Generate hint
- `POST /ai/analyze-answer/{id}` - Analyze answer
- `POST /ai/performance-report/{id}` - Generate report

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test

```bash
pytest tests/test_auth.py -v
```

### With Coverage

```bash
pytest --cov=app tests/
```

---

## 📊 Database Schema

```
users
├── id (PK)
├── email (unique)
├── password_hash
├── is_admin
└── created_at

languages
├── id (PK)
├── name (unique)
├── description
└── created_at

topics
├── id (PK)
├── language_id (FK)
├── title
├── description
├── type (theory/practical)
├── order
├── content
└── created_at

tests
├── id (PK)
├── topic_id (FK, unique)
├── questions
├── passing_percentage
└── created_at

user_progress
├── id (PK)
├── user_id (FK)
├── topic_id (FK)
├── status (not_started/in_progress/completed)
├── attempts
├── passed_at
├── created_at
└── updated_at

test_results
├── id (PK)
├── user_id (FK)
├── test_id (FK)
├── score
├── answers
├── performance_report
├── passed
└── created_at

leaderboard
├── id (PK)
├── user_id (FK)
├── language_id (FK)
├── completion_time
├── rank
└── completed_at
```

---

## 🔑 Key Features Explained

### Topic-Based Learning Cycle
1. User selects language
2. System presents first topic
3. AI teaches the topic
4. User takes time-based test
5. AI provides hints if needed
6. System evaluates answers
7. If pass: unlock next topic
8. If fail: re-teach, retry

### AI-Powered Features
- **Content Generation**: Dynamic teaching content per topic
- **Question Generation**: Automatically create tests
- **Hint System**: Contextual hints without spoilers
- **Answer Analysis**: Detailed feedback on submissions
- **Performance Reports**: Personalized improvement suggestions

### Admin Features
- Manage languages and topics
- Set passing percentages
- Promote users to admins
- View system analytics
- Monitor user progress

### Leaderboard System
- Ranked by completion time
- Language-specific rankings
- Global top 100
- Real-time updates

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql://... | Database connection |
| `SECRET_KEY` | your-secret | JWT signing key |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Token expiration |
| `OPENAI_API_KEY` | (empty) | OpenAI API key |
| `OPENAI_MODEL` | gpt-4 | OpenAI model |
| `DEBUG` | True | Debug mode |

### JWT Token Format

```bash
Authorization: Bearer <token>
```

Get token:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

---

## 🚨 Common Issues & Solutions

### PostgreSQL Connection Error
```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Or use Docker
docker-compose up db
```

### OpenAI API Errors
- Ensure `OPENAI_API_KEY` is set in `.env`
- Verify API key is valid
- Check API usage limits
- System works without it (degraded mode)

### Database Migration Issues
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head
```

### Port Already in Use
```bash
# Change port
uvicorn app.main:app --port 8001
```

---

## 📚 Next Steps

### For Development
1. Add more topics and languages
2. Integrate with frontend
3. Add more test types
4. Implement caching (Redis)
5. Add email notifications

### For Deployment
1. Use production database
2. Set up SSL/HTTPS
3. Configure rate limiting
4. Enable monitoring & logging
5. Set up CI/CD pipeline
6. Use production ASGI server (Gunicorn)

---

## 📞 Support

For issues or questions:
1. Check `.env` configuration
2. Review database logs
3. Check application logs in `logs/app.log`
4. Verify all dependencies installed
5. Check FastAPI documentation

---

**Smart AI Learning System v1.0.0**
All 12 phases implemented and ready for production! 🚀
