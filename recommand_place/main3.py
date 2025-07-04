# 파일명: main.py (단독 실행 최종판)

# --- 1. 라이브러리 임포트 ---
from transformers import BitsAndBytesConfig
import pandas as pd
import numpy as np
import joblib
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import os
import datetime
import pprint
from geopy.distance import great_circle
from category_mapper import CATEGORY_MAPPING # category_mapper.py에서 매핑 딕셔너리 불러오기
import logging
import openai
# --- 2. 프로젝트 설정 및 자산 로드 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = {
    "persona_vectors_path": os.path.join(BASE_DIR, "persona_vectors.npy"),
    "item_vectors_path": os.path.join(BASE_DIR, "item_vectors.npy"),
    "svd_persona_index_path": os.path.join(BASE_DIR, "svd_persona_index.pkl"),
    "svd_item_index_path": os.path.join(BASE_DIR, "svd_item_index.pkl"),
    "w2v_model_path": os.path.join(BASE_DIR, "w2v_activity_model.model"),
    "store_db_path": os.path.join(BASE_DIR, "final_store_db.csv"),}

def load_all_assets():
    """프로젝트에 필요한 모든 자산을 로드하는 함수"""
    logger.info("--- 모든 자산 로딩 시작 ---")
    assets = {}
    try:
        # SVD/W2V 모델 및 벡터 로드
        persona_index = joblib.load(CONFIG["svd_persona_index_path"])
        item_index = joblib.load(CONFIG["svd_item_index_path"])
        persona_vectors = np.load(CONFIG["persona_vectors_path"])
        item_vectors = np.load(CONFIG["item_vectors_path"])
        assets['persona_vectors_df'] = pd.DataFrame(persona_vectors, index=persona_index)
        assets['item_vectors_df'] = pd.DataFrame(item_vectors, index=item_index)
        assets['w2v_model'] = Word2Vec.load(CONFIG["w2v_model_path"])
        
        # 가게 DB 로드 및 전처리
        store_db = pd.read_csv(CONFIG["store_db_path"])
        store_db.dropna(subset=['latitude', 'longitude'], inplace=True)
        # 'category'는 가게 DB의 원본 카테고리 컬럼명입니다. 실제 파일에 맞게 수정해주세요.
        store_db['standard_category'] = store_db['standard_category'].map(CATEGORY_MAPPING)
        for col in ['tag', 'positive', 'negative']:
            if col in store_db.columns:
                store_db[col] = store_db[col].astype(str).apply(lambda x: x.strip("[]").replace("'", "").split(', '))
        assets['store_db'] = store_db
            
 
        logger.info("--- 모든 자산 로딩 완료! ---")
        return assets
    except Exception as e:
        logger.error(f"자산 로딩 중 심각한 오류 발생: {e}")
        raise

# --- 3. 핵심 추천 로직 함수 ---
def get_final_recommendation(request, assets, openai_client):
    """
    [최종 완성판]
    사용자 요청을 받아 SVD/W2V로 활동을 추천하고,
    DB에서 실제 가게 후보를 필터링/선정하여 OpenAI API로 최종 답변을 받는 함수
    """
    # --- 1. 그룹 페르소나 벡터 생성 ---
    persona_vectors_df = assets['persona_vectors_df']
    group_personas = [(p['age'], p['sex']) for p in request['personas']]
    group_vector = np.mean([persona_vectors_df.loc[p].values for p in group_personas if p in persona_vectors_df.index], axis=0).reshape(1, -1)
    logger.info("✅ 그룹 페르소나 벡터 계산 완료.")

    # --- 2. [핵심 수정] 동적 활동 시퀀스 생성 ---
    hour_map = {
        1: '새벽', 2: '아침', 3: '오전',
        4: '점심', 5: '점심', 6: '오후',
        7: '오후', 8: '저녁', 9: '저녁',
        10: '밤'
    }
    # 입력된 time_slots 코드를 '오후', '저녁' 등 실제 시간대 이름으로 변환
    course_slots = [hour_map.get(int(slot)) for slot in request['time_slots']]
    logger.info(f"   - 요청된 시간 슬롯: {request['time_slots']} -> 변환된 코스: {course_slots}")
    
    activity_sequence = []
    used_categories = []
    item_vectors_df = assets['item_vectors_df']
    w2v_model = assets['w2v_model']
    previous_activity = None
    
    # 변환된 코스 목록을 순회하며 각 시간대에 맞는 활동을 추천
    for i, slot_name in enumerate(course_slots):
        # 현재 시간대에 맞는 후보 활동들 필터링
        # 이전에 추천된 활동은 제외하여 중복 추천을 방지
        candidate_items = item_vectors_df[
            item_vectors_df.index.str.contains(slot_name) &
            ~item_vectors_df.index.str.split('_').str[0].isin(used_categories)
        ]
        if candidate_items.empty:
            continue

        # 1) SVD 점수 (그룹의 정적 선호도)
        svd_scores = cosine_similarity(group_vector, candidate_items.values)[0]
        
        # 2) W2V 점수 (이전 활동과의 동적 연결성)
        w2v_scores = np.zeros_like(svd_scores)
        if previous_activity and previous_activity in w2v_model.wv:
            w2v_sims = {item: score for item, score in w2v_model.wv.most_similar(previous_activity, topn=len(assets['item_vectors_df']))}
            w2v_scores = np.array([w2v_sims.get(item_name, 0) for item_name in candidate_items.index])
            
        # 3) 하이브리드 최종 점수 계산
        hybrid_scores = (0.7 * svd_scores) + (0.3 * w2v_scores)
        best_activity = candidate_items.index[np.argmax(hybrid_scores)]
        activity_sequence.append(best_activity)
        used_categories.append(best_activity.split('_')[0])
        previous_activity = best_activity

    logger.info(f"✅ SVD/W2V 동적 추천 활동: {activity_sequence}")



    # --- [핵심 수정] Step 3 & 4: DB에서 실제 가게 후보 필터링 및 프롬프트 생성 ---
    store_db = assets['store_db']
    user_loc = (request['location']['latitude'], request['location']['longitude'])

    # 1차 필터링: 위치 기반 (2km 반경)
    store_db['distance'] = store_db.apply(
        lambda row: great_circle(user_loc, (row['latitude'], row['longitude'])).km, axis=1
    )
    nearby_stores = store_db[store_db['distance'] <= 4.0].copy()
    logger.info(f"✅ 위치 기반 필터링 완료. 후보 {len(nearby_stores)}곳")

    llm_input_info = ""
    for i, activity in enumerate(activity_sequence):
        activity_category = activity.split('_')[0]
        
        # 2차 필터링: 카테고리 기반 & 평점순 정렬 후 상위 3개 선택
        final_candidates = nearby_stores[
            nearby_stores['standard_category'] == activity_category
        ].sort_values(by='score', ascending=False).head(3)
        
        llm_input_info += f"\n### 코스 {i+1} ({activity_category}) 추천 후보:\n"
        if not final_candidates.empty:
            for _, store in final_candidates.iterrows():
                # LLM에게 가게의 상세 정보를 동적으로 전달
                llm_input_info += (
                    f"- 가게명: {store['store_name']}\n"
                    f"  - 거리: {store['distance']:.2f}km\n"
                    f"  - 평점: {store['score']}\n"
                    f"  - 대표태그: {store['tag']}\n"
                    f"  - 긍정 키워드: {store['positive']}\n"
                )
        else:
            llm_input_info += "- 주변에 추천할 만한 가게를 찾지 못했습니다.\n"

    # --- Step 5: OpenAI API 호출 ---
    persona_desc = f"{request['personas'][0]['age']} {len(request['personas'])}명 그룹"
    prompt = f"""너는 모임의 목적과 그룹의 특징에 맞춰 최적의 하루 계획을 짜주는 AI 플래너야.

**[모임 정보]**
- 그룹: {persona_desc}
- 모임 목적: '{request['meeting_purpose']}'

**[시스템 추천 후보 상세 정보]**
{llm_input_info}

**[너의 임무]**
1. 위 '시스템 추천 후보' 목록에서, 각 코스별로 모임 목적과 상황에 가장 적합한 가게를 **딱 하나씩만 선택**해.
2. 만약 특정 코스에 추천할 후보가 없다면, 그 코스는 결과에 포함하지 마.
3. 아래 **'출력 형식'을 반드시 그대로 지켜서**, 두 개의 분리된 섹션으로 답변을 생성해줘.

**[출력 형식]**
### ✨ AI 추천 코스
- [코스 1 이름]: [선택한 가게 이름 1]
- [코스 2 이름]: [선택한 가게 이름 2]

### 📝 추천 이유
[위에서 가게를 선택한 구체적인 이유를 여기에 종합적으로 서술]
"""
    
    logger.info("\n✅ 최종 후보군 선정 완료. OpenAI API에 프롬프트 전달 시작...")
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}]
        )
        final_plan = response.choices[0].message.content
        logger.info("✅ OpenAI API로부터 최종 계획 수신 완료!")
        return final_plan
    except Exception as e:
        logger.error(f"❌ OpenAI API 호출 오류: {e}")
        return "API 호출에 실패했습니다."

# --- 4. 메인 실행부 ---
if __name__ == '__main__':
        # 1. OpenAI API 클라이언트 설정
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 오류: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("터미널에서 'export OPENAI_API_KEY=\"sk-...\"' 명령어를 실행해주세요.")
    else:
        client = openai.OpenAI(api_key=api_key)

        # 2. 로컬 자산(모델, 데이터) 로드
        loaded_assets = load_all_assets()

        if loaded_assets:
            # 3. 테스트할 사용자 요청 정의
            test_request_data = {
                "personas": [{"age": "20대", "sex": "M"}],
                "location": {"latitude": 37.56, "longitude": 126.90},
                "meeting_purpose": "친구와 스트레스 풀기",
                "time_slots": ["07", "08", "09"]
            }

            # 4. 추천 로직 실행
            final_recommendation = get_final_recommendation(test_request_data, loaded_assets, client)

            # 5. 최종 결과 출력
            print("\n\n" + "="*25)
            print("🎉 최종 AI 플래너 추천 결과 (OpenAI) 🎉")
            print("="*25)
            pprint.pprint(final_recommendation)
