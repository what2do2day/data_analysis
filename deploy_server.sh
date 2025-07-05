#!/bin/bash

# 서버 배포용 스크립트 - API Gateway 시스템
# 네이버 클라우드 또는 다른 서버에서 실행

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 루트 권한 확인
if [[ $EUID -eq 0 ]]; then
   log_warning "루트 권한으로 실행하는 것을 권장하지 않습니다."
   log_info "일반 사용자로 실행하세요."
fi

log_info "🚀 커플 앱 API Gateway 시스템 서버 배포 시작"
echo "=================================================="

# 1. 시스템 환경 확인
log_info "🔍 시스템 환경 확인 중..."

# Python 버전 확인
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_success "Python 3.x 발견: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $PYTHON_VERSION == "3."* ]]; then
        log_success "Python 3.x 발견: $PYTHON_VERSION"
        PYTHON_CMD="python"
    else
        log_error "Python 3.x가 필요합니다. 현재 버전: $PYTHON_VERSION"
        exit 1
    fi
else
    log_error "Python이 설치되어 있지 않습니다."
    exit 1
fi

# pip 확인
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    log_error "pip이 설치되어 있지 않습니다."
    exit 1
fi

# 2. 작업 디렉토리 생성
WORK_DIR="/home/$(whoami)/couple-app"
log_info "📁 작업 디렉토리 설정: $WORK_DIR"

if [ ! -d "$WORK_DIR" ]; then
    mkdir -p "$WORK_DIR"
    log_success "작업 디렉토리 생성 완료"
fi

cd "$WORK_DIR"

# 3. 환경 변수 설정
log_info "⚙️ 환경 변수 설정"

if [ ! -f ".env" ]; then
    log_warning "환경 변수 파일(.env)이 없습니다. 새로 생성합니다."
    
    # OpenAI API Key 입력
    echo -n "OpenAI API Key를 입력하세요: "
    read -s OPENAI_API_KEY
    echo
    
    if [ -z "$OPENAI_API_KEY" ]; then
        log_error "OpenAI API Key는 필수입니다."
        exit 1
    fi
    
    # 환경 변수 파일 생성
    cat > .env << EOF
# 환경 변수 설정
OPENAI_API_KEY=$OPENAI_API_KEY
ENVIRONMENT=production
LOG_LEVEL=info
HOST=0.0.0.0
EOF
    
    chmod 600 .env
    log_success "환경 변수 파일 생성 완료"
else
    log_success "기존 환경 변수 파일 사용"
fi

# 4. Python 가상환경 설정
log_info "🐍 Python 가상환경 설정"

if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    log_success "가상환경 생성 완료"
fi

source venv/bin/activate
log_success "가상환경 활성화 완료"

# 5. 의존성 설치
log_info "📦 의존성 설치 중..."

# requirements_server.txt가 없으면 생성
if [ ! -f "requirements_server.txt" ]; then
    log_info "requirements_server.txt 생성 중..."
    cat > requirements_server.txt << 'EOF'
# 서버 배포용 통합 의존성 파일
fastapi==0.109.2
uvicorn==0.27.1
pydantic==2.6.1
python-multipart==0.0.9
httpx==0.27.0
python-dotenv==1.0.1
openai==1.3.0
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=0.24.0
gensim>=4.1.0
geopy>=2.2.0
torch>=2.0.0
transformers>=4.30.0
requests>=2.25.0
aiofiles>=0.7.0
EOF
fi

$PIP_CMD install -r requirements_server.txt
log_success "의존성 설치 완료"

# 6. 로그 디렉토리 생성
log_info "📝 로그 디렉토리 생성"
mkdir -p logs
log_success "로그 디렉토리 생성 완료"

# 7. 시스템 서비스 실행 스크립트 생성
log_info "🔧 시스템 서비스 스크립트 생성"

cat > start_system.sh << 'EOF'
#!/bin/bash

# 커플 앱 시스템 시작 스크립트
cd /home/$(whoami)/couple-app
source venv/bin/activate
source .env

# 기존 프로세스 종료
pkill -f "python.*api_gateway.py" || true
pkill -f "uvicorn.*Generate_question" || true
pkill -f "uvicorn.*recommand_place" || true
pkill -f "python.*text_ai" || true

sleep 2

# 로그 파일 로테이션
if [ -f logs/gateway.log ] && [ $(stat -c%s logs/gateway.log) -gt 10485760 ]; then
    mv logs/gateway.log logs/gateway.log.old
fi

# 백엔드 서비스 시작
echo "Starting backend services..."
cd Generate_question && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 >> ../logs/generate_question.log 2>&1 &
cd ../recommand_place && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 >> ../logs/recommand_place.log 2>&1 &
cd ../text_ai && python app.py >> ../logs/text_ai.log 2>&1 &

# 백엔드 서비스 시작 대기
sleep 5

# API Gateway 시작
cd ..
python api_gateway.py >> logs/gateway.log 2>&1 &

echo "All services started successfully!"
echo "API Gateway: http://$(curl -s ifconfig.me 2>/dev/null || echo localhost):8000/docs"
EOF

chmod +x start_system.sh

# 8. 정지 스크립트 생성
cat > stop_system.sh << 'EOF'
#!/bin/bash

echo "Stopping Couple App System..."

# 모든 관련 프로세스 종료
pkill -f "python.*api_gateway.py" || true
pkill -f "uvicorn.*Generate_question" || true
pkill -f "uvicorn.*recommand_place" || true
pkill -f "python.*text_ai" || true

echo "All services stopped."
EOF

chmod +x stop_system.sh

# 9. 상태 확인 스크립트 생성
cat > check_status.sh << 'EOF'
#!/bin/bash

echo "=== Couple App System Status ==="
echo ""

# 프로세스 상태 확인
echo "🔍 Process Status:"
pgrep -f "python.*api_gateway.py" > /dev/null && echo "✅ API Gateway: Running" || echo "❌ API Gateway: Stopped"
pgrep -f "uvicorn.*Generate_question" > /dev/null && echo "✅ Generate Question: Running" || echo "❌ Generate Question: Stopped"
pgrep -f "uvicorn.*recommand_place" > /dev/null && echo "✅ Recommend Place: Running" || echo "❌ Recommend Place: Stopped"
pgrep -f "python.*text_ai" > /dev/null && echo "✅ Text AI: Running" || echo "❌ Text AI: Stopped"

echo ""
echo "🌐 API Endpoints:"
curl -s http://localhost:8000/health > /dev/null && echo "✅ Gateway (8000): Healthy" || echo "❌ Gateway (8000): Unhealthy"
curl -s http://localhost:8001/ > /dev/null && echo "✅ Generate Question (8001): Healthy" || echo "❌ Generate Question (8001): Unhealthy"
curl -s http://localhost:8002/ > /dev/null && echo "✅ Recommend Place (8002): Healthy" || echo "❌ Recommend Place (8002): Unhealthy"
curl -s http://localhost:8003/ > /dev/null && echo "✅ Text AI (8003): Healthy" || echo "❌ Text AI (8003): Unhealthy"

echo ""
echo "📊 Recent Logs:"
echo "Gateway: $(tail -n 1 logs/gateway.log 2>/dev/null || echo 'No logs')"
EOF

chmod +x check_status.sh

# 10. 방화벽 설정 (선택사항)
log_info "🛡️ 방화벽 설정"

if command -v ufw &> /dev/null; then
    log_warning "방화벽 규칙을 추가하시겠습니까? (y/n)"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ufw allow 8000/tcp
        sudo ufw allow 8001/tcp
        sudo ufw allow 8002/tcp
        sudo ufw allow 8003/tcp
        log_success "방화벽 규칙 추가 완료"
    fi
else
    log_warning "ufw가 설치되어 있지 않습니다. 수동으로 방화벽 설정해주세요."
fi

# 11. 시스템 시작
log_info "🚀 시스템 시작 중..."
./start_system.sh

# 12. 상태 확인
sleep 10
./check_status.sh

# 13. 공인 IP 확인
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "IP 확인 실패")

log_success "🎉 배포 완료!"
echo "=================================================="
echo ""
echo "🌐 접속 URL:"
echo "  📖 통합 API 문서: http://$PUBLIC_IP:8000/docs"
echo "  📊 서비스 상태: http://$PUBLIC_IP:8000/api/v1/services/status"
echo ""
echo "🔧 관리 명령어:"
echo "  시스템 시작: ./start_system.sh"
echo "  시스템 정지: ./stop_system.sh"
echo "  상태 확인: ./check_status.sh"
echo "  로그 확인: tail -f logs/gateway.log"
echo ""
echo "📁 작업 디렉토리: $WORK_DIR"
echo "📝 로그 파일: $WORK_DIR/logs/"
echo ""
log_info "SSH 연결을 끊어도 서비스가 백그라운드에서 계속 실행됩니다." 