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

