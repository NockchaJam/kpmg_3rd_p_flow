import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# 데이터 로드
df = pd.read_csv('../data/output/collected_samples.csv')

# 1. 업종별 평균 매출 등급 분포 (Box Plot)
plt.figure(figsize=(12, 6))
sns.boxplot(x='industry_category', y='avg_sales_level', data=df)
plt.xticks(rotation=45)
plt.title('업종별 평균 매출 등급 분포')
plt.show()

# 2. 위도/경도 산점도 (매출 등급으로 색상 구분)
plt.figure(figsize=(10, 10))
scatter = plt.scatter(df['longitude'], df['latitude'], 
                     c=df['avg_sales_level'], cmap='viridis',
                     alpha=0.6)
plt.colorbar(scatter, label='평균 매출 등급')
plt.title('공실 위치와 매출 등급')
plt.xlabel('경도')
plt.ylabel('위도')
plt.show()

# 3. 인터랙티브 지도 시각화 (plotly)
fig = px.scatter_mapbox(df, 
                       lat='latitude', 
                       lon='longitude',
                       color='avg_sales_level',
                       hover_data=['industry_category', 'avg_sales_level'],
                       zoom=12)
fig.update_layout(mapbox_style='carto-positron')
fig.show()

# 4. 상관관계 히트맵
numeric_cols = ['num_of_company', 'num_of_large', 'num_of_bus_stop',
               'num_of_hospital', 'num_of_theather', 'num_of_camp',
               'num_of_school', 'nearest_subway_distance', 'num_of_subway',
               'num_of_gvn_office', 'parks_within_500m', 
               'parking_lots_within_500m', 'avg_sales_level']

plt.figure(figsize=(12, 10))
sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', center=0)
plt.title('변수간 상관관계')
plt.show()

# 5. 그룹별 매출 등급 분포
plt.figure(figsize=(15, 5))
sns.histplot(data=df, x='avg_sales_level', bins=30)
plt.title('평균 매출 등급 분포')
plt.show()