"""Pydantic 모델 정의"""

from pydantic import BaseModel, Field
from typing import List, Dict

class UserPreference(BaseModel):
    gender: str
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
                    "preferences": {f"vec_{i}": round(0.1 * ((i-1)%10+1), 1) for i in range(1, 51)}
                },
                "user2": {
                    "gender": "F",
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