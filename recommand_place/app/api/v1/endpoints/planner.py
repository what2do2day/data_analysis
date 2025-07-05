"""플래너 API 엔드포인트"""

from typing import List
from fastapi import APIRouter, HTTPException

from app.models.schemas import PlannerRequest, PlannerResponse, TimeSlotResult
from app.services.store import StoreService
from app.services.vector import VectorService
from app.services.llm import LLMService

router = APIRouter()

@router.post("/generate-plan-vector", response_model=PlannerResponse)
async def generate_plan(request: PlannerRequest):
    """벡터 기반 플래너 생성"""
    
    # 서비스 초기화
    store_service = StoreService()
    vector_service = VectorService()
    llm_service = LLMService()
    
    # 그룹 벡터 생성
    group_vector = vector_service.create_group_vector(request)
    
    # 시간대별 슬롯 가져오기 (그룹 벡터 전달)
    time_slots = store_service.get_time_slots(request.startTime, request.endTime, group_vector)
    
    if not time_slots:
        raise HTTPException(status_code=400, detail="선택된 시간대에 맞는 추천을 찾을 수 없습니다.")
    
    final_plan_slots = []
    
    # 각 시간대별로 추천 생성
    for slot in time_slots:
        # 해당 시간대에 맞는 후보 가게들 가져오기
        candidates = store_service.get_candidate_stores(group_vector, slot['category'], request.keywords)
        
        if not candidates:
            continue
            
        # LLM을 통한 최종 추천
        llm_context = {
            "meeting_purpose": ' '.join(request.keywords),
            "weather": request.weather,
            "time_slot": slot['time_range'],
            "time_name": slot['name']
        }
        
        llm_recommendation = llm_service.get_recommendation(candidates, llm_context)
        
        # 각 시간대별 결과를 추가
        final_plan_slots.append(
            TimeSlotResult(
                slot=slot['time_range'],
                top_candidates=candidates,
                llm_recommendation=llm_recommendation
            )
        )
    
    if not final_plan_slots:
        raise HTTPException(
            status_code=400,
            detail="선택된 시간대에 맞는 추천 장소를 찾을 수 없습니다."
        )
    
    return PlannerResponse(time_slots=final_plan_slots) 