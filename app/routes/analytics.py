from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, UserProgress, TestResult, Test, Topic
from app.utils.security import decode_token

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Get current user from Authorization header"""
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
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/user/dashboard")
def get_user_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user performance dashboard"""
    progress_entries = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()
    
    test_results = db.query(TestResult).filter(TestResult.user_id == current_user.id).all()
    
    topics_completed = len([p for p in progress_entries if p.status == "completed"])
    total_topics = len(progress_entries)
    
    if test_results:
        average_score = sum([t.score for t in test_results]) / len(test_results)
    else:
        average_score = 0.0
    
    weak_topics = [t.topic.title for t in test_results if not t.passed][:5]
    
    return {
        "topics_completed": topics_completed,
        "total_topics": total_topics,
        "average_score": average_score,
        "weak_topics": weak_topics,
        "total_test_attempts": len(test_results),
        "passed_tests": len([t for t in test_results if t.passed])
    }


@router.get("/user/performance/{test_id}")
def get_test_performance(test_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get detailed test performance"""
    result = db.query(TestResult).filter(
        TestResult.test_id == test_id,
        TestResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    test = db.query(Test).filter(Test.id == test_id).first()
    topic = db.query(Topic).filter(Topic.id == test.topic_id).first()
    
    return {
        "test_id": test_id,
        "topic": topic.title,
        "score": result.score,
        "passed": result.passed,
        "passing_percentage": test.passing_percentage,
        "performance_report": result.performance_report,
        "created_at": result.created_at
    }


@router.get("/topic/{topic_id}/statistics")
def get_topic_statistics(topic_id: int, db: Session = Depends(get_db)):
    """Get statistics for a specific topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    test = db.query(Test).filter(Test.topic_id == topic_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="No test for this topic")
    
    results = db.query(TestResult).filter(TestResult.test_id == test.id).all()
    
    if results:
        average_score = sum([r.score for r in results]) / len(results)
        pass_count = len([r for r in results if r.passed])
        pass_rate = (pass_count / len(results)) * 100
    else:
        average_score = 0.0
        pass_rate = 0.0
    
    total_users = db.query(UserProgress).filter(UserProgress.topic_id == topic_id).count()
    
    return {
        "topic_id": topic_id,
        "topic_title": topic.title,
        "total_attempts": len(results),
        "average_score": average_score,
        "pass_rate": pass_rate,
        "total_users_attempted": total_users
    }
