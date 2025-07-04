import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.core.dimensions import get_dimensions_text

logger = logging.getLogger(__name__)



class QuestionGenerator:
    def __init__(self):
        """질문 생성기 초기화"""
        logger.info("QuestionGenerator가 초기화되었습니다.")

    async def generate_question(self) -> Optional[Dict[str, Any]]:
        """
        OpenAI의 LLM을 사용하여 커플의 취향을 파악할 수 있는
        이지선다 질문과 벡터 조정 값을 포함한 JSON 객체를 생성합니다.
        """
        dimensions_text = get_dimensions_text()
        
        prompt = f"""너는 커플의 취향을 파악하기 위한 이지선다 질문을 만드는 전문 작가야.
아래 규칙에 따라 JSON 형식으로 응답해줘.

## 너의 임무
아래 50개의 취향 차원 목록을 보고, 커플의 성향을 명확하게 구분할 수 있는 흥미로운 질문을 '하나만' 생성해줘.

## 따라야 할 규칙
1. 두 선택지(A와 B)는 서로 상반되거나 명확히 다른 가치를 대표해야 해.
2. 각 선택지는 최소 2개, 최대 4개의 취향 차원에 영향을 줘야 해.
3. 영향을 주는 각 차원의 변화량(change)은 -0.01에서 +0.01 사이의 값이어야 해.
4. **중요**: 변화량은 양수와 음수를 모두 포함해야 해. 각 선택지에 반드시 음수 값도 포함시켜야 해.
5. 변화량 예시: 0.007, -0.004, 0.009, -0.008, 0.003, -0.006, 0.005, -0.002
6. 차원은 반드시 vec_1, vec_2, ..., vec_50 형식으로 표현해야 해.
7. 매번 다른 카테고리의 차원들을 조합해서, 식상하지 않고 새로운 질문을 만들어줘.
8. 응답은 반드시 다음 JSON 형식을 따라야 해:
   {{
     "question": "질문 내용",
     "choice_a": "선택지 A 내용",
     "vectors_a": [
       {{"dimension": "vec_1", "change": 0.007}},
       {{"dimension": "vec_2", "change": -0.004}},
       {{"dimension": "vec_3", "change": 0.009}}
     ],
     "choice_b": "선택지 B 내용",
     "vectors_b": [
       {{"dimension": "vec_1", "change": -0.007}},
       {{"dimension": "vec_2", "change": 0.004}},
       {{"dimension": "vec_4", "change": -0.006}}
     ]
   }}

## 변화량 생성 가이드
- 선택지 A에서 어떤 차원이 +0.007이면, 선택지 B에서는 -0.007로 반대값을 주거나
- 완전히 다른 차원에 영향을 주되, 반드시 양수와 음수를 섞어서 사용해야 함
- 예: choice_a에 [0.008, -0.005, 0.003], choice_b에 [-0.008, 0.005, -0.003]

## 분석할 50개 취향 차원 목록
{dimensions_text}"""

        try:
            logger.info("LLM에게 새로운 질문 생성을 요청합니다...")
            # 가장 기본적인 형태로 클라이언트 초기화
            client = OpenAI()
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that always responds in JSON format."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("질문 생성이 완료되었습니다!")
            return result

        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return None 