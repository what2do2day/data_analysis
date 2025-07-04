from fastapi import APIRouter, HTTPException
from app.schemas.question import QuestionResponse
from app.services.question_generator import QuestionGenerator

router = APIRouter()
question_generator = QuestionGenerator()

@router.get("/generate", 
    response_model=QuestionResponse,
    summary="새로운 취향 질문 생성",
    description="""
    커플의 취향을 파악하기 위한 이지선다 질문을 생성합니다.
    각 선택지는 2-4개의 취향 차원에 영향을 주며, 변화량은 -0.1에서 +0.1 사이입니다.
    """,
    response_description="생성된 질문과 각 선택지별 취향 벡터 변화량"
)
async def generate_question():
    """새로운 취향 질문을 생성합니다."""
    result = await question_generator.generate_question()
    if not result:
        raise HTTPException(
            status_code=500,
            detail="질문 생성에 실패했습니다. 서버 로그를 확인해주세요."
        )
    return result 