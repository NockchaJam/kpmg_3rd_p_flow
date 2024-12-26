import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
from typing import Tuple, List, Dict
from pathlib import Path

class DataCollector:
    def __init__(self):
        """데이터 수집기 초기화"""
        self.vacant_stores = self._load_vacant_stores()
        self.commercial_buildings = self._load_commercial_buildings()
        # 공실 좌표로 BallTree 생성
        self.coords = self.vacant_stores[['latitude', 'longitude']].values
        self.tree = BallTree(np.deg2rad(self.coords), metric='haversine')
        
    def _load_vacant_stores(self) -> pd.DataFrame:
        """CSV에서 공실 데이터 로드"""
        try:
            df = pd.read_csv('./data/Vacant.common.csv')
            # 컬럼명 매핑
            df = df.rename(columns={
                '위도': 'latitude',
                '경도': 'longitude',
                'num_of_company(near 3km)': 'num_of_company',
                'num_of_large(near 1km)': 'num_of_large',
                'num_of_bus_stop(near 500m)': 'num_of_bus_stop',
                'num_of_hospital(near 1km)': 'num_of_hospital',
                'num_of_theather(near 1km)': 'num_of_theather',
                'num_of_camp(near 3km)': 'num_of_camp',
                'num_of_school(near 500m)': 'num_of_school',
                'nearest_subway_name': 'nearest_subway_name',
                'nearest_subway_distance': 'nearest_subway_distance',
                'num_of_subway(near 500m)': 'num_of_subway',
                'num_of_gvn_office(near 500m)': 'num_of_gvn_office',
                'parks_within_500m': 'parks_within_500m',
                'parking_lots_within_500m': 'parking_lots_within_500m'
            })
            # id 컬럼 추가
            df['id'] = range(len(df))
            print(f"로드된 공실 데이터: {len(df)}개")
            return df
            
        except Exception as e:
            print(f"공실 데이터 로드 실패: {e}")
            raise
            
    def _load_commercial_buildings(self) -> pd.DataFrame:
        """CSV에서 상가 데이터 로드"""
        try:
            df = pd.read_csv('./data/Store_common.csv')
            # 컬럼명 매핑
            df = df.rename(columns={
                '위도': 'latitude',
                '경도': 'longitude',
                '대분류업종': 'industry_category',
                '매출등급': 'sales_level'
            })
            # 필요한 컬럼만 선택
            df = df[['latitude', 'longitude', 'industry_category', 'sales_level']]
            return df
            
        except Exception as e:
            print(f"상가 데이터 로드 실패: {e}")
            raise

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """두 좌표 간의 거리를 km 단위로 계산"""
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c
            
    def _get_nearby_businesses_by_category(
        self, lat: float, lng: float, 
        category: str, radius_km: float = 0.5
    ) -> pd.DataFrame:
        """주어진 좌표 주변의 특정 업종 상가 데이터 조회"""
        nearby = self.commercial_buildings[
            self.commercial_buildings['industry_category'] == category
        ].copy()
        
        nearby['distance'] = nearby.apply(
            lambda row: self._haversine_distance(lat, lng, row['latitude'], row['longitude']),
            axis=1
        )
        return nearby[nearby['distance'] <= radius_km]

    def _calculate_avg_sales_level(self, nearby_businesses: pd.DataFrame) -> float:
        """평균 매출 등급 계산"""
        if len(nearby_businesses) == 0:
            return None
        return round(nearby_businesses['sales_level'].astype(float).mean(), 2)

    def find_nearest_stores(self, point: Tuple[float, float], radius_km: float = 0.5) -> pd.DataFrame:
        """주어진 좌표 근처의 가장 가까운 3개 공실 찾기 (중복 좌표 제외)"""
        radius_rad = radius_km / 6371.0
        point_rad = np.deg2rad(np.array([point]))
        
        # 반경 내의 모든 공실 찾기
        indices = self.tree.query_radius(point_rad, r=radius_rad)[0]
        if len(indices) < 3:
            return pd.DataFrame()
        
        # 모든 가까운 공실을 가져와서 DataFrame으로 변환
        distances, indices = self.tree.query(point_rad, k=len(indices))
        nearby_stores = self.vacant_stores.iloc[indices[0]].copy()
        nearby_stores['distance'] = distances[0]
        
        # 위도/경도 조합으로 중복 제거 (가장 가까운 것 유지)
        nearby_stores = nearby_stores.sort_values('distance')
        nearby_stores = nearby_stores.drop_duplicates(
            subset=['latitude', 'longitude'], 
            keep='first'
        )
        
        # 상위 3개만 선택
        if len(nearby_stores) < 3:
            return pd.DataFrame()
        
        return nearby_stores.head(3)

    def collect_data(self, n_samples: int = 5000, max_coords: int = 4500) -> pd.DataFrame:
        """데이터 수집 실행"""
        # 랜덤 좌표 로드 (최대 4500개까지만)
        random_coords = pd.read_csv('./data/random_coordinates.csv')
        random_coords = random_coords.head(max_coords)  # 처음 4500개만 사용
        
        if len(random_coords) < max_coords:
            print(f"경고: 요청된 {max_coords}개의 좌표 중 {len(random_coords)}개만 사용 가능")

        # 분석할 업종 목록 (제외할 업종 필터링)
        excluded_categories = ['기타', '운송업', '제조업']
        categories = self.commercial_buildings['industry_category'].unique()
        categories = [cat for cat in categories 
                     if pd.notna(cat) and cat not in excluded_categories]

        results = []
        group_id = 1
        
        for _, coord in random_coords.iterrows():
            point = (coord['위도'], coord['경도'])
            nearest_stores = self.find_nearest_stores(point)
            
            if len(nearest_stores) < 3:
                continue
            
            # 각 업종별로 시도
            for category in categories:
                if group_id > n_samples:  # 목표 그룹 수에 도달하면 종료
                    break
                
                group_results = []
                
                # 3개의 공실에 대해 같은 업종으로 계산
                for _, store in nearest_stores.iterrows():
                    # 공실 주변 상가 데이터 수집 (특정 업종만)
                    nearby_businesses = self._get_nearby_businesses_by_category(
                        store['latitude'], store['longitude'],
                        category
                    )
                    
                    # 평균 매출 등급 계산
                    avg_sales_level = self._calculate_avg_sales_level(nearby_businesses)
                    if avg_sales_level is None:
                        group_results = []  # 하나라도 실패하면 이 그룹은 무효
                        break
                    
                    store_data = {
                        'id': store['id'],
                        'group_id': group_id,
                        'latitude': store['latitude'],
                        'longitude': store['longitude'],
                        'num_of_company': store['num_of_company'],
                        'num_of_large': store['num_of_large'],
                        'num_of_bus_stop': store['num_of_bus_stop'],
                        'num_of_hospital': store['num_of_hospital'],
                        'num_of_theather': store['num_of_theather'],
                        'num_of_camp': store['num_of_camp'],
                        'num_of_school': store['num_of_school'],
                        'nearest_subway_name': store['nearest_subway_name'],
                        'nearest_subway_distance': store['nearest_subway_distance'],
                        'num_of_subway': store['num_of_subway'],
                        'num_of_gvn_office': store['num_of_gvn_office'],
                        'parks_within_500m': store['parks_within_500m'],
                        'parking_lots_within_500m': store['parking_lots_within_500m'],
                        'industry_category': category,
                        'avg_sales_level': avg_sales_level
                    }
                    
                    group_results.append(store_data)
                
                # 3개의 공실 모두 성공적으로 처리된 경우에만 결과에 추가
                if len(group_results) == 3:
                    results.extend(group_results)
                    group_id += 1
                    
                    if len(results) % 30 == 0:
                        print(f"수집 진행률: {group_id}/{n_samples} 그룹 "
                              f"({(group_id/n_samples*100):.1f}%)")
            
            if group_id > n_samples:  # 목표 그룹 수에 도달하면 종료
                break
        
        return pd.DataFrame(results)

def main():
    """메인 실행 함수"""
    try:
        collector = DataCollector()
        result_df = collector.collect_data(n_samples=5000, max_coords=4500)
        
        output_dir = Path('data/output')
        output_dir.mkdir(exist_ok=True, parents=True)
        output_path = output_dir / 'collected_samples.csv'
        result_df.to_csv(output_path, index=False)
        print(f"데이터 수집 완료! 결과가 {output_path}에 저장되었습니다.")
        
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 