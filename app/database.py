from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SSL 관련 설정 추가
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:12345678@localhost/location_data?charset=utf8mb4"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 데이터 베이스 테스트 코드
# def check_database_connection():
#     try:
#         with engine.connect() as connection:
#             result = connection.execute(text("SELECT 1"))
#             print("Database connection successful:", result.scalar() == 1)
#     except Exception as e:
#         print("Database connection failed:", e)

# # Call the function to check the connection
# check_database_connection()
