from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String(255), index=True)
    name = Column(String(100))
    description = Column(String(500))
    industry = Column(String(100))