"""설정 관리 모듈"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# API 설정
API_V1_STR = "/api/v1"
APP_NAME = "Couple Preference Question Generator"

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set") 