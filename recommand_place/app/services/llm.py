"""LLM 서비스 모듈"""

import json
import logging
from typing import List, Dict
import openai
from app.models.schemas import LLMRecommendation, CandidateStore
from app.core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    def get_recommendation(self, candidates: List[CandidateStore], context: Dict) -> LLMRecommendation:
        """후보 가게들 중에서 최적의 장소를 추천합니다."""
        llm_input_info = ""
        for cand in candidates:
            llm_input_info += f"- 가게명: {cand.store_name}, 총점: {cand.score:.2f}, 유사도: {cand.similarity:.2f}, 설명: {cand.description}\n"

        prompt = f"""[모임 정보]
- 목적: {context.get('meeting_purpose', '')}
- 날씨: {context.get('weather', '')}
- 시간대: {context.get('time_slot', '')}

[시스템 추천 후보]
{llm_input_info}

[너의 임무]
위 후보 중에서 가장 적합한 가게 하나만 선택하고, 그 이유를 JSON 형식으로 답변해줘.
시간대와 목적에 맞는 선택을 해주세요.
{{ "selected": "가게이름", "reason": "선택한 이유" }}
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}]
            )
            result = json.loads(response.choices[0].message.content)
            return LLMRecommendation(**result)
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return LLMRecommendation(selected="선택 실패", reason=str(e))

def call_llm(candidates: List[Dict], context: Dict) -> LLMRecommendation:
    """LLM을 호출하여 최적의 장소 추천을 받습니다."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
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