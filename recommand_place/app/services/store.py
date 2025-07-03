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
        return [{
            "name": "전체",
            "time_range": f"{start_time} ~ {end_time}",
            "category": list(self.store_db['mapped_category'].unique())
        }] 