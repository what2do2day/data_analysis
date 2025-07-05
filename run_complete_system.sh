#!/bin/bash

echo "🚀 커플 앱 - 완전한 시스템 실행"
echo "================================"
echo ""
echo "📍 통합 API 게이트웨이: http://localhost:8000/docs"
echo "📍 서비스 상태 확인: http://localhost:8000/api/v1/services/status"
echo ""
echo "🔗 개별 서비스 (백엔드):"
echo "  - Generate Question API: http://localhost:8001/docs"
echo "  - Recommend Place API: http://localhost:8002/docs"
echo "  - Text AI API: http://localhost:8003/docs"
echo ""

# 색상 출력을 위한 함수
print_color() {
    echo -e "\033[1;32m$1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m$1\033[0m"
}

# 백그라운드 프로세스 관리를 위한 함수
cleanup() {
    echo ""
    print_warning "전체 시스템을 종료합니다..."
    
    # API Gateway 종료
    pkill -f "python.*api_gateway.py"
    
    # 백엔드 서비스들 종료
    pkill -f "uvicorn.*Generate_question"
    pkill -f "uvicorn.*recommand_place"
    pkill -f "python.*text_ai"
    
    echo "모든 서비스가 종료되었습니다."
    exit 0
}

# Ctrl+C 시 cleanup 함수 실행
trap cleanup SIGINT

# httpx 패키지 설치 확인
if ! python -c "import httpx" 2>/dev/null; then
    print_color "📦 httpx 패키지 설치 중..."
    pip install httpx
    echo ""
fi

print_color "=== 1단계: 백엔드 서비스 실행 ==="

# 1. Generate Question 서비스 실행 (포트 8001)
print_color "🤔 Generate Question API 서버 시작 (포트 8001)..."
cd Generate_question
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 &
GEN_PID=$!
cd ..

# 2. Recommend Place 서비스 실행 (포트 8002)
print_color "🏪 Recommend Place API 서버 시작 (포트 8002)..."
cd recommand_place
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 &
REC_PID=$!
cd ..

# 3. Text AI 서비스 실행 (포트 8003)
print_color "💬 Text AI API 서버 시작 (포트 8003)..."
cd text_ai
python app.py &
TEXT_PID=$!
cd ..

# 백엔드 서비스 시작 대기
print_color "⏳ 백엔드 서비스 시작 대기 중..."
sleep 5

print_color "=== 2단계: API Gateway 실행 ==="

# 4. API Gateway 실행 (포트 8000)
print_color "🌐 API Gateway 시작 (포트 8000)..."
python api_gateway.py &
GATEWAY_PID=$!

# 전체 시스템 시작 대기
sleep 3

echo ""
print_color "🎉 전체 시스템이 성공적으로 실행되었습니다!"
print_color "================================"
echo ""
echo "✨ 메인 접속점:"
echo "   📖 통합 API 문서: http://localhost:8000/docs"
echo "   📊 서비스 상태: http://localhost:8000/api/v1/services/status"
echo ""
echo "🔧 개별 서비스 문서 (개발용):"
echo "   🤔 질문 생성: http://localhost:8001/docs"
echo "   🏪 장소 추천: http://localhost:8002/docs"
echo "   💬 텍스트 AI: http://localhost:8003/docs"
echo ""
echo "🛑 전체 시스템을 종료하려면 Ctrl+C를 누르세요."
echo ""

# 모든 백그라운드 프로세스가 종료될 때까지 대기
wait $GEN_PID $REC_PID $TEXT_PID $GATEWAY_PID 