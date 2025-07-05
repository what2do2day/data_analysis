"""
API Gateway - 3개의 독립적인 서버를 통합하는 게이트웨이
"""

import httpx
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import asyncio

# API Gateway 앱 생성
app = FastAPI(
    title="커플 앱 - 통합 API Gateway",
    description="""
    3개의 독립적인 마이크로서비스를 통합하는 API Gateway입니다.
    
    **구성 서비스:**
    - 🤔 Generate Question API: 커플 취향 질문 생성
    - 🏪 Recommend Place API: AI 기반 장소 추천
    - 💬 Text AI API: 텍스트 공감 유형 분류
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 URL 설정
SERVICES = {
    "question": "http://localhost:8001",
    "place": "http://localhost:8002", 
    "text_ai": "http://localhost:8003"
}

# 공통 응답 모델
class ServiceStatus(BaseModel):
    service: str
    status: str
    url: str

class GatewayInfo(BaseModel):
    message: str
    services: List[ServiceStatus]
    total_services: int

# =============================================================================
# 각 서비스의 요청/응답 스키마 정의
# =============================================================================

# Generate Question API 스키마
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

# Recommend Place API 스키마
class UserPreference(BaseModel):
    gender: str = Field(..., description="성별 (M/F)")
    age: int = Field(..., description="나이")
    preferences: Dict[str, float] = Field(..., description="50차원의 취향 벡터")

class PlannerRequest(BaseModel):
    user1: UserPreference = Field(..., description="첫 번째 사용자 정보")
    user2: UserPreference = Field(..., description="두 번째 사용자 정보")
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    weather: str = Field(..., description="날씨")
    startTime: str = Field(..., description="시작 시간 (HH:MM)")
    endTime: str = Field(..., description="종료 시간 (HH:MM)")
    keywords: List[str] = Field(..., description="키워드 목록")

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
    store_name: str = Field(..., description="가게 이름")
    score: float = Field(..., description="점수")
    similarity: float = Field(..., description="유사도")
    description: str = Field(..., description="설명")

class LLMRecommendation(BaseModel):
    selected: str = Field(..., description="선택된 가게")
    reason: str = Field(..., description="선택 이유")

class TimeSlotResult(BaseModel):
    slot: str = Field(..., description="시간대")
    top_candidates: List[CandidateStore] = Field(..., description="추천 가게 목록")
    llm_recommendation: LLMRecommendation = Field(..., description="LLM 추천 결과")

class PlannerResponse(BaseModel):
    time_slots: List[TimeSlotResult] = Field(..., description="시간대별 추천 결과")

# Text AI API 스키마
class TextRequest(BaseModel):
    text: str = Field(..., description="분류할 텍스트")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "힘든 시간을 보내고 있는 것 같아서 걱정이 되네요. 괜찮으시다면 언제든 얘기해 주세요."
            }
        }

class PredictionResponse(BaseModel):
    text: str = Field(..., description="입력된 텍스트")
    prediction: str = Field(..., description="예측된 공감 유형 (격려, 위로, 동조, 조언)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "힘든 시간을 보내고 있는 것 같아서 걱정이 되네요. 괜찮으시다면 언제든 얘기해 주세요.",
                "prediction": "위로"
            }
        }

# HTTP 클라이언트 설정
async def make_request(method: str, url: str, **kwargs):
    """외부 서비스로 HTTP 요청을 보내는 공통 함수"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(method, url, **kwargs)
            return response
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"서비스 연결 실패: {str(e)}"
            )

# =============================================================================
# 게이트웨이 정보 및 헬스체크
# =============================================================================

@app.get("/", response_model=GatewayInfo)
async def gateway_info():
    """API Gateway 정보 및 서비스 상태 확인"""
    services_status = []
    
    for service_name, service_url in SERVICES.items():
        try:
            response = await make_request("GET", f"{service_url}/")
            status = "✅ 정상" if response.status_code == 200 else "❌ 오류"
        except:
            status = "❌ 연결 실패"
        
        services_status.append(ServiceStatus(
            service=service_name,
            status=status,
            url=service_url
        ))
    
    return GatewayInfo(
        message="커플 앱 API Gateway가 정상 작동 중입니다!",
        services=services_status,
        total_services=len(SERVICES)
    )

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy", "gateway": "running"}

# =============================================================================
# 질문 생성 서비스 (Generate Question API)
# =============================================================================

@app.get("/api/v1/questions/generate", 
         response_model=QuestionResponse,
         tags=["🤔 Questions"],
         summary="새로운 취향 질문 생성",
         description="커플의 취향을 파악하기 위한 이지선다 질문을 생성합니다.")
async def generate_question():
    """질문 생성 서비스로 요청 전달"""
    response = await make_request("GET", f"{SERVICES['question']}/api/v1/questions/generate")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"질문 생성 실패: {response.text}"
        )

# =============================================================================
# 장소 추천 서비스 (Recommend Place API)  
# =============================================================================

@app.post("/api/v1/places/generate-plan",
          response_model=PlannerResponse,
          tags=["🏪 Places"],
          summary="벡터 기반 장소 추천",
          description="AI 기반으로 커플에게 적합한 장소를 추천합니다.")
async def generate_place_plan(request: PlannerRequest):
    """장소 추천 서비스로 요청 전달"""
    response = await make_request(
        "POST", 
        f"{SERVICES['place']}/api/v1/generate-plan-vector",
        json=request.dict()
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"장소 추천 실패: {response.text}"
        )

# =============================================================================
# 텍스트 AI 서비스 (Text AI API)
# =============================================================================

@app.post("/api/v1/text/classify",
          response_model=PredictionResponse,
          tags=["💬 Text AI"],
          summary="텍스트 공감 유형 분류",
          description="텍스트를 분석하여 공감 유형(격려, 위로, 동조, 조언)을 분류합니다.")
async def classify_text(request: TextRequest):
    """텍스트 분류 서비스로 요청 전달"""
    response = await make_request(
        "POST",
        f"{SERVICES['text_ai']}/classify",
        json=request.dict()
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"텍스트 분류 실패: {response.text}"
        )

# =============================================================================
# WebSocket 지원 (Text AI 채팅)
# =============================================================================

@app.websocket("/api/v1/text/chat")
async def websocket_chat_proxy(websocket: WebSocket):
    """Text AI 서비스의 WebSocket 채팅 프록시"""
    await websocket.accept()
    
    try:
        # Text AI 서비스와 WebSocket 연결
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", f"{SERVICES['text_ai']}/ws/chat") as response:
                if response.status_code == 101:  # WebSocket Upgrade
                    # WebSocket 프록시 로직 구현
                    # 실제 구현에서는 더 복잡한 프록시 로직이 필요합니다
                    while True:
                        data = await websocket.receive_text()
                        # 여기에 실제 WebSocket 프록시 로직 구현
                        await websocket.send_text(f"Proxy received: {data}")
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))

# =============================================================================
# 서비스 관리 엔드포인트
# =============================================================================

@app.get("/api/v1/services/status",
         tags=["🛠️ Management"],
         summary="모든 서비스 상태 확인")
async def check_all_services():
    """모든 마이크로서비스의 상태를 확인합니다"""
    results = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = await make_request("GET", f"{service_url}/", timeout=5.0)
            results[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": service_url,
                "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
            }
        except Exception as e:
            results[service_name] = {
                "status": "unreachable",
                "url": service_url,
                "error": str(e)
            }
    
    return results

# =============================================================================
# 메인 실행부
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 API Gateway 시작 중...")
    print("📍 통합 API 문서: http://localhost:8000/docs")
    print("📍 서비스 상태: http://localhost:8000/api/v1/services/status")
    print("")
    print("🔗 연결된 서비스:")
    print("  - 질문 생성: http://localhost:8001")
    print("  - 장소 추천: http://localhost:8002")
    print("  - 텍스트 AI: http://localhost:8003")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 