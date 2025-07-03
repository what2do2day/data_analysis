# AI Planner API

벡터 기반의 지능형 장소 추천 시스템

## 프로젝트 구조

```
recommand_place/
├── app/
│   ├── api/              # API 엔드포인트
│   ├── core/             # 설정 및 상수
│   ├── models/           # Pydantic 모델
│   ├── services/         # 비즈니스 로직
│   └── main.py          # 앱 진입점
├── data/                 # 데이터 파일
└── requirements.txt      # 의존성
```

## 설치 방법

1. 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. 환경변수 설정:
`.env` 파일을 생성하고 다음 내용을 추가:
```
OPENAI_API_KEY=your_api_key_here
```
<<<<<<< HEAD

## 실행 방법

```bash
uvicorn app.main:app --reload
```

서버가 시작되면 http://localhost:8000 에서 API를 사용할 수 있습니다.
API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다.

## API 엔드포인트
=======
---
>>>>>>> a6a7996b1be9b8f757f20c6baec37fdfea6f4fb6

### POST /api/v1/generate-plan-vector

사용자들의 취향과 상황을 고려하여 최적의 장소를 추천합니다.

요청 예시:
```json
{
    "user1": {
        "gender": "M",
        "age": 26,
        "preferences": {"vec_1": 0.1, ...}
    },
    "user2": {
        "gender": "F",
        "age": 26,
        "preferences": {"vec_1": 0.1, ...}
    },
    "date": "2025-07-03",
    "weather": "맑음",
    "startTime": "13:00",
    "endTime": "19:00",
    "keywords": ["기념일", "로맨틱"]
}
```

## 데이터 모델

- `stores_with_preferences_vec.csv`: 가게 정보와 벡터
- `w2v_activity_model.model`: Word2Vec 모델

## 라이선스

MIT License

```bash
cd recommand_place
uvicorn main:app --reload
```
- 서버가 `http://localhost:8000`에서 실행됩니다.

---

## 3. API 테스트

### 3.1. Swagger UI로 테스트
- 브라우저에서 [http://localhost:8000/docs](http://localhost:8000/docs) 접속

## 4. 서버 배포 (간단한 방법)

### 4.1. 로컬에서만 쓸 경우
- 위의 `uvicorn` 명령으로 충분

### 4.2. 외부에서 접속하려면
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
- 방화벽/공유기 포트포워딩 필요

### 4.3. 클라우드 서버 (예: AWS, GCP, Azure)
- 서버에 위 환경 세팅 후 위와 같이 실행
- 도메인 연결, HTTPS 적용 등은 별도 작업 필요

---

## 5. 예시 응답

```json
{
  "time_slots": [
    {
      "slot": "11:00 ~ 14:59",
      "top_candidates": [
        {
          "store_name": "맛집1",
          "score": 1.23,
          "similarity": 0.98,
          "description": "한식 가게입니다."
        }
        // ... 최대 3개
      ],
      "llm_recommendation": {
        "selected": "맛집1",
        "reason": "기념일에 어울리는 분위기와 음식"
      }
    }
    // ... 오후, 저녁 슬롯
  ]
}
```

