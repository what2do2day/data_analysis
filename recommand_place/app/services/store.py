"""가게 데이터 처리 서비스"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import CONFIG
from app.core.constants import CATEGORY_MAPPING
from app.models.schemas import CandidateStore

class StoreService:
    def __init__(self):
        self.store_db = None
        self.store_vectors = None
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

    def get_candidate_stores(self, group_vector: np.ndarray, categories: List[str]) -> List[CandidateStore]:
        """주어진 그룹 벡터와 카테고리에 맞는 후보 가게들을 반환합니다."""
        candidate_stores_df = self.store_db[self.store_db['mapped_category'].isin(categories)].copy()
        
        similarities = cosine_similarity(group_vector, candidate_stores_df[[f'vec_{i}' for i in range(1, 51)]].values).flatten()
        candidate_stores_df['similarity'] = similarities
        candidate_stores_df['keyword_score'] = 0.0  # TODO: 키워드 점수 로직
        candidate_stores_df['total_score'] = candidate_stores_df['similarity'] + candidate_stores_df['keyword_score']

        top_3_candidates = candidate_stores_df.sort_values(by='total_score', ascending=False).head(3)

        return [
            CandidateStore(
                store_name=row['store_name'],
                score=row['total_score'],
                similarity=row['similarity'],
                description=f"{row['standard_category']} 가게입니다."
            ) for _, row in top_3_candidates.iterrows()
        ]

    def get_time_slots(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """시간대별 슬롯을 생성합니다."""
        
        # 실제 데이터베이스의 카테고리 확인
        available_categories = list(self.store_db['mapped_category'].unique())
        
        # 시간을 분으로 변환
        def time_to_minutes(time_str):
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        
        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)
        
        # 기본 시간대 매핑 (2시간 단위)
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
        
        # 시간대별 기본 카테고리 (음식/비음식 혼합)
        time_categories = {
            "01": ["호텔"],  # 새벽
            "02": ["커피/음료", "제과/제빵/떡/케익"],  # 아침
            "03": ["커피/음료", "제과/제빵/떡/케익"],  # 오전
            "04": ["한식", "중식", "일식/수산물", "양식"],  # 점심
            "05": ["커피/음료", "취미/오락"],  # 오후
            "06": ["취미/오락", "커피/음료"],  # 늦은 오후
            "07": ["한식", "고기요리", "양식"],  # 저녁
            "08": ["고기요리", "한식"],  # 밤
            "09": ["고기요리"],  # 늦은 밤
            "10": ["호텔"]  # 자정
        }
        
        # 요청된 시간 범위와 겹치는 슬롯 찾기
        slots = []
        for slot_id, (slot_start_str, slot_end_str) in time_mapping.items():
            slot_start_minutes = time_to_minutes(slot_start_str)
            slot_end_minutes = time_to_minutes(slot_end_str)
            
            # 시간대가 요청된 범위와 겹치는지 확인
            if not (end_minutes <= slot_start_minutes or start_minutes >= slot_end_minutes):
                categories = time_categories.get(slot_id, [])
                # 실제 DB에 있는 카테고리만 필터링
                valid_categories = [cat for cat in categories if cat in available_categories]
                
                if valid_categories:
                    slots.append({
                        "name": f"시간대 {slot_id}",
                        "time_range": f"{slot_start_str} ~ {slot_end_str}",
                        "category": valid_categories
                    })
                else:
                    # 유효한 카테고리가 없으면 기본 카테고리 사용
                    slots.append({
                        "name": f"시간대 {slot_id}",
                        "time_range": f"{slot_start_str} ~ {slot_end_str}",
                        "category": available_categories[:3]  # 상위 3개만 사용
                    })
        
        return slots if slots else [{
            "name": "전체",
            "time_range": f"{start_time} ~ {end_time}",
            "category": available_categories[:5]  # 상위 5개만 사용
        }] 