from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import API_V1_STR, APP_NAME
from app.api.v1.endpoints import questions

app = FastAPI(
    title=APP_NAME,
    description="""
    커플의 취향을 파악하기 위한 이지선다 질문을 생성하는 API 서버입니다.
    OpenAI의 GPT-4를 사용하여 다양한 취향 차원을 고려한 질문을 생성합니다.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(
    questions.router,
    prefix=API_V1_STR + "/questions",
    tags=["questions"]
) 