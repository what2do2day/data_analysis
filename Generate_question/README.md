# 커플 취향 질문 생성기 API

커플의 취향을 파악하기 위한 이지선다 질문을 자동으로 생성하는 API 서버입니다.
OpenAI의 GPT-4를 활용하여 50개의 취향 차원을 고려한 흥미로운 질문을 생성합니다.

## 기능

- 이지선다 질문 자동 생성
- 각 선택지별 취향 벡터 변화량 계산
- Swagger UI를 통한 API 문서 제공
- 로깅 시스템을 통한 에러 추적

## 기술 스택

- Python 3.8+
- FastAPI
- OpenAI GPT-4
- Pydantic
- uvicorn

## 설치 방법

1. 저장소 클론

```bash
git clone <repository-url>
cd Generate_question
```

2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치

```bash
pip install -r requirements.txt
```

4. 환경변수 설정
   `.env` 파일을 생성하고 다음 내용을 추가합니다:

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4
```

## 실행 방법

개발 서버 실행:

```bash
uvicorn app.main:app --reload
```

서버가 실행되면 다음 URL에서 API를 사용할 수 있습니다:

- API 문서: http://localhost:8000/docs
- ReDoc 문서: http://localhost:8000/redoc
- API 엔드포인트: http://localhost:8000/api/v1/questions/generate

## API 엔드포인트

### GET /api/v1/questions/generate

새로운 취향 질문을 생성합니다.

**응답 예시:**

```json
{
  "question": "데이트 코스를 고른다면?",
  "choice_a": "도심 속 트렌디한 카페와 갤러리 투어",
  "vectors_a": [
    { "dimension": "#모던한", "change": 0.1 },
    { "dimension": "#힙한", "change": 0.1 }
  ],
  "choice_b": "한적한 교외의 자연 속 피크닉",
  "vectors_b": [
    { "dimension": "#자연친화적", "change": 0.1 },
    { "dimension": "#휴식적인", "change": 0.1 }
  ]
}
```

## 배포 가이드

1. 프로덕션 환경 설정

```bash
# 프로덕션용 환경변수 설정
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-4
```

2. 프로덕션 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 보안 고려사항

1. `.env` 파일을 `.gitignore`에 추가하여 API 키 보호
2. 프로덕션 환경에서는 구체적인 CORS origin 설정
3. 적절한 rate limiting 설정 필요
4. API 키 순환 정책 수립

## 로깅

로그는 기본적으로 콘솔에 출력되며, 다음과 같은 정보를 포함합니다:

- API 요청/응답
- OpenAI API 호출 결과
- 에러 및 예외 상황

## 문제 해결

일반적인 문제 해결 방법:

1. OpenAI API 키 오류

   - `.env` 파일의 API 키 확인
   - 환경변수 설정 확인

2. 서버 시작 실패

   - 포트 충돌 확인
   - 의존성 설치 상태 확인

3. 질문 생성 실패
   - 로그에서 구체적인 에러 메시지 확인
   - OpenAI API 상태 확인

## 라이센스

MIT License
