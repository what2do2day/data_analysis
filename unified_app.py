"""
통합 FastAPI 애플리케이션
모든 서비스를 하나의 앱에서 실행 (프록시 방식)
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 통합 앱 생성
app = FastAPI(
    title="Data Analysis API Collection",
    description="커플 취향 질문 생성, AI 장소 추천, 텍스트 분류 서비스 통합 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델 정의
class VectorChange(BaseModel):
    dimension: str = Field(..., description="벡터 차원 (vec_1 ~ vec_50)")
    change: float = Field(..., description="변화량 (-0.01 ~ 0.01)")

class QuestionResponse(BaseModel):
    question: str = Field(..., description="질문 내용")
    choice_a: str = Field(..., description="선택지 A")
    vectors_a: List[VectorChange] = Field(..., description="선택지 A의 벡터 변화량")
    choice_b: str = Field(..., description="선택지 B")
    vectors_b: List[VectorChange] = Field(..., description="선택지 B의 벡터 변화량")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "데이트할 때 어떤 장소를 더 선호하시나요?",
                    "choice_a": "트렌디한 도심 카페에서 시간 보내기",
                    "vectors_a": [
                        {"dimension": "vec_5", "change": 0.008},
                        {"dimension": "vec_37", "change": 0.006},
                        {"dimension": "vec_3", "change": -0.004}
                    ],
                    "choice_b": "조용한 공원에서 산책하며 대화하기",
                    "vectors_b": [
                        {"dimension": "vec_8", "change": 0.007},
                        {"dimension": "vec_16", "change": 0.005},
                        {"dimension": "vec_12", "change": -0.003}
                    ]
                }
            ]
        }
    }

class UserPreference(BaseModel):
    gender: str = Field(..., description="성별 (M/F)", examples=["M", "F"])
    age: int = Field(..., description="나이", examples=[26])
    preferences: Dict[str, float] = Field(..., description="50차원의 취향 벡터", examples=[{f"vec_{i}": round(0.1 * ((i-1)%10+1), 1) for i in range(1, 51)}])

class PlannerRequest(BaseModel):
    user1: UserPreference
    user2: UserPreference
    date: str = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2025-07-03"])
    weather: str = Field(..., description="날씨", examples=["맑음"])
    startTime: str = Field(..., description="시작 시간 (HH:MM)", examples=["13:00"])
    endTime: str = Field(..., description="종료 시간 (HH:MM)", examples=["19:00"])
    keywords: List[str] = Field(..., description="키워드 목록", examples=[["기념일", "로맨틱"]])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
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
            ]
        }
    }

class CandidateStore(BaseModel):
    store_name: str = Field(..., description="가게 이름")
    score: float = Field(..., description="평점")
    similarity: float = Field(..., description="유사도")
    description: str = Field(..., description="가게 설명")

class LLMRecommendation(BaseModel):
    selected: str = Field(..., description="선택된 가게 이름")
    reason: str = Field(..., description="선택 이유")

class TimeSlotResult(BaseModel):
    slot: str = Field(..., description="시간대")
    top_candidates: List[CandidateStore] = Field(..., description="추천 후보 목록")
    llm_recommendation: LLMRecommendation = Field(..., description="LLM 최종 추천")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "slot": "13:00 ~ 19:00",
                    "top_candidates": [
                        {
                            "store_name": "로맨틱 카페",
                            "score": 4.5,
                            "similarity": 0.85,
                            "description": "한식 가게입니다."
                        },
                        {
                            "store_name": "분위기 좋은 레스토랑",
                            "score": 4.2,
                            "similarity": 0.78,
                            "description": "양식 가게입니다."
                        }
                    ],
                    "llm_recommendation": {
                        "selected": "로맨틱 카페",
                        "reason": "기념일에 어울리는 분위기와 음식"
                    }
                }
            ]
        }
    }

class PlannerResponse(BaseModel):
    time_slots: List[TimeSlotResult] = Field(..., description="시간대별 추천 결과")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "time_slots": [
                        {
                            "slot": "13:00 ~ 19:00",
                            "top_candidates": [
                                {
                                    "store_name": "맛집1",
                                    "score": 1.23,
                                    "similarity": 0.98,
                                    "description": "한식 가게입니다."
                                },
                                {
                                    "store_name": "맛집2",
                                    "score": 1.15,
                                    "similarity": 0.95,
                                    "description": "양식 가게입니다."
                                }
                            ],
                            "llm_recommendation": {
                                "selected": "맛집1",
                                "reason": "기념일에 어울리는 분위기와 음식"
                            }
                        }
                    ]
                }
            ]
        }
    }

class TextClassificationRequest(BaseModel):
    text: str = Field(..., description="분류할 텍스트", examples=["이 제품은 정말 훌륭하고 좋습니다!"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "이 제품은 정말 훌륭하고 좋습니다!"
                }
            ]
        }
    }

class TextClassificationResponse(BaseModel):
    prediction: str = Field(..., description="예측 결과 (positive/negative/neutral)", examples=["positive"])
    confidence: float = Field(..., description="신뢰도 (0.0 ~ 1.0)", examples=[0.85])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prediction": "positive",
                    "confidence": 0.85
                }
            ]
        }
    }

# Generate_question 서비스 엔드포인트
@app.get("/api/v1/questions/generate", response_model=QuestionResponse, tags=["Questions"])
async def generate_question():
    """새로운 커플 취향 질문을 생성합니다."""
    try:
        # 직접 QuestionGenerator 사용
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Generate_question 경로 추가
        generate_path = os.path.join(current_dir, "Generate_question")
        if generate_path not in sys.path:
            sys.path.insert(0, generate_path)
        
        # 환경변수 로드
        from dotenv import load_dotenv
        load_dotenv(os.path.join(generate_path, ".env"))
        
        # QuestionGenerator import 및 실행
        from app.services.question_generator import QuestionGenerator
        question_generator = QuestionGenerator()
        result = await question_generator.generate_question()
        
        if result:
            return result
        else:
            raise HTTPException(status_code=500, detail="질문 생성에 실패했습니다.")
            
    except Exception as e:
        logger.error(f"질문 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"질문 생성에 실패했습니다: {str(e)}")

# recommand_place 서비스 엔드포인트
@app.post("/api/v1/planner/generate-plan-vector", response_model=PlannerResponse, tags=["Planner"])
async def generate_plan_vector(request: PlannerRequest):
    """벡터 기반 장소 추천을 생성합니다."""
    try:
        # 더미 후보 가게들 생성
        candidates = [
            CandidateStore(
                store_name="로맨틱 카페",
                score=4.5,
                similarity=0.89,
                description="한식 가게입니다."
            ),
            CandidateStore(
                store_name="분위기 좋은 레스토랑",
                score=4.2,
                similarity=0.82,
                description="양식 가게입니다."
            ),
            CandidateStore(
                store_name="전통 찻집",
                score=4.0,
                similarity=0.75,
                description="카페 가게입니다."
            )
        ]
        
        # LLM 추천 생성
        meeting_purpose = request.keywords[0] if request.keywords else "데이트"
        llm_recommendation = LLMRecommendation(
            selected=candidates[0].store_name,
            reason=f"{meeting_purpose}에 어울리는 분위기와 {request.user1.gender}-{request.user2.gender} 커플에게 적합한 위치"
        )
        
        # 시간대별 결과 생성
        time_slot_result = TimeSlotResult(
            slot=f"{request.startTime} ~ {request.endTime}",
            top_candidates=candidates,
            llm_recommendation=llm_recommendation
        )
        
        return PlannerResponse(time_slots=[time_slot_result])
        
    except Exception as e:
        logger.error(f"장소 추천 오류: {e}")
        raise HTTPException(status_code=500, detail=f"장소 추천에 실패했습니다: {str(e)}")

# text_ai 서비스 엔드포인트
@app.post("/api/v1/text/classify", response_model=TextClassificationResponse, tags=["Text AI"])
async def classify_text(request: TextClassificationRequest):
    """텍스트 분류를 수행합니다."""
    try:
        # 간단한 텍스트 분류 로직
        text_length = len(request.text)
        positive_keywords = ["좋다", "훌륭하다", "멋지다", "최고", "excellent", "good", "great"]
        negative_keywords = ["나쁘다", "싫다", "최악", "terrible", "bad", "awful"]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in request.text.lower())
        negative_count = sum(1 for keyword in negative_keywords if keyword in request.text.lower())
        
        if positive_count > negative_count:
            prediction = "positive"
            confidence = min(0.95, 0.6 + (positive_count * 0.1))
        elif negative_count > positive_count:
            prediction = "negative"
            confidence = min(0.95, 0.6 + (negative_count * 0.1))
        else:
            prediction = "neutral"
            confidence = 0.5 + (text_length / 1000)
            
        confidence = min(confidence, 0.95)
        
        return TextClassificationResponse(
            prediction=prediction,
            confidence=round(confidence, 2)
        )
        
    except Exception as e:
        logger.error(f"텍스트 분류 오류: {e}")
        raise HTTPException(status_code=500, detail=f"텍스트 분류에 실패했습니다: {str(e)}")

@app.post("/api/v1/text/upload-model", tags=["Text AI"])
async def upload_model():
    """모델 업로드 엔드포인트"""
    return {"message": "모델 업로드 기능은 구현 예정입니다.", "status": "pending"}

@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트 - 사용 가능한 서비스 목록"""
    return {
        "message": "Data Analysis API Collection",
        "version": "1.0.0",
        "services": {
            "questions": {
                "description": "커플 취향 질문 생성",
                "endpoint": "/api/v1/questions/generate",
                "method": "GET"
            },
            "planner": {
                "description": "AI 장소 추천",
                "endpoint": "/api/v1/planner/generate-plan-vector",
                "method": "POST"
            },
            "text_ai": {
                "description": "텍스트 분류",
                "endpoints": [
                    {
                        "path": "/api/v1/text/classify",
                        "method": "POST",
                        "description": "텍스트 감정 분류"
                    },
                    {
                        "path": "/api/v1/text/upload-model",
                        "method": "POST",
                        "description": "모델 업로드"
                    }
                ]
            }
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy", 
        "services": ["questions", "planner", "text_ai"],
        "timestamp": "2025-01-04T11:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 통합 API 서버 시작...")
    logger.info("📖 API 문서: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000) 