from fastapi import FastAPI
from app.schemas import WordResponse
from fastapi import HTTPException
from app.routers import words
from app.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

from fastapi import APIRouter, Depends, HTTPException
import random

from app.schemas import ValidateSentenceRequest, ValidateSentenceResponse
from app.models import Word, PracticeSession
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils import mock_ai_validation


Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Vocabulary Practice API",
    version="1.0.0",
    description="API for vocabulary practice and learning"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(words.router, prefix="/api", tags=["words"])

@app.get("/")
def read_root():
    return {
        "message": "Vocabulary Practice API",
        "version": "1.0.0",
        "endpoints": {
            "random_word": "/api/word",
            "validate": "/api/validate-sentence",
            "summary": "/api/summary",
            "history": "/api/history"
        }
    }

@app.post("/api/validate-sentence", response_model=ValidateSentenceResponse)
def validate_sentence(request: ValidateSentenceRequest, db: Session = Depends(get_db)):
    word = db.query(Word).filter(Word.id == request.word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    result = mock_ai_validation(
        request.sentence,
        word.word,
        word.difficulty_level
    )

    session_record = PracticeSession(
        word_id=word.id,
        user_sentence=request.sentence,
        score=result["score"],
        feedback=result["suggestion"],
        corrected_sentence=result["corrected_sentence"]
        # practiced_at: auto
    )

    db.add(session_record)
    db.commit()
    db.refresh(session_record)

    return ValidateSentenceResponse(
        score=result["score"],
        level=result["level"],
        suggestion=result["suggestion"],
        corrected_sentence=result["corrected_sentence"]
    )