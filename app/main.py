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
    ).all()
    
    # 각 공실 위치별로 주변 상가들의 평균 점수 계산
    result_with_scores = []
    for vacant in vacants:
        # 해당 공실 주변의 상가들 검색
        nearby_business_scores = db.query(
            func.avg(models.CommercialBuilding.score).label('avg_score')
        ).filter(
            func.acos(
                func.sin(radians(vacant.latitude)) * 
                func.sin(func.radians(models.CommercialBuilding.latitude)) +
                func.cos(radians(vacant.latitude)) * 
                func.cos(func.radians(models.CommercialBuilding.latitude)) *
                func.cos(func.radians(models.CommercialBuilding.longitude) - 
                        radians(vacant.longitude))
            ) * 6371000 <= 100  # 100미터 반경 내의 상가들
        ).scalar()

        avg_score = round(nearby_business_scores) if nearby_business_scores else 0
        
        result_with_scores.append({
            "id": vacant.id,
            "property_type": vacant.property_type,
            "floor_info": vacant.floor_info,
            "deposit": vacant.deposit,
            "monthly_rent": vacant.monthly_rent,
            "formatted_price": vacant.formatted_price,
            "area1": vacant.area1,
            "area2": vacant.area2,
            "latitude": vacant.latitude,
            "longitude": vacant.longitude,
            "description": vacant.description,
            "area_score": avg_score  # 평균 점수 추가
        })
    
    return result_with_scores

@app.get("/api/businesses/search")
def search_businesses(
    lat: float, 
    lng: float, 
    radius: float, 
    business_type: str,
    db: Session = Depends(get_db)
):
    # 위도/경도를 라디안으로 변환
    lat_rad = radians(lat)
    lng_rad = radians(lng)
    
    # Haversine 공식을 SQL로 구현
    distance_formula = func.acos(
        func.sin(lat_rad) * func.sin(func.radians(models.CommercialBuilding.latitude)) +
        func.cos(lat_rad) * func.cos(func.radians(models.CommercialBuilding.latitude)) *
        func.cos(func.radians(models.CommercialBuilding.longitude) - lng_rad)
    ) * 6371000  # 지구 반지름 (미터)

    # 쿼리 실행
    businesses = db.query(models.CommercialBuilding).filter(
        and_(
            distance_formula <= radius,
            models.CommercialBuilding.business_type == business_type
        )
    )
    
    return [
        {
            "id": b.id,
            "building_name": b.building_name,
            "address": b.address,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "business_type": b.business_type,
            "floor_info": b.floor_info,
            "score": b.score
        }
        for b in businesses.all()
    ]
