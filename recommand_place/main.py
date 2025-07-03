# --- 1. 라이브러리 임포트 ---
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging
import openai
from geopy.distance import great_circle
import datetime
import json
from dotenv import load_dotenv
from gensim.models import Word2Vec
load_dotenv()

# --- 2. 프로젝트 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = {
    "store_db_path": os.path.join(BASE_DIR, "stores_with_preferences_vec.csv"),
    "w2v_model_path": os.path.join(BASE_DIR, "w2v_activity_model.model"),
}
assets = {}  # 전역 변수로 데이터 저장

CATEGORY_MAPPING = {
    # --- 🍚 한식 ---
    '한식': '한식',
    '국밥': '한식',
    '곰탕': '한식',
    '설렁탕': '한식',
    '찌개,전골': '한식',
    '해장국': '한식',
    '감자탕': '한식',
    '삼계탕': '한식',
    '한정식': '한식',
    '쌈밥': '한식',
    '두부전문점': '한식',
    '기사식당': '한식',
    # --- 🥩 고기요리 ---
    '육류,고기': '고기요리',
    '고기요리': '고기요리',
    '삼겹살': '고기요리',
    '갈비': '고기요리',
    '불고기,두루치기': '고기요리',
    '족발,보쌈': '고기요리',
    '곱창,막창': '고기요리',
    '고기뷔페': '부페',
    '사철탕,영양탕': '고기요리',
    # --- 🍗 닭/오리요리 ---
    '닭요리': '닭/오리요리',
    '닭/오리요리': '닭/오리요리',
    '닭강정': '닭/오리요리',
    '치킨': '닭/오리요리',
    '오리': '닭/오리요리',
    # --- 🍣 중식/일식/양식/기타 국가 ---
    '중식': '중식',
    '중국요리': '중식',
    '일식': '일식/수산물',
    '일식집': '일식/수산물',
    '일식/수산물': '일식/수산물',
    '초밥,롤': '일식/수산물',
    '참치회': '일식/수산물',
    '회': '일식/수산물',
    '해물,생선': '일식/수산물',
    '돈까스,우동': '일식/수산물',
    '일본식라면': '일식/수산물',
    '퓨전일식': '일식/수산물',
    '조개': '일식/수산물',
    '게,대게': '일식/수산물',
    '장어': '일식/수산물',
    '아구': '일식/수산물',
    '추어': '한식',
    '양식': '양식',
    '이탈리안': '양식',
    '프랑스음식': '양식',
    '스테이크,립': '양식',
    '패밀리레스토랑': '양식',
    '베트남음식': '별식/퓨전요리',
    '태국음식': '별식/퓨전요리',
    '동남아음식': '별식/퓨전요리',
    '멕시칸,브라질': '별식/퓨전요_리',
    '스페인음식': '별식/퓨전요리',
    '인도음식': '별식/퓨전요리',
    '아시아음식': '별식/퓨전요리',
    '퓨전요리': '별식/퓨전요리',
    '별식/퓨전요리': '별식/퓨전요리',
    '퓨전한식': '별식/퓨전요리',
    # --- ☕ 카페/디저트/주점 ---
    '카페': '커피/음료',
    '커피/음료': '커피/음료',
    '커피전문점': '커피/음료',
    '디저트카페': '커피/음료',
    '북카페': '취미/오락',
    '갤러리카페': '전시장',
    '키즈카페': '취미/오락',
    '테마카페': '커피/음료',
    '다방': '커피/음료',
    '전통찻집': '커피/음료',
    '음악감상실': '취미/오락',
    '제과,베이커리': '제과/제빵/떡/케익',
    '제과/제빵/떡/케익': '제과/제빵/떡/케익',
    '도넛': '제과/제빵/떡/케익',
    '아이스크림': '제과/제빵/떡/케익',
    '아이스크림판매': '제과/제빵/떡/케익',
    '유흥주점': '유흥주점',
    '일본식주점': '유흥주점',
    '실내포장마차': '유흥주점',
    '호프,요리주점': '유흥주점',
    '술집': '유흥주점',
    '칵테일바': '유흥주점',
    # --- 🍕 분식/패스트푸드 ---
    '분식': '분식',
    '떡볶이': '분식',
    '순대': '분식',
    '국수': '한식',
    '수제비': '한식',
    '패스트푸드': '패스트푸드',
    '햄버거': '패스트푸드',
    '피자': '패스트푸드',
    '샌드위치': '패스트푸드',
    '도시락': '패스트푸드',
    '간식': '분식',
    # --- 뷔페 ---
    '부페': '부페',
    '뷔페': '부페',
    '해산물뷔페': '부페',
    '한식뷔페': '부페',
    # --- 🛍️ 쇼핑 및 판매 ---
    '의류판매': '의류판매',
    '여성의류': '의류판매',
    '의류수선': '의류판매',
    '의류할인매장': '의류판매',
    '상설할인매장': '의류판매',
    '대형마트': '대형마트',
    '대형슈퍼': '대형마트',
    '슈퍼마켓': '대형마트',
    '면세점': '의류판매',
    '복합쇼핑몰': '복합쇼핑몰',
    '식품판매': '대형마트',
    '가구판매': '가구판매',
    '가구거리': '가구판매',
    '주방용품': '주방용품',
    '인테리어장식판매': '인테리어장식판매',
    '커튼,블라인드판매': '인테리어장식판매',
    '꽃집,꽃배달': '꽃집,꽃배달',
    '음반,레코드샵': '음반,레코드샵',
    '디자인문구': '디자인문구',
    '문구,사무용품': '문구,사무용품',
    # --- 📚 서점 ---
    '서점': '서점',
    '중고서점': '서점',
    '독립서점': '서점',
    # --- ⚽ 여가/오락/관광 ---
    '경기관람': '경기관람',
    '스포츠/레저': '스포츠/레저',
    '일반스포츠': '스포츠/레저',
    '전시장': '전시장',
    '전시관': '전시장',
    '미술관': '전시장',
    '박물관': '전시장',
    '과학관': '전시장',
    '기념관': '전시장',
    '공연장,연극극장': '공연장,연극극장',
    '테마파크': '테마파크',
    '테마파크시설': '테마파크',
    '아쿠아리움': '테마파크',
    '워터테마파크': '테마파크',
    '동물원': '테마파크',
    '실내동물원': '테마파크',
    '놀이시설': '테마파크',
    '취미/오락': '취미/오락',
    '미술,공예': '취미/오락',
    '음악': '취미/오락',
    '사진관,포토스튜디오': '취미/오락',
    '미술학원': '취미/오락',
    '녹음실': '취미/오락',
    'PC방': '취미/오락',
    '노래방': '취미/오락',
    '공원': '스포츠/레저',
    '도시근린공원': '스포츠/레저',
    '공원시설물': '스포츠/레저',
    '놀이터': '스포츠/레저',
    '호수': '관광,명소',
    '강': '관광,명소',
    '하천': '관광,명소',
    '산': '스포츠/레저',
    '등산로': '스포츠/레저',
    '둘레길': '스포츠/레저',
    '야영,캠핑장': '스포츠/레저',
    '글램핑장': '스포츠/레저',
    '자연휴양림': '스포츠/레저',
    '자전거여행': '스포츠/레저',
    '도보여행': '스포츠/레저',
    '체험여행': '스포츠/레저',
    '정보화,체험마을': '체험여행',
    '드라이브코스': '관광,명소',
    '촬영지': '관광,명소',
    '관광,명소': '관광,명소',
    # --- 🐶 반려동물 ---
    '반려동물': '반려동물',
    '반려동물용품': '반려동물',
    '반려동물미용': '반려동물',
    '반려동물분양': '반려동물',
    '반려견놀이터': '반려동물',
    # --- 🏨 숙박 ---
    '호텔': '호텔',
    '여관,모텔': '호텔',
    '게스트하우스': '호텔',
    '펜션': '펜션',
    # --- 💅 미용 ---
    '미용': '미용',
    '미용실': '미용',
    '네일샵': '미용',
    '체형관리': '미용',
    # --- 기타 분류가 애매하거나 불필요한 카테고리 ---
    '지명': None,
    'nan': None,
    '종합건설사': None,
    '빌라,주택': None,
    '화학': None,
    '농장,목장': None,
    '보관,저장': None,
    '원예업': None,
    '출판사': None,
    '어린이집': None,
    '냉난방기제조': None,
    '직업소개,인력파견': None,
    '산업용품': None,
    '비철금속처리': None,
}

# --- 3. Pydantic 입출력 모델 정의 ---
class UserPreference(BaseModel):
    gender: str
    age: int
    preferences: Dict[str, float] = Field(..., description="50차원의 취향 벡터")
class PlannerRequest(BaseModel):
    user1: UserPreference
    user2: UserPreference
    date: str
    weather: str
    startTime: str
    endTime: str
    keywords: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "user1": {
                    "gender": "M",
                    "age": 26,
                    "preferences": {f"vec_{i}": round(0.1 * ((i-1)%10+1), 1) for i in range(1, 51)}
                },
                "user2": {
                    "gender": "F",
                    "age": 26,
                    "preferences": {f"vec_{i}": round(0.1 * ((i-1)%10+1), 1) for i in range(1, 51)}
                },
                "date": "2025-07-03",
                "weather": "맑음",
                "startTime": "13:00",
                "endTime": "19:00",
                "keywords": ["기념일", "로맨틱"]
            }
        }
class CandidateStore(BaseModel):
    store_name: str
    score: float
    similarity: float
    description: str

class LLMRecommendation(BaseModel):
    selected: str
    reason: str

class TimeSlotResult(BaseModel):
    slot: str
    top_candidates: List[CandidateStore]
    llm_recommendation: LLMRecommendation

class PlannerResponse(BaseModel):
    time_slots: List[TimeSlotResult]

# --- 4. FastAPI 앱 설정 및 자산 로드 ---
app = FastAPI(title="AI Planner API v2 (Vector-based)")

@app.on_event("startup")
def load_assets():
    logger.info("--- 가게 DB 및 취향 벡터 로딩 시작 ---")
    try:
        store_db = pd.read_csv(CONFIG["store_db_path"])
        store_db.dropna(subset=['latitude', 'longitude'], inplace=True)
        store_db['mapped_category'] = store_db['standard_category'].map(CATEGORY_MAPPING)
        store_db['mapped_category'] = store_db['mapped_category'].str.strip()
        store_db = store_db[~store_db['mapped_category'].isna()]
        print('DB mapped_category 목록:', store_db['mapped_category'].unique())
        print('DB 전체 데이터 개수:', len(store_db))
        vec_cols = [f'vec_{i}' for i in range(1, 51)]
        assets['store_vectors'] = store_db[vec_cols].values
        assets['store_db'] = store_db
        assets['w2v_model'] = Word2Vec.load(CONFIG['w2v_model_path'])
        assets['llm_client'] = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("--- 자산 로딩 완료! ---")
    except Exception as e:
        logger.error(f"자산 로딩 오류: {e}")
        raise

# --- 5. 헬퍼 함수 정의 ---
def create_group_vector(request: PlannerRequest) -> np.ndarray:
    vec1 = np.array(list(request.user1.preferences.values()))
    vec2 = np.array(list(request.user2.preferences.values()))
    return np.mean([vec1, vec2], axis=0).reshape(1, -1)

def get_w2v_slots(group_vector: np.ndarray) -> List[Dict]:
    """w2v 모델 기반으로 가장 적절한 활동 슬롯(카테고리) 추천"""
    w2v_model = assets['w2v_model']
    index = assets['store_db']['standard_category'].dropna().unique()
    index = list(set(index).intersection(set(w2v_model.wv.index_to_key)))
    scores = {cat: cosine_similarity(group_vector, [w2v_model.wv[cat]])[0, 0] for cat in index}
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
    return [{"name": cat, "time_range": f"{time_start} ~ {time_end}", "category": [cat]} for (cat, _), (_, time_start, time_end) in zip(top_cats, time_mapping)]

def call_llm(candidates: List[Dict], context: Dict) -> LLMRecommendation:
    client = assets['llm_client']
    llm_input_info = ""
    for cand in candidates:
        llm_input_info += f"- 가게명: {cand['store_name']}, 총점: {cand['score']:.2f}, 유사도: {cand['similarity']:.2f}, 설명: {cand['description']}\n"

    prompt = f"""[모임 정보]
- 목적: {context['meeting_purpose']}
- 날씨: {context['weather']}

[시스템 추천 후보]
{llm_input_info}
[너의 임무]
위 후보 중에서 가장 적합한 가게 하나만 선택하고, 그 이유를 JSON 형식으로 답변해줘.
{{ "selected": "가게이름", "reason": "선택한 이유" }}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.choices[0].message.content)
        return LLMRecommendation(**result)
    except Exception as e:
        logger.error(f"LLM 호출 실패: {e}")
        return LLMRecommendation(selected="선택 실패", reason=str(e))

def get_time_slots(start_time_str: str, end_time_str: str) -> List[Dict]:
    return [
        {
            "name": "전체",
            "time_range": f"{start_time_str} ~ {end_time_str}",
            "category": list(assets['store_db']['mapped_category'].unique())
        }
    ]

# --- 6. 메인 API 엔드포인트 ---
@app.post("/generate-plan-vector", response_model=PlannerResponse)
def generate_plan(request: PlannerRequest):
    if not assets:
        raise HTTPException(status_code=503, detail="서버 준비 중")

    group_vector = create_group_vector(request)
    time_slots = get_time_slots(request.startTime, request.endTime)

    final_plan_slots = []
    for slot in time_slots:
        print('슬롯 카테고리:', slot['category'])
        print('DB 카테고리:', assets['store_db']['mapped_category'].unique())
        candidate_stores_df = assets['store_db'][assets['store_db']['mapped_category'].isin(slot['category'])].copy()
        print('후보 개수:', len(candidate_stores_df))

        similarities = cosine_similarity(group_vector, candidate_stores_df[[f'vec_{i}' for i in range(1, 51)]].values).flatten()
        candidate_stores_df['similarity'] = similarities
        candidate_stores_df['keyword_score'] = 0.0  # TODO: 키워드 점수 로직
        candidate_stores_df['total_score'] = candidate_stores_df['similarity'] + candidate_stores_df['keyword_score']

        top_3_candidates = candidate_stores_df.sort_values(by='total_score', ascending=False).head(3)

        top_candidates_list = [
            CandidateStore(
                store_name=row['store_name'],
                score=row['total_score'],
                similarity=row['similarity'],
                description=f"{row['standard_category']} 가게입니다."
            ) for _, row in top_3_candidates.iterrows()
        ]

        llm_context = {"meeting_purpose": request.keywords[0], "weather": request.weather}
        llm_recommendation = call_llm(top_3_candidates.to_dict('records'), llm_context)

        final_plan_slots.append(
            TimeSlotResult(
                slot=slot['time_range'],
                top_candidates=top_candidates_list,
                llm_recommendation=llm_recommendation
            )
        )

    return PlannerResponse(time_slots=final_plan_slots)
