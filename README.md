# 🚀 Data Analysis API Collection

AI 기반 데이터 분석 서비스 통합 플랫폼

## 📋 프로젝트 개요

이 프로젝트는 3개의 AI 서비스를 하나의 통합 서버로 제공합니다:

- **🤖 Generate_question**: 커플 취향 질문 생성 API (OpenAI GPT 기반)
- **🎯 recommand_place**: AI 장소 추천 시스템 (벡터 기반)
- **📝 text_ai**: 텍스트 감정 분류 AI

## 🛠️ 빠른 시작 가이드

### 2. 환경 설정

#### Python 가상환경 생성

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows
```

#### 의존성 설치

```bash
pip install -r requirements_unified.txt
```

### 3. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
# OpenAI API 키 (필수)
OPENAI_API_KEY=your_openai_api_key_here
```

서버가 성공적으로 시작되면:

- 🌐 **API 서버**: http://localhost:8000
- 📖 **API 문서**: http://localhost:8000/docs
- 🔍 **ReDoc**: http://localhost:8000/redoc

## 🧪 API 테스트 방법

### Swagger UI

http://localhost:8000/docs

## 🐳 Docker로 실행 (선택사항)

### Docker Compose 사용

```bash
# .env 파일 설정 후
docker-compose up --build
```

### 개별 Docker 실행

```bash
docker build -t data-analysis-api .
docker run -p 8000:8000 --env-file .env data-analysis-api
```

## 📁 프로젝트 구조

```
data_analysis/
├── 🚀 unified_app.py              # 통합 서버 (메인 실행 파일)
├── 📋 requirements_unified.txt     # 통합 의존성
├── 🐳 Dockerfile                  # Docker 설정
├── 🐳 docker-compose.yml          # Docker Compose 설정
├── 📖 README.md                   # 이 파일
├── 🔧 .env                        # 환경변수 (직접 생성)
│
├── 📁 Generate_question/           # 질문 생성 서비스
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── services/
│   │   └── schemas/
│   └── requirements.txt
│
├── 📁 recommand_place/            # 장소 추천 서비스
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── data/
│   └── requirements.txt
│
└── 📁 text_ai/                   # 텍스트 분류 서비스
    ├── app.py
    ├── text_cla.py
    └── requirements.txt
```

## 🌐 API 엔드포인트

### 질문 생성 API

- **GET** `/api/v1/questions/generate`
- 커플 취향 질문과 벡터 변화량을 생성합니다.

### 장소 추천 API

- **POST** `/api/v1/planner/generate-plan-vector`
- 사용자 취향 벡터를 기반으로 장소를 추천합니다.

### 텍스트 분류 API

- **POST** `/api/v1/text/classify`
- 텍스트의 감정을 분류합니다 (positive/negative/neutral).

### 기타

- **GET** `/health` - 서버 상태 확인
- **GET** `/docs` - Swagger UI 문서
- **GET** `/redoc` - ReDoc 문서

## 🔧 환경변수 설정

| 변수명           | 설명          | 필수 여부 | 기본값      |
| ---------------- | ------------- | --------- | ----------- |
| `OPENAI_API_KEY` | OpenAI API 키 | ✅ 필수   | -           |
| `ENVIRONMENT`    | 실행 환경     | ⚪ 선택   | development |
| `LOG_LEVEL`      | 로그 레벨     | ⚪ 선택   | INFO        |

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 이슈를 생성해주세요.

---

⭐ 이 프로젝트가 도움이 되었다면 별표를 눌러주세요!
