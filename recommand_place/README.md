# AI Planner API (Vector-based)

## 1. 설치 및 환경설정

### 1.1. Python 환경 준비
- Python 3.8 이상 권장
- 가상환경 사용 권장

```bash
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
```

### 1.2. 필수 패키지 설치
`requirements.txt` 예시:
```
fastapi
uvicorn
pandas
numpy
scikit-learn
openai
geopy
python-dotenv
```

### 1.3. 환경 변수 설정
- OpenAI API 키 필요:  
  `.env` 파일 또는 환경변수로 `OPENAI_API_KEY` 등록

```bash
export OPENAI_API_KEY=sk-xxxxxx   # (Windows: set OPENAI_API_KEY=sk-xxxxxx)
```

- `final_store_db.csv` 파일이 `recommand_place/` 폴더에 있어야 합니다.

---

## 2. 서버 실행

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