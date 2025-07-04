from pydantic import BaseModel, Field
from typing import List, Optional

class VectorChange(BaseModel):
    """취향 벡터 변화량"""
    dimension: str = Field(..., description="취향 차원 태그 (예: #로맨틱)")
    change: float = Field(..., ge=-0.1, le=0.1, description="변화량 (-0.1 ~ 0.1)")

class QuestionResponse(BaseModel):
    """질문 생성 응답"""
    question: str = Field(..., description="생성된 질문")
    choice_a: str = Field(..., description="선택지 A")
    vectors_a: List[VectorChange] = Field(..., description="선택지 A의 취향 벡터 변화량")
    choice_b: str = Field(..., description="선택지 B")
    vectors_b: List[VectorChange] = Field(..., description="선택지 B의 취향 벡터 변화량")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "데이트 코스를 고른다면?",
                "choice_a": "도심 속 트렌디한 카페와 갤러리 투어",
                "vectors_a": [
                    {"dimension": "#모던한", "change": 0.1},
                    {"dimension": "#힙한", "change": 0.1}
                ],
                "choice_b": "한적한 교외의 자연 속 피크닉",
                "vectors_b": [
                    {"dimension": "#자연친화적", "change": 0.1},
                    {"dimension": "#휴식적인", "change": 0.1}
                ]
            }
        } 