import pandas as pd
from sqlalchemy.orm import Session
from .. import models
from ..database import SessionLocal, engine
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import random

def process_store_row(row):
    """final_data.csv 데이터 처리"""
    try:
        if pd.isna(row['위도']) or pd.isna(row['경도']):
            return None
            
        def safe_str(value):
            return str(value) if pd.notna(value) else None
            
        def safe_float(value):
            try:
                return float(value) if pd.notna(value) else None
            except:
                return None
            
        return {
            'industry_category': safe_str(row['대분류업종']),
            'latitude': safe_float(row['위도']),
            'longitude': safe_float(row['경도']),
            'sales_level': safe_str(row['매출등급']),
            'coordinates': from_shape(Point(float(row['경도']), float(row['위도']))) if not pd.isna(row['경도']) and not pd.isna(row['위도']) else None
        }
    except Exception as e:
        print(f"상가 데이터 정리 중 오류 발생: {row}")
        print(f"오류 내용: {e}")
        return None

def process_vacant_row(row):
    """Gongsil_final.csv 데이터 처리"""
    try:
        if pd.isna(row['위도']) or pd.isna(row['경도']):
            return None
            
        def safe_float(value):
            try:
                return float(value) if pd.notna(value) else None
            except Exception as e:
                print(f"숫자 변환 오류: {value}, 오류: {e}")
                return None
            
        lat = safe_float(row['위도'])
        lng = safe_float(row['경도'])
        
        if lat is None or lng is None:
            return None
            
        try:
            point = Point(float(lng), float(lat))
            coordinates = from_shape(point)
        except Exception as e:
            print(f"좌표 생성 중 오류: {e}")
            return None
            
        return {
            'latitude': lat,
            'longitude': lng,
            'coordinates': coordinates
        }
    except Exception as e:
        print(f"공실 데이터 행 처리 중 오류 발생: {row}")
        print(f"오류 내용: {e}")
        return None

def import_commercial_data(store_file: str = './data/final_data.csv', 
                         vacant_file: str = './data/Gongsil_final.csv',
                         batch_size: int = 100):
    """상가 및 공실 데이터 임포트"""
    db = None
    try:
        db = SessionLocal()
        
        # 기존 데이터 삭제
        print("\n기존 데이터 삭제 시작...")
        vacant_count = db.query(models.VacantListing).count()
        print(f"삭제할 공실 데이터 수: {vacant_count}")
        db.query(models.CommercialBuilding).delete()
        db.query(models.VacantListing).delete()
        db.commit()
        print("기존 데이터 삭제 완료")
        
        # 상가 데이터 임포트
        print("\n상가 데이터 파일 읽기 시작...")
        store_df = pd.read_csv(store_file, encoding='utf-8')
        print("상가 데이터 샘플:")
        print(store_df.head())
        
        stores = []
        for _, row in store_df.iterrows():
            try:
                data = process_store_row(row)
                if data:
                    store_obj = models.CommercialBuilding(**data)
                    stores.append(store_obj)
                    
                    if len(stores) >= batch_size:
                        db.bulk_save_objects(stores)
                        db.commit()
                        stores = []
            except Exception as e:
                print(f"상가 데이터 처리 중 오류: {e}")
                continue
        
        if stores:
            try:
                db.bulk_save_objects(stores)
                db.commit()
            except Exception as e:
                print(f"상가 데이터 최종 저장 중 오류: {e}")
                db.rollback()
        
        # 공실 데이터 임포트
        print("\n공실 데이터 파일 읽기 시작...")
        try:
            vacant_df = pd.read_csv(vacant_file, encoding='utf-8')
            print(f"공실 데이터 총 {len(vacant_df)}행 로드됨")
            print("공실 데이터 컬럼명:", vacant_df.columns.tolist())
            print("\n공실 데이터 첫 5행 샘플:")
            print(vacant_df[['위도', '경도']].head())
        except Exception as e:
            print(f"공실 데이터 파일 읽기 오류: {e}")
            return
        
        print("\n공실 데이터 처리 시작...")
        vacants = []
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for idx, row in vacant_df.iterrows():
            try:
                processed_count += 1
                data = process_vacant_row(row)
                
                if data:
                    vacant_obj = models.VacantListing(**data)
                    vacants.append(vacant_obj)
                    success_count += 1
                    
                    if len(vacants) >= batch_size:
                        try:
                            db.bulk_save_objects(vacants)
                            db.commit()
                            print(f"진행 상황: {processed_count}/{len(vacant_df)} 행 처리됨 "
                                  f"(성공: {success_count}, 실패: {error_count})")
                            vacants = []
                        except Exception as e:
                            print(f"공실 데이터 일괄 저장 중 오류: {e}")
                            db.rollback()
                            vacants = []
                else:
                    error_count += 1
                    
                if processed_count % 1000 == 0:
                    print(f"진행 상황: {processed_count}/{len(vacant_df)} 행 처리됨 "
                          f"(성공: {success_count}, 실패: {error_count})")
                    
            except Exception as e:
                error_count += 1
                print(f"공실 데이터 처리 중 오류 (행 {idx}): {e}")
                continue
        
        if vacants:
            try:
                db.bulk_save_objects(vacants)
                db.commit()
                success_count += len(vacants)
                print(f"\n마지막 {len(vacants)}개 공실 데이터 저장 완료")
            except Exception as e:
                error_count += len(vacants)
                print(f"공실 데이터 최종 저장 중 오류: {e}")
                db.rollback()
        
        print("\n공실 데이터 임포트 완료")
        print(f"총 처리된 행: {processed_count}")
        print(f"성공적으로 저장된 데이터: {success_count}")
        print(f"실패한 데이터: {error_count}")
        
        # 최종 데이터 확인
        final_count = db.query(models.VacantListing).count()
        print(f"\n데이터베이스의 최종 공실 데이터 수: {final_count}")
            
    except Exception as e:
        print(f"데이터 임포트 중 오류: {e}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    import_commercial_data()