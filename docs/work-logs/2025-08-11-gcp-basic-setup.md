# 2025-08-11: GCP 기본 환경 구축 및 연결 테스트

## 📋 오늘의 목표
AWS 계정 문제로 인해 GCP로 전환, 기본 인스턴스를 띄우고 외부에서 접근 가능한지 확인

## 🔄 마이그레이션 배경
- **기존 환경**: AWS EC2 기반
- **변경 사유**: AWS 계정 관련 이슈
- **새 환경**: GCP Compute Engine
- **오늘 목표**: 기본 연결 테스트까지만

## 🏗️ GCP 기본 개념

### AWS vs GCP 핵심 용어
| 개념 | AWS | GCP |
|------|-----|-----|
| 가상머신 | EC2 Instance | Compute Engine |
| 네트워크 | VPC | VPC Network |
| 방화벽 | Security Group | Firewall Rules |
| SSH 키 | Key Pair | SSH Keys |

## 🚀 GCP 초기 설정

### 1. 프로젝트 생성
```
1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성 → "llm-inference-lab"
3. 결제 계정 연결
4. 프로젝트 ID 확인: llm-inference-lab-[숫자]
```

### 2. gCloud CLI 설치
```bash
# macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 인증 및 프로젝트 설정
gcloud auth login
PROJECT_ID="llm-inference-lab-123456"  # 실제 프로젝트 ID로 변경
gcloud config set project $PROJECT_ID
```

### 3. 필수 API 활성화
```bash
gcloud services enable compute.googleapis.com
```

## 💻 기본 인스턴스 생성

### 1. 방화벽 규칙 설정
```bash
# SSH 접근 허용
gcloud compute firewall-rules create allow-ssh \
    --allow tcp:22 \
    --source-ranges 0.0.0.0/0

# HTTP 서버 테스트용 포트 허용
gcloud compute firewall-rules create allow-http-8000 \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags test-server
```

### 2. SSH 키 준비
```bash
# SSH 키 생성 (없는 경우)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gcp-key

# 공개 키 내용 확인
cat ~/.ssh/gcp-key.pub
```

### 3. 인스턴스 생성
```bash
# 기본 인스턴스 생성
gcloud compute instances create test-server \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --tags=test-server

# 인스턴스 목록 확인
gcloud compute instances list
```

### 4. SSH 접속 테스트
```bash
# gcloud를 이용한 SSH 접속
gcloud compute ssh test-server --zone=us-central1-a

# 또는 외부 IP로 직접 접속
EXTERNAL_IP=$(gcloud compute instances describe test-server \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "External IP: $EXTERNAL_IP"

# SSH 접속 (사용자명은 gcloud 계정명과 동일)
ssh -i ~/.ssh/gcp-key username@$EXTERNAL_IP
```

## 🧪 연결 테스트

### 1. 인스턴스 내부에서 간단한 HTTP 서버 실행
```bash
# 인스턴스에 SSH 접속 후
sudo apt update
sudo apt install -y python3

# 간단한 HTTP 서버 실행
python3 -m http.server 8000
```

### 2. 외부에서 접근 테스트
```bash
# 로컬 머신에서 테스트
curl http://$EXTERNAL_IP:8000

# 브라우저에서 접근
# http://EXTERNAL_IP:8000
```

### 3. 기본 시스템 정보 확인
```bash
# 인스턴스 내부에서 실행
echo "=== System Information ==="
uname -a
lscpu | grep "Model name"
free -h
df -h
```

## 📊 상태 확인 명령어

### GCP 리소스 상태 확인
```bash
# 인스턴스 상태
gcloud compute instances list

# 방화벽 규칙 확인
gcloud compute firewall-rules list

# 프로젝트 정보 확인
gcloud compute project-info describe

# 현재 설정 확인
gcloud config list
```

### 비용 확인
```bash
# 대략적인 비용 (e2-medium 기준)
# - 인스턴스: ~$0.03/hr
# - 스토리지: ~$0.004/hr  
# - 네트워크: 송신 트래픽 기준 과금
# 총 예상: ~$25/월 (24시간 운영시)
```

## 🧹 리소스 정리

### 테스트 완료 후 정리
```bash
# 인스턴스 중지 (과금 중단)
gcloud compute instances stop test-server --zone=us-central1-a

# 인스턴스 완전 삭제
gcloud compute instances delete test-server --zone=us-central1-a

# 방화벽 규칙 삭제 (선택사항)
gcloud compute firewall-rules delete allow-http-8000
```

## 📝 오늘의 성과
- [x] GCP 프로젝트 생성 및 CLI 설정
- [x] 기본 방화벽 규칙 구성
- [x] 테스트용 인스턴스 생성
- [x] SSH 접속 확인
- [x] 외부에서 HTTP 서버 접근 테스트
- [x] 기본 시스템 정보 확인
- [x] 리소스 정리 방법 정리

## 🔄 다음 단계
1. **GPU 인스턴스 생성**
   - GPU 할당량 요청
   - L4 또는 T4 GPU 인스턴스 테스트

2. **LLM 환경 구축**
   - Deep Learning VM 사용
   - vLLM 설치 및 모델 로딩

3. **클라이언트 연동**
   - 기존 클라이언트 코드 수정
   - API 엔드포인트 변경

## 💡 오늘 배운 점
- GCP CLI 사용법이 AWS CLI와 유사하지만 구조가 다름
- 방화벽 규칙이 태그 기반으로 적용됨
- SSH 키 관리 방식이 AWS와 다름
- 기본 인스턴스 생성이 간단하고 직관적임

## ⚠️ 주의사항
- 인스턴스 사용하지 않을 때는 반드시 중지
- 방화벽 규칙 생성시 소스 IP 범위 주의
- SSH 키 파일 권한 관리 중요 (`chmod 400`)
- 프로젝트 ID는 전역적으로 고유해야 함