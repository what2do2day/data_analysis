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

## 실행 방법

```bash
uvicorn app.main:app --reload
```

서버가 시작되면 http://localhost:8000 에서 API를 사용할 수 있습니다.
API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다.

## API 엔드포인트

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

### 3.2. curl로 테스트

```bash
curl -X POST "http://localhost:8000/generate-plan-vector" ^
-H "Content-Type: application/json" ^
-d "{\"user1\": {\"gender\": \"M\", \"age\": 26, \"preferences\": {\"vec_1\": 0.9, \"vec_2\": 0.8, \"vec_3\": 1.0, \"vec_4\": 0.7, \"vec_5\": 0.6, \"vec_6\": 0.5, \"vec_7\": 0.4, \"vec_8\": 0.3, \"vec_9\": 0.2, \"vec_10\": 0.1, \"vec_11\": 0.9, \"vec_12\": 0.8, \"vec_13\": 1.0, \"vec_14\": 0.7, \"vec_15\": 0.6, \"vec_16\": 0.5, \"vec_17\": 0.4, \"vec_18\": 0.3, \"vec_19\": 0.2, \"vec_20\": 0.1, \"vec_21\": 0.9, \"vec_22\": 0.8, \"vec_23\": 1.0, \"vec_24\": 0.7, \"vec_25\": 0.6, \"vec_26\": 0.5, \"vec_27\": 0.4, \"vec_28\": 0.3, \"vec_29\": 0.2, \"vec_30\": 0.1, \"vec_31\": 0.9, \"vec_32\": 0.8, \"vec_33\": 1.0, \"vec_34\": 0.7, \"vec_35\": 0.6, \"vec_36\": 0.5, \"vec_37\": 0.4, \"vec_38\": 0.3, \"vec_39\": 0.2, \"vec_40\": 0.1, \"vec_41\": 0.9, \"vec_42\": 0.8, \"vec_43\": 1.0, \"vec_44\": 0.7, \"vec_45\": 0.6, \"vec_46\": 0.5, \"vec_47\": 0.4, \"vec_48\": 0.3, \"vec_49\": 0.2, \"vec_50\": 0.1}}, \"user2\": {\"gender\": \"F\", \"age\": 26, \"preferences\": {\"vec_1\": 0.9, \"vec_2\": 0.8, \"vec_3\": 1.0, \"vec_4\": 0.7, \"vec_5\": 0.6, \"vec_6\": 0.5, \"vec_7\": 0.4, \"vec_8\": 0.3, \"vec_9\": 0.2, \"vec_10\": 0.1, \"vec_11\": 0.9, \"vec_12\": 0.8, \"vec_13\": 1.0, \"vec_14\": 0.7, \"vec_15\": 0.6, \"vec_16\": 0.5, \"vec_17\": 0.4, \"vec_18\": 0.3, \"vec_19\": 0.2, \"vec_20\": 0.1, \"vec_21\": 0.9, \"vec_22\": 0.8, \"vec_23\": 1.0, \"vec_24\": 0.7, \"vec_25\": 0.6, \"vec_26\": 0.5, \"vec_27\": 0.4, \"vec_28\": 0.3, \"vec_29\": 0.2, \"vec_30\": 0.1, \"vec_31\": 0.9, \"vec_32\": 0.8, \"vec_33\": 1.0, \"vec_34\": 0.7, \"vec_35\": 0.6, \"vec_36\": 0.5, \"vec_37\": 0.4, \"vec_38\": 0.3, \"vec_39\": 0.2, \"vec_40\": 0.1, \"vec_41\": 0.9, \"vec_42\": 0.8, \"vec_43\": 1.0, \"vec_44\": 0.7, \"vec_45\": 0.6, \"vec_46\": 0.5, \"vec_47\": 0.4, \"vec_48\": 0.3, \"vec_49\": 0.2, \"vec_50\": 0.1}}, \"date\": \"2025-07-03\", \"weather\": \"맑음\", \"startTime\": \"11:00\", \"endTime\": \"22:59\", \"keywords\": [\"기념일\", \"로맨틱\"]}"
```

> **참고:**  
> - Windows PowerShell에서는 `^`로 줄바꿈,  
> - macOS/Linux에서는 `\`로 줄바꿈 사용  
> - 실제 요청에서는 `"preferences"`에 50개 벡터값을 모두 넣어야 합니다.

---

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

## 5. 로컬 테스트 팁

- 서버 실행 후,  
  - [http://localhost:8000/docs](http://localhost:8000/docs)에서 직접 테스트  
  - 또는 위 curl 명령어로 테스트  
- 응답이 잘 오면 연동 성공!

---

## 6. 기타

- 오류 발생 시, 콘솔 로그/에러 메시지 확인
- `final_store_db.csv` 파일, OpenAI API Key, 50차원 벡터 등 필수 데이터 확인

---

## 7. 예시 응답

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

---

## 8. 자주 묻는 질문

- **Q. 50차원 벡터는 어떻게 넣나요?**  
  → `"preferences": {"vec_1": 0.9, ..., "vec_50": 0.1}` 형식으로 50개 모두 넣어야 합니다.

- **Q. OpenAI Key가 없으면?**  
  → LLM 추천 부분이 동작하지 않습니다. 