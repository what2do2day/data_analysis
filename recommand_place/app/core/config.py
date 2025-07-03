"""설정 관리 모듈"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 기본 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 프로젝트 설정
CONFIG = {
    "store_db_path": os.path.join(BASE_DIR, "data", "stores_with_preferences_vec.csv"),
    "w2v_model_path": os.path.join(BASE_DIR, "data", "w2v_activity_model.model"),
}

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set") 