"""벡터 연산 서비스"""

import numpy as np
from gensim.models import Word2Vec
from app.core.config import CONFIG
from app.models.schemas import PlannerRequest

class VectorService:
    def __init__(self):
        self.w2v_model = Word2Vec.load(CONFIG["w2v_model_path"])

    def create_group_vector(self, request: PlannerRequest) -> np.ndarray:
        """두 사용자의 취향 벡터를 평균내어 그룹 벡터를 생성합니다."""
        vec1 = np.array(list(request.user1.preferences.values()))
        vec2 = np.array(list(request.user2.preferences.values()))
        return np.mean([vec1, vec2], axis=0).reshape(1, -1)

    def get_w2v_slots(self, group_vector: np.ndarray) -> list:
        """Word2Vec 모델을 사용하여 적절한 활동 슬롯을 추천합니다."""
        index = self.store_db['standard_category'].dropna().unique()
        index = list(set(index).intersection(set(self.w2v_model.wv.index_to_key)))
        scores = {cat: cosine_similarity(group_vector, [self.w2v_model.wv[cat]])[0, 0] for cat in index}
        top_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

        time_mapping = [
            ("01", "00:00", "06:59"),
            ("02", "07:00", "08:59"),
            ("03", "09:00", "10:59"),
            ("04", "11:00", "12:59"),
            ("05", "13:00", "14:59"),
            ("06", "15:00", "16:59"),
            ("07", "17:00", "18:59"),
            ("08", "19:00", "20:59"),
            ("09", "21:00", "22:59"),
            ("10", "23:00", "23:59")
        ]
        
        return [
            {
                "name": cat,
                "time_range": f"{time_start} ~ {time_end}",
                "category": [cat]
            } for (cat, _), (_, time_start, time_end) in zip(top_cats, time_mapping)
        ] 