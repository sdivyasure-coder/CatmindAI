from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Leaderboard, User, Language

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/{language_id}")
def get_language_leaderboard(language_id: int, db: Session = Depends(get_db)):
    """Get leaderboard for a language"""
    language = db.query(Language).filter(Language.id == language_id).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    
    entries = db.query(Leaderboard).filter(
        Leaderboard.language_id == language_id
    ).order_by(Leaderboard.completion_time).all()
    
    return [
        {
            "rank": rank,
            "user_email": entry.user.email,
            "completion_time": entry.completion_time,
            "completed_at": entry.completed_at
        }
        for rank, entry in enumerate(entries, 1)
    ]


@router.get("/global/top")
def get_global_leaderboard(limit: int = 100, db: Session = Depends(get_db)):
    """Get global leaderboard across all languages"""
    entries = db.query(Leaderboard).order_by(
        Leaderboard.completion_time
    ).limit(limit).all()
    
    return [
        {
            "rank": rank,
            "user_email": entry.user.email,
            "language": entry.language.name,
            "completion_time": entry.completion_time,
            "completed_at": entry.completed_at
        }
        for rank, entry in enumerate(entries, 1)
    ]


@router.post("/update-rank/{user_id}/{language_id}")
def update_user_rank(user_id: int, language_id: int, db: Session = Depends(get_db)):
    """Update user rank on leaderboard"""
    leaderboard_entry = db.query(Leaderboard).filter(
        Leaderboard.user_id == user_id,
        Leaderboard.language_id == language_id
    ).first()
    
    if not leaderboard_entry:
        raise HTTPException(status_code=404, detail="Leaderboard entry not found")
    
    rank = db.query(Leaderboard).filter(
        Leaderboard.language_id == language_id,
        Leaderboard.completion_time < leaderboard_entry.completion_time
    ).count() + 1
    
    leaderboard_entry.rank = rank
    db.commit()
    
    return {"rank": rank, "message": "Rank updated successfully"}
