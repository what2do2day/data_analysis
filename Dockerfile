# Python 3.9 이미지 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements_unified.txt .
RUN pip install --no-cache-dir -r requirements_unified.txt

# 애플리케이션 코드 복사
COPY . .

# 환경변수 설정
ENV PYTHONPATH=/app

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["python", "unified_app.py"] 