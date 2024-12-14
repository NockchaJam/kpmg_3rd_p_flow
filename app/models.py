from sqlalchemy import Column, Integer, String, Float
from .database import Base
from geoalchemy2 import Geometry

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String(255), index=True)
    name = Column(String(100))
    description = Column(String(500))
    industry = Column(String(100))
    coordinates = Column(Geometry('POINT'), nullable=False)
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

class CommercialBuilding(Base):
    __tablename__ = 'commercial_buildings'

    id = Column(Integer, primary_key=True, index=True)
    building_name = Column(String(100), nullable=True)
    address = Column(String(255), index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    postal_code = Column(String(20), nullable=True)
    floor_info = Column(String(50), nullable=True)
    business_type = Column(String(50), nullable=True)
    coordinates = Column(Geometry('POINT'), nullable=False)
    score = Column(Integer, nullable=True)
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

class VacantListing(Base):
    __tablename__ = 'vacant_listings'

    id = Column(Integer, primary_key=True, index=True)
    property_type = Column(String(50), nullable=True)
    verification_type = Column(String(50), nullable=True)
    floor_info = Column(String(100), nullable=True)
    deposit = Column(Integer, nullable=True)
    monthly_rent = Column(Integer, nullable=True)
    formatted_price = Column(String(100), nullable=True)
    area1 = Column(Float, nullable=True)
    area2 = Column(Float, nullable=True)
    direction = Column(String(50), nullable=True)
    confirmation_date = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String(1000), nullable=True)
    coordinates = Column(Geometry('POINT'), nullable=False)
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
