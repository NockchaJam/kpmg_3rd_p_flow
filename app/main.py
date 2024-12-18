from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models
from .database import SessionLocal, engine
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델 정의
class CommercialBuildingBase(BaseModel):
    industry_category: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    sales_level: str | None = None

class VacantListingBase(BaseModel):
    latitude: float | None = None
    longitude: float | None = None

class CommercialBuilding(CommercialBuildingBase):
    id: int

    class Config:
        orm_mode = True

class VacantListing(VacantListingBase):
    id: int

    class Config:
        orm_mode = True

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/commercial-buildings/", response_model=List[CommercialBuilding])
def get_commercial_buildings(db: Session = Depends(get_db)):
    """상가 데이터 조회"""
    buildings = db.query(models.CommercialBuilding).all()
    return buildings

@app.get("/vacant-listings/", response_model=List[VacantListing])
def get_vacant_listings(db: Session = Depends(get_db)):
    """공실 데이터 조회"""
    vacants = db.query(models.VacantListing).all()
    return vacants

@app.get("/commercial-buildings/nearby/")
def get_nearby_commercial_buildings(
    lat: float, 
    lng: float, 
    radius: float = 1000, 
    industry_category: str | None = None,
    db: Session = Depends(get_db)
):
    """주변 상가 데이터 조회"""
    print(f"\n주변 상가 검색 요청 받음:")
    print(f"위도: {lat}, 경도: {lng}, 반경: {radius}m")
    print(f"선택된 업종: {industry_category}")
    
    # 업종 필터링 조건 추가
    query = text("""
        SELECT id, industry_category, latitude, longitude, sales_level,
            ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) as distance
        FROM commercial_buildings
        WHERE ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) <= :radius
        AND (:industry_category IS NULL OR industry_category = :industry_category)
        ORDER BY distance;
    """)
    
    point = f'POINT({lng} {lat})'
    try:
        result = db.execute(query, {
            'point': point, 
            'radius': radius,
            'industry_category': industry_category
        })
        
        buildings = []
        for row in result:
            buildings.append({
                'id': row.id,
                'industry_category': row.industry_category,
                'latitude': row.latitude,
                'longitude': row.longitude,
                'sales_level': row.sales_level,
                'distance': row.distance
            })
        
        print(f"검색 결과: {len(buildings)}개의 상가 발견")
        if len(buildings) > 0:
            print("첫 번째 결과:")
            print(f"- ID: {buildings[0]['id']}")
            print(f"- 업종: {buildings[0]['industry_category']}")
            print(f"- 위치: ({buildings[0]['latitude']}, {buildings[0]['longitude']})")
            print(f"- 거리: {buildings[0]['distance']}m")
            
        return buildings
        
    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations/search")
def search_locations(lat: float, lng: float, radius: float = 1000, db: Session = Depends(get_db)):
    """위치 기반 공실 검색"""
    print(f"\n공실 검색 요청 받음:")
    print(f"위도: {lat}, 경도: {lng}, 반경: {radius}m")
    
    query = text("""
        SELECT id, latitude, longitude,
            ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) as distance
        FROM vacant_listings
        WHERE ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) <= :radius
        ORDER BY distance;
    """)
    
    point = f'POINT({lng} {lat})'
    print(f"검색 포인트: {point}")
    
    try:
        result = db.execute(query, {'point': point, 'radius': radius})
        
        vacants = []
        for row in result:
            vacants.append({
                'id': row.id,
                'latitude': row.latitude,
                'longitude': row.longitude,
                'distance': row.distance
            })
        
        print(f"검색 결과: {len(vacants)}개의 공실 발견")
        if len(vacants) > 0:
            print("첫 번째 결과:")
            print(f"- ID: {vacants[0]['id']}")
            print(f"- 위치: ({vacants[0]['latitude']}, {vacants[0]['longitude']})")
            print(f"- 거리: {vacants[0]['distance']}m")
        
        return vacants
        
    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/business-categories")
def get_business_categories(db: Session = Depends(get_db)):
    """상가 업종 카테고리 목록 조회"""
    try:
        # industry_category 컬럼의 고유한 값들을 조회
        query = text("""
            SELECT DISTINCT industry_category 
            FROM commercial_buildings 
            WHERE industry_category IS NOT NULL 
            ORDER BY industry_category;
        """)
        
        result = db.execute(query)
        categories = [row[0] for row in result if row[0]]  # None 값 제외
        
        print(f"업종 카테고리 조회 결과: {len(categories)}개 카테고리 발견")
        print("카테고리 목록:", categories)
        
        return categories
        
    except Exception as e:
        print(f"업종 카테고리 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))
