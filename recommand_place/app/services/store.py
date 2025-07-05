"""가게 데이터 처리 서비스"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec
from app.core.config import CONFIG
from app.core.constants import CATEGORY_MAPPING
from app.models.schemas import CandidateStore

class StoreService:
    def __init__(self):
        self.store_db = None
        self.store_vectors = None
        self.w2v_model = None
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

    def get_candidate_stores(self, group_vector: np.ndarray, categories: List[str], keywords: List[str] = None) -> List[CandidateStore]:
        """주어진 그룹 벡터와 카테고리에 맞는 후보 가게들을 반환합니다."""
        candidate_stores_df = self.store_db[self.store_db['mapped_category'].isin(categories)].copy()
        
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

    def get_similar_categories(self, category: str, exclude_types: List[str] = None, exclude_categories: List[str] = None) -> List[str]:
        """W2V를 사용하여 주어진 카테고리와 유사한 카테고리들을 반환합니다."""
        if exclude_types is None:
            exclude_types = []
        if exclude_categories is None:
            exclude_categories = []
            
        available_categories = list(self.store_db['mapped_category'].unique())
        w2v_categories = [cat for cat in available_categories if cat in self.w2v_model.wv.index_to_key]
        
        if category not in self.w2v_model.wv.index_to_key:
            return [cat for cat in available_categories[:5] if cat not in exclude_categories]
        
        try:
            # 유사한 카테고리 찾기
            similar_items = self.w2v_model.wv.most_similar(category, topn=20)
            similar_categories = []
            
            for sim_cat, score in similar_items:
                if sim_cat in available_categories and sim_cat not in exclude_categories:
                    # 음식 타입 제외 로직
                    is_food = any(food_type in sim_cat for food_type in ['한식', '중식', '일식', '양식', '고기요리', '제과', '커피', '분식'])
                    
                    # 같은 타입(음식/비음식) 제외
                    if 'food' in exclude_types and is_food:
                        continue
                    if 'non_food' in exclude_types and not is_food:
                        continue
                        
                    similar_categories.append(sim_cat)
                    
                if len(similar_categories) >= 3:
                    break
            
            # 유사한 카테고리가 부족하면 기본 카테고리로 보충
            if len(similar_categories) < 3:
                backup_categories = [cat for cat in available_categories 
                                   if cat not in exclude_categories and cat not in similar_categories]
                similar_categories.extend(backup_categories[:3-len(similar_categories)])
                    
            return similar_categories if similar_categories else available_categories[:3]
            
        except Exception:
            return [cat for cat in available_categories[:5] if cat not in exclude_categories]

    def categorize_activity_type(self, category: str) -> str:
        """카테고리를 활동 타입으로 분류합니다."""
        food_categories = ['한식', '중식', '일식', '양식', '고기요리', '제과/제빵/떡/케익', '커피/음료', '분식', '패스트푸드']
        
        if any(food_type in category for food_type in food_categories):
            return 'food'
        else:
            return 'non_food'

    def get_time_slots(self, start_time: str, end_time: str, group_vector: np.ndarray = None) -> List[Dict[str, Any]]:
        """W2V 기반 연관성 추천으로 시간대별 슬롯을 생성합니다."""
        
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
                categories = [cat for cat in available_categories if cat not in used_categories][:3]
                if categories:
                    used_categories.extend(categories)
            
            slots.append({
                "name": f"시간대 {slot_id}",
                "time_range": f"{slot_start_str} ~ {slot_end_str}",
                "category": categories[:3] if categories else []
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
            "01": ["호텔"],
            "02": ["커피/음료", "제과/제빵/떡/케익"],
            "03": ["커피/음료", "제과/제빵/떡/케익"],
            "04": ["한식", "중식", "일식/수산물", "양식"],
            "05": ["커피/음료", "취미/오락"],
            "06": ["취미/오락", "커피/음료"],
            "07": ["한식", "고기요리", "양식"],
            "08": ["고기요리", "한식"],
            "09": ["고기요리"],
            "10": ["호텔"]
        }
        
        available_categories = list(self.store_db['mapped_category'].unique())
        default_cats = time_categories.get(slot_id, [])
        valid_categories = [cat for cat in default_cats if cat in available_categories]
        
        return valid_categories if valid_categories else available_categories[:3] 