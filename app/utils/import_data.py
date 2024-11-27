import pandas as pd
from sqlalchemy.orm import Session
from .. import models
from ..database import SessionLocal, engine

def process_row(row_str: str):
    """쉼표로 구분된 데이터를 처리"""
    try:
        parts = row_str.strip().split(',')
        if len(parts) >= 6:  # 최소 6개의 필드가 있는지 확인
            lat, lon, addr, name, desc, ind = parts[:6]  # 처음 6개 필드만 사용
            
            # 빈 문자열이나 'None' 값 처리
            if lat and lon and lat.lower() != 'none' and lon.lower() != 'none':
                return {
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'address': addr.strip(),
                    'name': name.strip(),
                    'description': desc.strip(),
                    'industry': ind.strip()
                }
    except Exception as e:
        print(f"행 처리 중 오류 발생: {row_str}")
        print(f"오류 내용: {e}")
    return None

def import_location_data(file_path: str = './data/location_test_data_3-4.csv', batch_size: int = 100):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            locations = []
            db = SessionLocal()
            count = 0
            
            try:
                for line in file:
                    if not line.strip():  # 빈 줄 건너뛰기
                        continue
                    
                    data = process_row(line)
                    if data:  # 유효한 데이터만 처리
                        location = models.Location(**data)
                        locations.append(location)
                        count += 1
                    
                    # 배치 크기에 도달하면 DB에 저장
                    if len(locations) >= batch_size:
                        db.bulk_save_objects(locations)
                        db.commit()
                        print(f"{count}개 레코드 처리 완료")
                        locations = []
                
                # 남은 데이터 처리
                if locations:
                    db.bulk_save_objects(locations)
                    db.commit()
                    print(f"마지막 {len(locations)}개 레코드 처리 완료")
                
                print(f"총 {count}개의 데이터 임포트가 완료되었습니다!")
                
            except Exception as e:
                print(f"데이터 삽입 중 오류 발생: {e}")
                db.rollback()
            
            finally:
                db.close()
                
    except Exception as e:
        print(f"파일 읽기 오류: {e}")

def clear_locations():
    db = SessionLocal()
    try:
        db.query(models.Location).delete()
        db.commit()
        print("기존 데이터가 모두 삭제되었습니다.")
    except Exception as e:
        print(f"데이터 삭제 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

def check_file_format(file_path: str):
    """파일 형식을 확인하기 위해 첫 몇 줄을 출력"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file):
                if i < 3:  # 처음 3줄만 출력
                    print(f"Line {i+1}: {repr(line)}")  # repr()를 사용하여 숨겨진 문자도 표시
    except Exception as e:
        print(f"파일 읽기 오류: {e}")

# 데이터 임포트 전에 기존 데이터 삭제가 필요하다면:
if __name__ == "__main__":
    clear_locations()  # 기존 데이터 삭제
    import_location_data()  # 새 데이터 임포트
    check_file_format('./data/location_test_data_3-2.csv')