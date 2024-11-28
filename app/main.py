from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models
from .database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 앱의 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/locations/recent")
def get_recent_locations(db: Session = Depends(get_db)):
    locations = db.query(models.Location).limit(5).all()
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "address": loc.address,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "description": loc.description,
            "industry": loc.industry
        }
        for loc in locations
    ]
