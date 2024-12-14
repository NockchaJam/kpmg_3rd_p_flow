import pandas as pd
from sqlalchemy.orm import Session
from .. import models
from ..database import SessionLocal, engine
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import inspect
import random

def process_building_row(row):
    """total_seoul_info_ree2.csv 데이터 처리"""
    try:
        if pd.isna(row['위도']) or pd.isna(row['경도']):
            return None
            
        def safe_str(value):
            return str(value) if pd.notna(value) else ''
            
        # 랜덤 업종 선택
        business_types = ["카페", "편의점", "음식점", "인테리어", "pc방", "체육관"]
        random_business = random.choice(business_types)
        
        # 1부터 100까지의 랜덤 점수 생성
        random_score = random.randint(1, 100)
            
        return {
            'building_name': safe_str(row.get('건물명', '')),
            'address': row['도로명주소'],
            'latitude': float(row['위도']),
            'longitude': float(row['경도']),
            'postal_code': safe_str(row.get('신우편번호', '')),
            'floor_info': safe_str(row.get('층정보', '')),
            'business_type': random_business,
            'coordinates': from_shape(Point(float(row['경도']), float(row['위도']))),
            'score': random_score  # 랜덤 점수 추가
        }
    except Exception as e:
        print(f"건물 데이터 행 처리 중 오류 발생: {row}")
        print(f"오류 내용: {e}")
        return None

def process_vacant_row(row):
    """naver_test_data2.csv 데이터 처리"""
    try:
        if pd.isna(row['lat']) or pd.isna(row['lng']):
            return None
            
        # 모든 필드에 대해 NaN 처리
        def safe_str(value):
            return str(value) if pd.notna(value) else ''
            
        def safe_float(value):
            if pd.isna(value):
                return 0.0
            try:
                # 문자열에서 숫자만 추출
                value_str = str(value)
                num_str = ''.join(filter(lambda x: x.isdigit() or x == '.', value_str))
                return float(num_str) if num_str else 0.0
            except:
                return 0.0
            
        def parse_price(value):
            if pd.isna(value):
                return 0
            try:
                # 문자열에서 숫자만 추출
                value_str = str(value)
                num_str = ''.join(filter(str.isdigit, value_str))
                return int(num_str) if num_str else 0
            except:
                return 0
            
        # 가격 정보 처리
        deposit = parse_price(row['prc'])
        monthly_rent = parse_price(row['rentPrc'])
        
        return {
            'property_type': safe_str(row['tradTpNm']),
            'verification_type': safe_str(row['vrfcTpCd']),
            'floor_info': safe_str(row['flrInfo']),
            'deposit': deposit,
            'monthly_rent': monthly_rent,
            'formatted_price': safe_str(row['hanPrc']),
            'area1': safe_float(row['spc1']),
            'area2': safe_float(row['spc2']),
            'direction': safe_str(row['direction']),
            'confirmation_date': safe_str(row['atclCfmYmd']),
            'latitude': float(row['lat']),
            'longitude': float(row['lng']),
            'description': safe_str(row['atclFetrDesc']),
            'coordinates': from_shape(Point(float(row['lng']), float(row['lat'])))
        }
    except Exception as e:
        print(f"공실 데이터 행 처리 중 오류 발생: {row}")
        print(f"오류 내용: {e}")
        return None

def check_tables():
    """데이터베이스 테이블 존재 여부 확인"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("현재 존재하는 테이블:", tables)
    
    # CommercialBuilding 테이블 컬럼 확인
    if 'commercial_buildings' in tables:
        columns = [col['name'] for col in inspector.get_columns('commercial_buildings')]
        print("\ncommercial_buildings 테이블 컬럼:", columns)

def import_commercial_data(building_file: str = './data/total_seoul_info_ree2.csv', 
                         vacant_file: str = './data/naver_test_data2.csv',
                         batch_size: int = 100):
    """상가 및 공실 데이터 임포트"""
    # 테이블 체크 추가
    check_tables()
    
    db = None
    try:
        db = SessionLocal()
        
        # CSV 파일 확인
        print(f"\n건물 데이터 파일 확인:")
        building_df = pd.read_csv(
            building_file, 
            encoding='utf-8',
            names=['건물본번지', '건물부번지', '건물관리번호', '건물명', '도로명주소', 
                   '구우편번호', '신우편번호', '동정보', '층정보', '호정보', 
                   '경도', '위도', '총점']
        )
        print("건물 데이터 샘플:")
        print(building_df.head())
        print("\n건물 데이터 컬럼명:", building_df.columns.tolist())
        
        # 기존 데이터 삭제
        db.query(models.CommercialBuilding).delete()
        db.query(models.VacantListing).delete()
        db.commit()
        
        # 상가건물 데이터 임포트
        buildings = []
        
        for _, row in building_df.iterrows():
            try:
                data = process_building_row(row)
                if data:
                    building_obj = models.CommercialBuilding(**data)
                    buildings.append(building_obj)
                    
                    if len(buildings) >= batch_size:
                        db.bulk_save_objects(buildings)
                        db.commit()
                        buildings = []
            except Exception as e:
                print(f"건물 데이터 처리 중 오류: {e}")
                continue
        
        if buildings:
            try:
                db.bulk_save_objects(buildings)
                db.commit()
            except Exception as e:
                print(f"건물 데이터 최종 저장 중 오류: {e}")
                db.rollback()
        
        # 공실 매물 데이터 임포트
        print(f"\n공실 데이터 파일 확인:")
        
        # 컬럼명을 명시적으로 지정하여 CSV 읽기
        vacant_columns = ['tradTpNm', 'vrfcTpCd', 'flrInfo', 'prc', 'rentPrc', 
                         'hanPrc', 'spc1', 'spc2', 'direction', 'atclCfmYmd', 
                         'lat', 'lng', 'atclFetrDesc']
        
        vacant_df = pd.read_csv(
            vacant_file, 
            encoding='utf-8',
            usecols=vacant_columns  # 사용할 컬럼만 명시적으로 지정
        )
        
        # 데이터 타입 변환
        try:
            vacant_df['lat'] = pd.to_numeric(vacant_df['lat'], errors='coerce')
            vacant_df['lng'] = pd.to_numeric(vacant_df['lng'], errors='coerce')
            vacant_df['spc1'] = pd.to_numeric(vacant_df['spc1'], errors='coerce')
            vacant_df['spc2'] = pd.to_numeric(vacant_df['spc2'], errors='coerce')
        except Exception as e:
            print(f"데이터 타입 변환 중 오류: {e}")
        
        print("공실 데이터 샘플:")
        print(vacant_df.head())
        print("\n공실 데이터 컬럼명:", vacant_df.columns.tolist())
        print("\n데이터 타입:", vacant_df.dtypes)
        
        vacants = []
        
        for _, row in vacant_df.iterrows():
            try:
                data = process_vacant_row(row)
                if data:
                    vacant_obj = models.VacantListing(**data)
                    vacants.append(vacant_obj)
                    
                    if len(vacants) >= batch_size:
                        db.bulk_save_objects(vacants)
                        db.commit()
                        vacants = []
            except Exception as e:
                print(f"공실 데이터 처리 중 오류: {e}")
                continue
        
        if vacants:
            try:
                db.bulk_save_objects(vacants)
                db.commit()
            except Exception as e:
                print(f"공실 데이터 최종 저장 중 오류: {e}")
                db.rollback()
            
    except Exception as e:
        print(f"데이터 임포트 중 오류: {e}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    import_commercial_data()