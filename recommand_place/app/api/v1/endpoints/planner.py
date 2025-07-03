"""플래너 API 엔드포인트"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import PlannerRequest, PlannerResponse, TimeSlotResult
from app.services.store import StoreService
from app.services.vector import VectorService
from app.services.llm import call_llm

router = APIRouter()
store_service = StoreService()
vector_service = VectorService()

@router.post("/generate-plan-vector", response_model=PlannerResponse)
def generate_plan(request: PlannerRequest):
    """벡터 기반 계획 생성 엔드포인트"""
    try:
        # 그룹 벡터 생성
        group_vector = vector_service.create_group_vector(request)
        
        # 시간대별 슬롯 가져오기
        time_slots = store_service.get_time_slots(request.startTime, request.endTime)

        final_plan_slots = []
        for slot in time_slots:
            # 후보 가게 추천
            top_candidates = store_service.get_candidate_stores(
                group_vector=group_vector,
                categories=slot['category']
            )

            # LLM 추천
            llm_context = {
                "meeting_purpose": request.keywords[0],
                "weather": request.weather
            }
            llm_recommendation = call_llm(
                [candidate.dict() for candidate in top_candidates],
                llm_context
            )

            final_plan_slots.append(
                TimeSlotResult(
                    slot=slot['time_range'],
                    top_candidates=top_candidates,
                    llm_recommendation=llm_recommendation
                )
            )

        return PlannerResponse(time_slots=final_plan_slots)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 