from sqlalchemy import Column, Integer, String, Float
from .database import Base
from geoalchemy2 import Geometry

class CommercialBuilding(Base):
    __tablename__ = 'commercial_buildings'

    id = Column(Integer, primary_key=True, index=True)
    sales_level = Column(String(50), nullable=True)
    industry_category = Column(String(100), nullable=True)
    industry_code = Column(String(50), nullable=True)
    address = Column(String(200), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    coordinates = Column(Geometry('POINT'), nullable=True)
    
    # 주변 시설 정보
    num_of_company = Column(Integer, nullable=True)  # 3km 내 기업 수
    num_of_large = Column(Integer, nullable=True)    # 1km 내 대기업 수
    num_of_bus_stop = Column(Integer, nullable=True) # 500m 내 버스정류장 수
    num_of_hospital = Column(Integer, nullable=True) # 1km 내 병원 수
    num_of_theather = Column(Integer, nullable=True) # 1km 내 극장 수
    num_of_camp = Column(Integer, nullable=True)     # 3km 내 캠핑장 수
    num_of_school = Column(Integer, nullable=True)   # 500m 내 학교 수
    
    # 지하철 정보
    nearest_subway_name = Column(String(100), nullable=True)
    nearest_subway_distance = Column(Float, nullable=True)
    num_of_subway = Column(Integer, nullable=True)   # 500m 내 지하철역 수
    
    # 기타 시설
    num_of_gvn_office = Column(Integer, nullable=True) # 500m 내 관공서 수
    parks_within_500m = Column(Integer, nullable=True)
    parking_lots_within_500m = Column(Integer, nullable=True)
    
    # 대학교 거리별 수
    university_within_0m_500m = Column(Integer, nullable=True)
    university_within_500m_1000m = Column(Integer, nullable=True)
    university_within_1000m_1500m = Column(Integer, nullable=True)
    university_within_1500m_2000m = Column(Integer, nullable=True)

    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

class VacantListing(Base):
    __tablename__ = 'vacant_listings'

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    coordinates = Column(Geometry('POINT'), nullable=True)
    
    # 주변 시설 정보
    num_of_company = Column(Integer, nullable=True)  # 3km 내 기업 수
    num_of_large = Column(Integer, nullable=True)    # 1km 내 대기업 수
    num_of_bus_stop = Column(Integer, nullable=True) # 500m 내 버스정류장 수
    num_of_hospital = Column(Integer, nullable=True) # 1km 내 병원 수
    num_of_theather = Column(Integer, nullable=True) # 1km 내 극장 수
    num_of_camp = Column(Integer, nullable=True)     # 3km 내 캠핑장 수
    num_of_school = Column(Integer, nullable=True)   # 500m 내 학교 수
    
    # 지하철 정보
    nearest_subway_name = Column(String(100), nullable=True)
    nearest_subway_distance = Column(Float, nullable=True)
    num_of_subway = Column(Integer, nullable=True)   # 500m 내 지하철역 수
    
    # 기타 시설
    num_of_gvn_office = Column(Integer, nullable=True) # 500m 내 관공서 수
    parks_within_500m = Column(Integer, nullable=True)
    parking_lots_within_500m = Column(Integer, nullable=True)
    
    # 대학교 거리별 수
    university_within_0m_500m = Column(Integer, nullable=True)
    university_within_500m_1000m = Column(Integer, nullable=True)
    university_within_1000m_1500m = Column(Integer, nullable=True)
    university_within_1500m_2000m = Column(Integer, nullable=True)

    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
