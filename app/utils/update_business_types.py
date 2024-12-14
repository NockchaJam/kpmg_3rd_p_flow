from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models
import random

def update_business_types():
    db = SessionLocal()
    try:
        business_types = ["카페", "편의점", "음식점", "인테리어", "pc방", "체육관"]
        
        # 모든 CommercialBuilding 레코드 조회
        buildings = db.query(models.CommercialBuilding).all()
        
        # 각 레코드에 대해 랜덤 업종 할당
        for building in buildings:
            building.business_type = random.choice(business_types)
        
        db.commit()
        print("업종 정보 업데이트 완료")
        
    except Exception as e:
        print(f"업데이트 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_business_types() 