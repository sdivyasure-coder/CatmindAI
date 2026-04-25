from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
import json
from app.database import get_db
from app.models import User, Test, TestResult, Topic, UserProgress, ProgressStatus
from app.schemas.test import TestCreate, TestResponse, TestStartRequest, TestSubmitRequest, TestResultResponse
from app.utils.security import decode_token

router = APIRouter(prefix="/tests", tags=["tests"])


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


@router.post("/{topic_id}/start", response_model=TestResponse)
def start_test(topic_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start a test for a topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    test = db.query(Test).filter(Test.topic_id == topic_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found for this topic")
    
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.topic_id == topic_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            topic_id=topic_id,
            status=ProgressStatus.IN_PROGRESS
        )
        db.add(progress)
    
    db.commit()
    db.refresh(test)
    return test


@router.get("/{test_id}/questions")
def get_test_questions(test_id: int, db: Session = Depends(get_db)):
    """Get test questions"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    try:
        questions = json.loads(test.questions) if isinstance(test.questions, str) else test.questions
    except:
        questions = [{"question": test.questions}]
    
    return {
        "test_id": test_id,
        "topic_id": test.topic_id,
        "questions": questions,
        "passing_percentage": test.passing_percentage
    }


@router.post("/{test_id}/submit", response_model=TestResultResponse)
def submit_test(test_id: int, request: TestSubmitRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Submit test answers"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    score = calculate_score(request.answers, test.questions)
    passed = score >= test.passing_percentage
    
    result = TestResult(
        user_id=current_user.id,
        test_id=test_id,
        score=score,
        passed=passed,
        answers=json.dumps(request.answers),
        performance_report=None
    )
    db.add(result)
    
    if passed:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.topic_id == test.topic_id
        ).first()
        if progress:
            progress.status = ProgressStatus.COMPLETED
            progress.passed_at = datetime.utcnow()
    else:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.topic_id == test.topic_id
        ).first()
        if progress:
            progress.attempts += 1
    
    db.commit()
    db.refresh(result)
    return result


@router.post("/{test_id}/analyze")
def analyze_test(test_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get AI-based answer analysis and performance report"""
    result = db.query(TestResult).filter(
        TestResult.test_id == test_id,
        TestResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    test = db.query(Test).filter(Test.id == test_id).first()
    
    report = generate_performance_report(result.score, test.passing_percentage, result.answers)
    result.performance_report = report
    
    db.commit()
    
    return {
        "test_id": test_id,
        "score": result.score,
        "passed": result.passed,
        "passing_percentage": test.passing_percentage,
        "report": report
    }


def calculate_score(answers: dict, questions: str) -> float:
    """Calculate test score based on answers"""
    try:
        question_list = json.loads(questions) if isinstance(questions, str) else questions
    except:
        question_list = [{"question": questions}]
    
    correct_count = len([a for a in answers.values() if a])
    total = len(question_list) if isinstance(question_list, list) else 1
    
    return (correct_count / max(total, 1)) * 100


def generate_performance_report(score: float, passing_percentage: float, answers: str) -> str:
    """Generate AI-based performance report"""
    if score >= passing_percentage:
        return f"Excellent! You scored {score:.1f}%, which exceeds the passing percentage of {passing_percentage}%."
    else:
        return f"You scored {score:.1f}%, which is below the passing percentage of {passing_percentage}%. Review the material and try again."
