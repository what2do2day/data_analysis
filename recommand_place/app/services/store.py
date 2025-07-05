"""가게 데이터 처리 서비스"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec
from geopy.distance import great_circle
from app.core.config import CONFIG
from app.core.constants import CATEGORY_MAPPING
from app.models.schemas import CandidateStore

class StoreService:
    def __init__(self):
        self.store_db = None
        self.store_vectors = None
        self.w2v_model = None
        self.first_location = None  # 첫 번째 추천 장소의 위치
        self.max_distance_km = 5.0  # 최대 거리 3km
        self.load_store_data()

    def load_store_data(self):
        """가게 데이터와 벡터를 로드합니다."""
        store_db = pd.read_csv(CONFIG["store_db_path"])
        store_db.dropna(subset=['latitude', 'longitude'], inplace=True)
        store_db['mapped_category'] = store_db['standard_category'].map(CATEGORY_MAPPING)
        store_db['mapped_category'] = store_db['mapped_category'].str.strip()
        store_db = store_db[~store_db['mapped_category'].isna()]
        
        vec_cols = [f'vec_{i}' for i in range(1, 51)]
        self.store_vectors = store_db[vec_cols].values
        self.store_db = store_db
        
        # W2V 모델 로드
        self.w2v_model = Word2Vec.load(CONFIG["w2v_model_path"])

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """두 지점 간의 거리를 km 단위로 계산합니다."""
        try:
            return great_circle((lat1, lon1), (lat2, lon2)).kilometers
        except:
            return float('inf')

    def filter_by_distance(self, candidate_stores_df: pd.DataFrame, center_lat: float, center_lon: float, max_distance: float = None) -> pd.DataFrame:
        """중심점에서 일정 거리 내의 가게들만 필터링합니다."""
        if max_distance is None:
            max_distance = self.max_distance_km
            
        # 거리 계산
        distances = candidate_stores_df.apply(
            lambda row: self.calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']),
            axis=1
        )
        
        # 거리 필터링
        within_distance = distances <= max_distance
        filtered_df = candidate_stores_df[within_distance].copy()
        filtered_df['distance_km'] = distances[within_distance]
        
        return filtered_df

    def get_candidate_stores(self, group_vector: np.ndarray, categories: List[str], keywords: List[str] = None, 
                           is_first_slot: bool = False, center_location: Optional[Tuple[float, float]] = None) -> List[CandidateStore]:
        """주어진 그룹 벡터와 카테고리에 맞는 후보 가게들을 반환합니다."""
        candidate_stores_df = self.store_db[self.store_db['mapped_category'].isin(categories)].copy()
        
        if len(candidate_stores_df) == 0:
            return []
        
        # 거리 기반 필터링 (첫 번째 슬롯이 아닌 경우)
        if not is_first_slot and center_location:
            center_lat, center_lon = center_location
            candidate_stores_df = self.filter_by_distance(candidate_stores_df, center_lat, center_lon)
            
            if len(candidate_stores_df) == 0:
                print(f"거리 필터링 후 후보가 없음. 거리 범위를 {self.max_distance_km * 2}km로 확장")
                # 거리 범위를 2배로 확장하여 재시도
                candidate_stores_df = self.store_db[self.store_db['mapped_category'].isin(categories)].copy()
                candidate_stores_df = self.filter_by_distance(candidate_stores_df, center_lat, center_lon, self.max_distance_km * 2)
        
        if len(candidate_stores_df) == 0:
            return []
        
        similarities = cosine_similarity(group_vector, candidate_stores_df[[f'vec_{i}' for i in range(1, 51)]].values).flatten()
        candidate_stores_df['similarity'] = similarities
        
        # 키워드 점수 계산
        keyword_scores = np.zeros(len(candidate_stores_df))
        if keywords:
            for keyword in keywords:
                keyword_match = candidate_stores_df['store_name'].str.contains(keyword, case=False, na=False) | \
                              candidate_stores_df['standard_category'].str.contains(keyword, case=False, na=False)
                keyword_scores += keyword_match.astype(float) * 0.2  # 키워드당 0.2점
        
        candidate_stores_df['keyword_score'] = keyword_scores
        
        # 거리 점수 추가 (가까울수록 높은 점수)
        distance_scores = np.zeros(len(candidate_stores_df))
        if not is_first_slot and 'distance_km' in candidate_stores_df.columns:
            # 거리 점수: 가까울수록 높은 점수 (최대 0.3점)
            max_distance_in_df = candidate_stores_df['distance_km'].max()
            if max_distance_in_df > 0:
                distance_scores = 0.3 * (1 - candidate_stores_df['distance_km'] / max_distance_in_df)
        
        candidate_stores_df['distance_score'] = distance_scores
        candidate_stores_df['total_score'] = candidate_stores_df['similarity'] + candidate_stores_df['keyword_score'] + candidate_stores_df['distance_score']

        top_3_candidates = candidate_stores_df.sort_values(by='total_score', ascending=False).head(3)

        candidates = []
        for _, row in top_3_candidates.iterrows():
            description = f"{row['standard_category']} 가게입니다."
            if not is_first_slot and 'distance_km' in row:
                description += f" (거리: {row['distance_km']:.1f}km)"
                
            candidates.append(CandidateStore(
                store_name=row['store_name'],
                score=row['total_score'],
                similarity=row['similarity'],
                description=description
            ))
        
        # 첫 번째 슬롯의 경우 첫 번째 후보의 위치를 저장
        if is_first_slot and candidates:
            first_candidate = top_3_candidates.iloc[0]
            self.first_location = (first_candidate['latitude'], first_candidate['longitude'])
            print(f"첫 번째 추천 장소: {first_candidate['store_name']} (위치: {self.first_location})")
        
        return candidates

    def get_similar_categories(self, category: str, exclude_types: List[str] = None, exclude_categories: List[str] = None) -> List[str]:
        """W2V를 사용하여 주어진 카테고리와 유사한 카테고리들을 반환합니다."""
        if exclude_types is None:
            exclude_types = []
        if exclude_categories is None:
            exclude_categories = []
            
        available_categories = list(self.store_db['mapped_category'].unique())
        w2v_categories = [cat for cat in available_categories if cat in self.w2v_model.wv.index_to_key]
        
        if category not in self.w2v_model.wv.index_to_key:
            return [cat for cat in available_categories[:8] if cat not in exclude_categories]
        
        try:
            # 유사한 카테고리 찾기
            similar_items = self.w2v_model.wv.most_similar(category, topn=30)
            similar_categories = []
            
            for sim_cat, score in similar_items:
                if sim_cat in available_categories and sim_cat not in exclude_categories:
                    # 활동 타입 확인
                    activity_type = self.categorize_activity_type(sim_cat)
                    
                    # 제외할 타입인지 확인
                    if activity_type in exclude_types:
                        continue
                        
                    similar_categories.append(sim_cat)
                    
                if len(similar_categories) >= 5:
                    break
            
            # 유사한 카테고리가 부족하면 다양한 타입의 카테고리로 보충
            if len(similar_categories) < 5:
                # 타입별로 카테고리 선택
                type_categories = {
                    'cultural': ['전시장', '테마파크', '관광,명소', '체험여행', '취미/오락'],
                    'shopping': ['복합쇼핑몰', '대형마트', '의류판매', '백화점', '시장'],
                    'nature': ['산봉우리', '계곡', '폭포', '수목원,식물원', '스포츠/레저'],
                    'historical': ['고궁,궁', '문화유적', '종교유적지', '생가,고택'],
                    'food': ['한식', '양식', '커피/음료', '제과/제빵/떡/케익']
                }
                
                # 현재 카테고리 타입을 제외한 다른 타입들에서 선택
                current_type = self.categorize_activity_type(category)
                
                for type_name, type_cats in type_categories.items():
                    if type_name not in exclude_types and type_name != current_type:
                        for cat in type_cats:
                            if (cat in available_categories and 
                                cat not in exclude_categories and 
                                cat not in similar_categories):
                                similar_categories.append(cat)
                                if len(similar_categories) >= 5:
                                    break
                    if len(similar_categories) >= 5:
                        break
                    
            return similar_categories if similar_categories else available_categories[:5]
            
        except Exception:
            return [cat for cat in available_categories[:8] if cat not in exclude_categories]

    def categorize_activity_type(self, category: str) -> str:
        """카테고리를 활동 타입으로 분류합니다."""
        food_categories = [
            '한식', '중식', '일식/수산물', '양식', '고기요리', '제과/제빵/떡/케익', 
            '커피/음료', '분식', '패스트푸드', '닭/오리요리', '별식/퓨전요리',
            '부페', '유흥주점', '철판요리', '냉면', '칼국수', '샤브샤브', '양꼬치'
        ]
        
        cultural_categories = [
            '전시장', '박물관', '미술관', '공연장,연극극장', '테마파크', '관광,명소',
            '체험여행', '취미/오락', '스포츠/레저', '서점', '음반,레코드샵'
        ]
        
        shopping_categories = [
            '복합쇼핑몰', '대형마트', '의류판매', '가구판매', '주방용품', '백화점',
            '시장', '디자인문구', '반려동물', '미용'
        ]
        
        nature_categories = [
            '산봉우리', '계곡', '폭포', '바위', '저수지', '수목원,식물원', 
            '케이블카', '숲', '연못'
        ]
        
        historical_categories = [
            '고궁,궁', '문화유적', '종교유적지', '생가,고택', '사당,제단',
            '향교,서당', '릉,묘,총', '불상,석불', '산성,성곽', '봉수대'
        ]
        
        if any(food_type in category for food_type in food_categories):
            return 'food'
        elif any(cultural_type in category for cultural_type in cultural_categories):
            return 'cultural'
        elif any(shopping_type in category for shopping_type in shopping_categories):
            return 'shopping'
        elif any(nature_type in category for nature_type in nature_categories):
            return 'nature'
        elif any(historical_type in category for historical_type in historical_categories):
            return 'historical'
        else:
            return 'other'

    def get_time_slots(self, start_time: str, end_time: str, group_vector: np.ndarray = None) -> List[Dict[str, Any]]:
        """W2V 기반 연관성 추천으로 시간대별 슬롯을 생성합니다."""
        
        # 첫 번째 호출시 위치 초기화
        self.first_location = None
        
        # 시간을 분으로 변환
        def time_to_minutes(time_str):
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        
        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)
        
        # 기본 시간대 매핑
        time_mapping = {
            "01": ("00:00", "06:59"),
            "02": ("07:00", "08:59"),
            "03": ("09:00", "10:59"),
            "04": ("11:00", "12:59"),
            "05": ("13:00", "14:59"),
            "06": ("15:00", "16:59"),
            "07": ("17:00", "18:59"),
            "08": ("19:00", "20:59"),
            "09": ("21:00", "22:59"),
            "10": ("23:00", "23:59")
        }
        
        # 요청된 시간 범위와 겹치는 슬롯 찾기
        matching_slots = []
        for slot_id, (slot_start_str, slot_end_str) in time_mapping.items():
            slot_start_minutes = time_to_minutes(slot_start_str)
            slot_end_minutes = time_to_minutes(slot_end_str)
            
            if not (end_minutes <= slot_start_minutes or start_minutes >= slot_end_minutes):
                matching_slots.append((slot_id, slot_start_str, slot_end_str))
        
        if not matching_slots:
            return [{
                "name": "전체",
                "time_range": f"{start_time} ~ {end_time}",
                "category": list(self.store_db['mapped_category'].unique())[:5]
            }]
        
        slots = []
        previous_category = None
        previous_type = None
        used_categories = []  # 이미 사용된 카테고리 추적
        
        for i, (slot_id, slot_start_str, slot_end_str) in enumerate(matching_slots):
            if i == 0:
                # 첫 번째 슬롯: 사용자 취향에 가장 맞는 카테고리 선택
                if group_vector is not None:
                    categories = self.get_best_category_for_user(group_vector, slot_id)
                else:
                    categories = self.get_default_categories_for_time(slot_id)
                    
                previous_category = categories[0] if categories else None
                previous_type = self.categorize_activity_type(previous_category) if previous_category else None
                used_categories.extend(categories)
                
            else:
                # 이후 슬롯: 이전 활동과 연관성 있으면서도 다른 타입의 활동
                if previous_category:
                    # 이전 타입과 다른 타입을 우선적으로 선택
                    exclude_types = [previous_type] if previous_type else []
                    categories = self.get_similar_categories(previous_category, exclude_types, used_categories)
                    
                    # 만약 유사한 카테고리가 없으면 기본 카테고리 사용
                    if not categories:
                        categories = self.get_default_categories_for_time(slot_id)
                        categories = [cat for cat in categories if cat not in used_categories]
                    
                    if categories:
                        previous_category = categories[0]
                        previous_type = self.categorize_activity_type(previous_category)
                        used_categories.extend(categories)
                else:
                    categories = self.get_default_categories_for_time(slot_id)
                    categories = [cat for cat in categories if cat not in used_categories]
                    if categories:
                        previous_category = categories[0]
                        previous_type = self.categorize_activity_type(previous_category)
                        used_categories.extend(categories)
            
            # 카테고리가 없으면 기본값 사용
            if not categories:
                available_categories = list(self.store_db['mapped_category'].unique())
                categories = [cat for cat in available_categories if cat not in used_categories][:5]
                if categories:
                    used_categories.extend(categories)
            
            slots.append({
                "name": f"시간대 {slot_id}",
                "time_range": f"{slot_start_str} ~ {slot_end_str}",
                "category": categories[:5] if categories else [],
                "is_first_slot": i == 0  # 첫 번째 슬롯 여부 추가
            })
        
        return slots

    def get_best_category_for_user(self, group_vector: np.ndarray, slot_id: str) -> List[str]:
        """사용자 취향 벡터를 기반으로 최적의 카테고리를 선택합니다."""
        available_categories = list(self.store_db['mapped_category'].unique())
        w2v_categories = [cat for cat in available_categories if cat in self.w2v_model.wv.index_to_key]
        
        if not w2v_categories:
            return self.get_default_categories_for_time(slot_id)
        
        try:
            # 각 카테고리와 사용자 취향 벡터의 유사도 계산
            scores = {}
            for cat in w2v_categories:
                try:
                    cat_vector = self.w2v_model.wv[cat].reshape(1, -1)
                    similarity = cosine_similarity(group_vector, cat_vector)[0, 0]
                    scores[cat] = similarity
                except:
                    continue
            
            # 상위 3개 카테고리 선택
            top_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            return [cat for cat, score in top_categories]
            
        except Exception:
            return self.get_default_categories_for_time(slot_id)

    def get_default_categories_for_time(self, slot_id: str) -> List[str]:
        """시간대별 기본 카테고리를 반환합니다."""
        time_categories = {
            "01": ["호텔", "펜션"],  # 새벽
            "02": ["커피/음료", "제과/제빵/떡/케익", "호텔"],  # 아침
            "03": ["커피/음료", "제과/제빵/떡/케익", "전시장", "박물관", "미술관"],  # 오전
            "04": ["한식", "중식", "일식/수산물", "양식", "대형마트", "복합쇼핑몰"],  # 점심
            "05": ["커피/음료", "취미/오락", "테마파크", "전시장", "관광,명소", "체험여행"],  # 오후
            "06": ["취미/오락", "커피/음료", "테마파크", "전시장", "관광,명소", "복합쇼핑몰", "의류판매"],  # 늦은 오후
            "07": ["한식", "고기요리", "양식", "공연장,연극극장", "관광,명소"],  # 저녁
            "08": ["고기요리", "한식", "양식", "유흥주점", "공연장,연극극장"],  # 밤
            "09": ["고기요리", "유흥주점", "취미/오락"],  # 늦은 밤
            "10": ["호텔", "펜션"]  # 자정
        }
        
        available_categories = list(self.store_db['mapped_category'].unique())
        default_cats = time_categories.get(slot_id, [])
        valid_categories = [cat for cat in default_cats if cat in available_categories]
        
        # 만약 시간대별 카테고리가 부족하면 모든 카테고리에서 추가
        if len(valid_categories) < 5:
            # 다양한 타입의 카테고리를 추가
            additional_categories = [
                '스포츠/레저', '서점', '음반,레코드샵', '디자인문구', '주방용품',
                '반려동물', '미용', '가구판매', '백화점', '시장',
                '생가,고택', '테마거리', '먹자골목', '고궁,궁', '문화유적',
                '산봉우리', '계곡', '케이블카', '종교유적지', '수목원,식물원',
                '체험여행', '폭포', '바위', '저수지'
            ]
            
            for cat in additional_categories:
                if cat in available_categories and cat not in valid_categories:
                    valid_categories.append(cat)
                    if len(valid_categories) >= 8:  # 최대 8개까지
                        break
        
        return valid_categories if valid_categories else available_categories[:8] 