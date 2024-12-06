from ..database import engine
from .. import models
from sqlalchemy import text
from sqlalchemy import inspect

def create_commercial_tables():
    """상가 및 공실 관련 테이블 생성"""
    try:
        # 직접 SQL로 테이블 삭제 (IF EXISTS 사용)
        with engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS vacant_listings"))
            connection.execute(text("DROP TABLE IF EXISTS commercial_buildings"))
            connection.commit()
        
        # 새로운 테이블 생성
        models.Base.metadata.create_all(bind=engine)
        print("테이블이 성공적으로 생성되었습니다.")
        
        # 테이블 생성 확인
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("생성된 테이블:", tables)
        
    except Exception as e:
        print(f"테이블 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    create_commercial_tables() 