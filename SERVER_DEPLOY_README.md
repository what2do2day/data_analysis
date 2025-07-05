# 🚀 커플 앱 API Gateway 서버 배포 가이드

## 📋 개요

이 가이드는 **커플 앱 API Gateway 시스템**을 서버에 배포하는 방법을 설명합니다.

### 🏗️ 시스템 구조

```
API Gateway (포트 8000)
├── 🤔 Generate Question API (포트 8001)
├── 🏪 Recommend Place API (포트 8002)
└── 💬 Text AI API (포트 8003)
```

### ✨ 주요 기능

- **통합 API 문서**: 모든 서비스를 하나의 스웨거에서 확인
- **자동 프록시**: 요청을 적절한 백엔드 서비스로 전달
- **서비스 상태 모니터링**: 실시간 서비스 상태 확인
- **백그라운드 실행**: SSH 연결 종료 후에도 지속 실행

## 🔧 배포 방법

### 방법 1: 자동 배포 (권장)

#### 1단계: 파일 복사

```bash
./copy_to_server.sh
```

#### 2단계: 서버 접속

```bash
ssh your-user@your-server-ip
cd /home/your-user/couple-app-deploy
```

#### 3단계: 배포 실행

```bash
./deploy_server.sh
```

### 방법 2: 수동 배포

#### 1단계: 서버 준비

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 3.x 설치 (없는 경우)
sudo apt install python3 python3-pip python3-venv -y

# 필요한 도구 설치
sudo apt install curl wget -y
```

#### 2단계: 파일 업로드

```bash
# 로컬에서 실행
scp -r Generate_question/ recommand_place/ text_ai/ api_gateway.py requirements_server.txt deploy_server.sh your-user@your-server:/home/your-user/
```

#### 3단계: 배포 스크립트 실행

```bash
# 서버에서 실행
chmod +x deploy_server.sh
./deploy_server.sh
```

## 📋 배포 전 준비사항

### 🛠️ 시스템 요구사항

- **OS**: Ubuntu 18.04+ / CentOS 7+ / 기타 Linux
- **Python**: 3.8 이상
- **Memory**: 최소 2GB (권장 4GB)
- **Storage**: 최소 5GB 여유 공간

### 🔑 필수 정보

1. **OpenAI API Key**: 질문 생성 및 장소 추천에 필요
2. **서버 SSH 접속 정보**: IP, 사용자명, 포트

### 🌐 네트워크 설정

다음 포트들이 열려있어야 합니다:

- **8000**: API Gateway (메인 포트)
- **8001**: Generate Question API
- **8002**: Recommend Place API
- **8003**: Text AI API

## 🚀 배포 후 확인

### 1. 서비스 상태 확인

```bash
./check_status.sh
```

### 2. API 테스트

```bash
# Gateway 접속 테스트
curl http://localhost:8000/health

# 개별 서비스 테스트
curl http://localhost:8001/
curl http://localhost:8002/
curl http://localhost:8003/
```

### 3. 웹 브라우저 접속

```
http://your-server-ip:8000/docs
```

## 📊 시스템 관리

### 🔧 관리 명령어

```bash
# 시스템 시작
./start_system.sh

# 시스템 정지
./stop_system.sh

# 상태 확인
./check_status.sh

# 로그 확인
tail -f logs/gateway.log
tail -f logs/generate_question.log
tail -f logs/recommand_place.log
tail -f logs/text_ai.log
```

### 📝 로그 위치

```
/home/your-user/couple-app/logs/
├── gateway.log           # API Gateway 로그
├── generate_question.log # 질문 생성 서비스 로그
├── recommand_place.log   # 장소 추천 서비스 로그
└── text_ai.log          # 텍스트 AI 서비스 로그
```

### 🔄 서비스 재시작

```bash
# 전체 재시작
./stop_system.sh && ./start_system.sh

# 개별 서비스 재시작
pkill -f "python.*api_gateway.py" && python api_gateway.py >> logs/gateway.log 2>&1 &
```

## 🛡️ 보안 설정

### 방화벽 설정

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 8002/tcp
sudo ufw allow 8003/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --permanent --add-port=8002/tcp
sudo firewall-cmd --permanent --add-port=8003/tcp
sudo firewall-cmd --reload
```

### 환경 변수 보안

```bash
# .env 파일 권한 설정
chmod 600 .env

# 환경 변수 확인
grep -v "^#" .env | grep -v "^$"
```

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
sudo netstat -tlnp | grep :8000
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 PID
```

#### 2. 권한 오류

```bash
# 파일 권한 확인
ls -la
chmod +x *.sh
```

#### 3. 의존성 설치 실패

```bash
# 가상환경 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_server.txt
```

#### 4. 서비스 응답 없음

```bash
# 서비스 로그 확인
tail -f logs/gateway.log

# 프로세스 상태 확인
ps aux | grep python
```

### 로그 분석

```bash
# 에러 로그 확인
grep -i error logs/*.log

# 최근 로그 확인
tail -n 50 logs/gateway.log

# 실시간 로그 모니터링
tail -f logs/gateway.log
```

## 📞 지원

### 디버깅 정보 수집

```bash
# 시스템 정보
uname -a
python3 --version
pip3 --version

# 서비스 상태
./check_status.sh

# 로그 파일 크기
du -sh logs/
```

### 접속 URL 요약

배포 완료 후 다음 URL들을 사용할 수 있습니다:

- **📖 통합 API 문서**: `http://your-server-ip:8000/docs`
- **📊 서비스 상태**: `http://your-server-ip:8000/api/v1/services/status`
- **🤔 질문 생성**: `http://your-server-ip:8001/docs`
- **🏪 장소 추천**: `http://your-server-ip:8002/docs`
- **💬 텍스트 AI**: `http://your-server-ip:8003/docs`

---

## 🎉 완료!

이제 커플 앱 API Gateway 시스템이 서버에서 실행 중입니다.
SSH 연결을 끊어도 백그라운드에서 지속적으로 실행됩니다.
