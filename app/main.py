from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from . import models
from .database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware
from math import cos, radians

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

@app.get("/api/locations/search")
def search_locations(lat: float, lng: float, radius: float, db: Session = Depends(get_db)):
    # 위도/경도를 라디안으로 변환
    lat_rad = radians(lat)
    lng_rad = radians(lng)
    
    # Haversine 공식을 SQL로 구현
    distance_formula = func.acos(
        func.sin(lat_rad) * func.sin(func.radians(models.VacantListing.latitude)) +
        func.cos(lat_rad) * func.cos(func.radians(models.VacantListing.latitude)) *
        func.cos(func.radians(models.VacantListing.longitude) - lng_rad)
    ) * 6371000  # 지구 반지름 (미터)

    # 쿼리 실행
    vacants = db.query(models.VacantListing).filter(
        distance_formula <= radius
    )
    
    # 결과를 딕셔너리 리스트로 변환
    return [
        {
            "id": v.id,
            "property_type": v.property_type,
            "floor_info": v.floor_info,
            "deposit": v.deposit,
            "monthly_rent": v.monthly_rent,
            "formatted_price": v.formatted_price,
            "area1": v.area1,
            "area2": v.area2,
            "latitude": v.latitude,
            "longitude": v.longitude,
            "description": v.description
        }
        for v in vacants.all()
    ]
