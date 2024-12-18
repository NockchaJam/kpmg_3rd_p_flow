from sqlalchemy import Column, Integer, String, Float
from .database import Base
from geoalchemy2 import Geometry

class CommercialBuilding(Base):
    __tablename__ = 'commercial_buildings'

    id = Column(Integer, primary_key=True, index=True)
    industry_category = Column(String(100), nullable=True)  # 대분류업종
    latitude = Column(Float, nullable=True)                 # 위도
    longitude = Column(Float, nullable=True)                # 경도
    sales_level = Column(String(50), nullable=True)        # 매출등급
    coordinates = Column(Geometry('POINT'), nullable=True)
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

class VacantListing(Base):
    __tablename__ = 'vacant_listings'

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=True)                # 위도
    longitude = Column(Float, nullable=True)               # 경도
    coordinates = Column(Geometry('POINT'), nullable=True)
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
