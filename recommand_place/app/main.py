"""메인 FastAPI 애플리케이션"""

import logging
from fastapi import FastAPI
from app.api.v1.endpoints import planner

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="AI Planner API v2 (Vector-based)")

# 라우터 등록
app.include_router(planner.router, prefix="/api/v1", tags=["planner"])

# 시작 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    logger.info("애플리케이션 시작")

# 종료 이벤트 핸들러
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("애플리케이션 종료") 