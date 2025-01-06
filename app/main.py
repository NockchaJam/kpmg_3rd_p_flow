from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models
from .database import SessionLocal, engine
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
import os
import requests

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

# Pydantic 모델 추가
class VacantReportData(BaseModel):
    lat: float
    lng: float
    vacant_data: List[dict]
    selected_business_type: str | None = None
    search_radius: float  # 검색 반경 추가

# Pydantic 모델 수정/추가
class StoreReportData(BaseModel):
    lat: float
    lng: float
    selected_business_type: str | None = None
    search_radius: float

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
            
        return buildings
        
    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations/search")
def search_locations(lat: float, lng: float, radius: float = 1000, db: Session = Depends(get_db)):
    """위치 기반 공실 검색"""
    query = text("""
        SELECT id, latitude, longitude,
            ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) as distance
        FROM vacant_listings
        WHERE ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) <= :radius
        ORDER BY distance;
    """)
    
    point = f'POINT({lng} {lat})'
    
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
        
        return vacants
        
    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/business-categories")
def get_business_categories(db: Session = Depends(get_db)):
    """상가 업종 카테고리 목록 조회"""
    try:
        query = text("""
            SELECT DISTINCT industry_category 
            FROM commercial_buildings 
            WHERE industry_category IS NOT NULL 
            ORDER BY industry_category;
        """)
        
        result = db.execute(query)
        categories = [row[0] for row in result if row[0]]
        
        return categories
        
    except Exception as e:
        print(f"업종 카테고리 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nearest-vacant-listings/")
def get_nearest_vacant_listings(
    lat: float, 
    lng: float, 
    db: Session = Depends(get_db)
):
    """클릭한 좌표에서 가장 가까운 공실 3개의 상세 정보 조회"""
    query = text("""
        WITH nearest_three AS (
            SELECT id, 
                ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) as distance
            FROM vacant_listings
            ORDER BY ST_Distance_Sphere(coordinates, ST_GeomFromText(:point))
            LIMIT 3
        )
        SELECT 
            v.*,
            n.distance
        FROM vacant_listings v
        JOIN nearest_three n ON v.id = n.id
        ORDER BY n.distance;
    """)
    
    point = f'POINT({lng} {lat})'
    
    try:
        result = db.execute(query, {'point': point})
        
        vacants = []
        for row in result:
            vacant_data = {
                'id': row.id,
                'latitude': row.latitude,
                'longitude': row.longitude,
                'distance': row.distance,
                
                # 주변 시설 정보
                'num_of_company': row.num_of_company,
                'num_of_large': row.num_of_large,
                'num_of_bus_stop': row.num_of_bus_stop,
                'num_of_hospital': row.num_of_hospital,
                'num_of_theather': row.num_of_theather,
                'num_of_camp': row.num_of_camp,
                'num_of_school': row.num_of_school,
                
                # 지하철 정보
                'nearest_subway_name': row.nearest_subway_name,
                'nearest_subway_distance': row.nearest_subway_distance,
                'num_of_subway': row.num_of_subway,
                
                # 기타 시설
                'num_of_gvn_office': row.num_of_gvn_office,
                'parks_within_500m': row.parks_within_500m,
                'parking_lots_within_500m': row.parking_lots_within_500m,
                
                # 대학교 거리별 수
                'university_within_0m_500m': row.university_within_0m_500m,
                'university_within_500m_1000m': row.university_within_500m_1000m,
                'university_within_1000m_1500m': row.university_within_1000m_1500m,
                'university_within_1500m_2000m': row.university_within_1500m_2000m
            }
            vacants.append(vacant_data)
        
        return vacants
        
    except Exception as e:
        print(f"가장 가까운 공실 검색 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save-vacant-report/")
def save_vacant_report(data: VacantReportData, db: Session = Depends(get_db)):
    """공실 분석 리포트 데이터 저장"""
    try:
        # 가장 가까운 공실 3개 검색 (위도/경도 중복 제외)
        nearest_query = text("""
            WITH ranked_locations AS (
                SELECT 
                    id,
                    latitude,
                    longitude,
                    ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) as distance,
                    ROW_NUMBER() OVER (
                        PARTITION BY latitude, longitude 
                        ORDER BY id
                    ) as rn
                FROM vacant_listings
            )
            SELECT 
                v.*,
                r.distance
            FROM vacant_listings v
            JOIN (
                SELECT id, distance
                FROM ranked_locations
                WHERE rn = 1
                ORDER BY distance
                LIMIT 3
            ) r ON v.id = r.id
            ORDER BY r.distance;
        """)
        
        point = f'POINT({data.lng} {data.lat})'
        result = db.execute(nearest_query, {'point': point})
        
        # 데이터를 컬럼별로 묶기
        aggregated_data = {
            'avg_sales_level': [],
            'selected_business_type': [],
            
            # 주변 시설 정보
            'num_of_company': [],
            'num_of_large': [],
            'num_of_bus_stop': [],
            'num_of_hospital': [],
            'num_of_theather': [],
            'num_of_camp': [],
            'num_of_school': [],
            
            # 지하철 정보
            'nearest_subway_name': [],
            'nearest_subway_distance': [],
            'num_of_subway': [],
            
            # 기타 시설
            'num_of_gvn_office': [],
            'parks_within_500m': [],
            'parking_lots_within_500m': []
            
            # # 대학교 거리별 수
            # 'university_within_0m_500m': [],
            # 'university_within_500m_1000m': [],
            # 'university_within_1000m_1500m': [],
            # 'university_within_1500m_2000m': []
        }
        
        for row in result:
            # 각 공실 주변의 상가 데이터 조회 (사용자가 지정한 반경 사용)
            nearby_query = text("""
                SELECT sales_level
                FROM commercial_buildings
                WHERE ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) <= :radius
                AND industry_category = :business_type
                AND sales_level IS NOT NULL
            """)
            
            vacant_point = f'POINT({row.longitude} {row.latitude})'
            nearby_result = db.execute(nearby_query, {
                'point': vacant_point,
                'business_type': data.selected_business_type,
                'radius': data.search_radius
            })
            
            # 매출 등급 평균 계산
            sales_levels = [int(r.sales_level) for r in nearby_result if r.sales_level.isdigit()]
            avg_sales_level = sum(sales_levels) / len(sales_levels) if sales_levels else 0
            
            # 기본 정보 추가 (distance 제거)
            aggregated_data['avg_sales_level'].append(f"{avg_sales_level:.2f}")
            aggregated_data['selected_business_type'].append(data.selected_business_type)
            
            # 나머지 필드들 추가
            for key in aggregated_data.keys():
                if key not in ['avg_sales_level', 'selected_business_type']:
                    aggregated_data[key].append(getattr(row, key))
        
        # 필요한 메타데이터를 aggregated_data에 포함
        data_to_save = aggregated_data
        
        # data 디렉토리가 없으면 생성
        os.makedirs('data/collected_samples', exist_ok=True)
        
        # 파일명에 타임스탬프 포함
        filename = f'data/collected_samples/vacant_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # JSON 파일 저장
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, separators=(',', ':'))

        # API 호출 - HTTP 프로토콜 사용
        response = requests.post(
            "http://213.173.110.34:17618/ma/analyze1",  # RunPod의 HTTP 포트(8000) 사용
            json=data_to_save,
            headers={'Content-Type': 'application/json'}  # HTTP 헤더 명시
        )
        
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail="외부 API 호출 실패")
            
        analysis_result = response.json()['result']
        
        return {
            "status": "success",
            "filename": filename,
            "analysis": analysis_result
        }
        
    except Exception as e:
        print(f"리포트 데이터 저장 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save-store-report/")
def save_store_report(data: StoreReportData, db: Session = Depends(get_db)):
    """상가 분석 리포트 데이터 저장"""
    try:
        # 가장 가까운 상가 3개 검색 (위도/경도 중복 제외)
        nearest_query = text("""
            WITH ranked_locations AS (
                SELECT 
                    id,
                    latitude,
                    longitude,
                    industry_category,
                    sales_level,
                    ST_Distance_Sphere(coordinates, ST_GeomFromText(:point)) as distance,
                    ROW_NUMBER() OVER (
                        PARTITION BY latitude, longitude 
                        ORDER BY id
                    ) as rn
                FROM commercial_buildings
                WHERE industry_category = :business_type
            )
            SELECT 
                c.*,
                r.distance
            FROM commercial_buildings c
            JOIN (
                SELECT id, distance
                FROM ranked_locations
                WHERE rn = 1
                ORDER BY distance
                LIMIT 3
            ) r ON c.id = r.id
            ORDER BY r.distance;
        """)
        
        point = f'POINT({data.lng} {data.lat})'
        result = db.execute(nearest_query, {
            'point': point,
            'business_type': data.selected_business_type
        })
        
        # 데이터를 컬럼별로 묶기
        aggregated_data = {
            '매출등급': [],
            '대분류업종': [],
            '대분류업종코드': [],
            'distance': [],
            'gongsil_latitude': [],
            'gongsil_longitude': [],
            
            # 주변 시설 정보
            'num_of_company': [],
            'num_of_large': [],
            'num_of_bus_stop': [],
            'num_of_hospital': [],
            'num_of_theather': [],
            'num_of_camp': [],
            'num_of_school(near 500m)': [],
            
            # 지하철 정보
            'nearest_subway_name': [],
            'nearest_subway_distance': [],
            'num_of_subway': [],
            
            # 기타 시설
            'num_of_gvn_office(near 500m)': [],
            'parks_within_500m': [],
            'parking_lots_within_500m': [],
            
            # 대학교 거리별 수
            'university_within_0m_500m': [],
            'university_within_500m_1000m': [],
            'university_within_1000m_1500m': [],
            'university_within_1500m_2000m': []
        }
        
        for row in result:
            for key in aggregated_data.keys():
                if key not in ['gongsil_latitude', 'gongsil_longitude']:  # 공실 좌표는 별도 처리
                    if key == '매출등급':
                        aggregated_data[key].append(getattr(row, 'sales_level'))
                    elif key == '대분류업종':
                        aggregated_data[key].append(getattr(row, 'industry_category'))
                    elif key == '대분류업종코드':
                        aggregated_data[key].append(getattr(row, 'industry_code'))
                    elif key == 'num_of_school(near 500m)':
                        aggregated_data[key].append(getattr(row, 'num_of_school'))
                    elif key == 'num_of_gvn_office(near 500m)':  # num_of_gvn_office 데이터 매핑
                        aggregated_data[key].append(getattr(row, 'num_of_gvn_office'))
                    else:
                        aggregated_data[key].append(getattr(row, key))
            # distance는 result의 distance 값을 사용
            aggregated_data['distance'][-1] = row.distance
            # 공실 좌표 추가
            aggregated_data['gongsil_latitude'].append(data.lat)
            aggregated_data['gongsil_longitude'].append(data.lng)
        
        # 필요한 메타데이터를 aggregated_data에 포함
        data_to_save = aggregated_data
        
        # data 디렉토리가 없으면 생성
        os.makedirs('data/collected_samples', exist_ok=True)
        
        # 파일명에 타임스탬프 포함
        filename = f'data/collected_samples/store_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # JSON 파일 저장
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, separators=(',', ':'))

        # API 호출 - HTTP 프로토콜 사용
        response = requests.post(
            "http://213.173.110.34:17618/ma/analyze2",  # RunPod의 HTTP 포트(8000) 사용
            json=data_to_save,
            headers={'Content-Type': 'application/json'}  # HTTP 헤더 명시
        )

        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail="외부 API 호출 실패")
            
        analysis_result = response.json()['result']
        
        return {
            "status": "success",
            "filename": filename,
            "analysis": analysis_result
        }
        
    except Exception as e:
        print(f"상가 리포트 데이터 저장 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))
