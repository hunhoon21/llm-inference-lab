---
sidebar_position: 1
---

# GCP 기본 환경 구축

GCP에서 LLM 추론 서비스를 위한 기본 환경을 구축하는 방법을 알아봅니다.

## 🎯 학습 목표

이 튜토리얼을 완료하면 다음을 할 수 있습니다:
- GCP 프로젝트 생성 및 설정
- gCloud CLI 설치 및 구성
- 기본 Compute Engine 인스턴스 생성
- SSH 접속 및 방화벽 설정
- 외부에서 인스턴스 접근 테스트

## 📋 사전 요구사항

- Google 계정
- 결제 정보 등록 (무료 크레딧 $300 제공)
- 기본적인 터미널 사용법

## 🚀 1. GCP 프로젝트 설정

### 프로젝트 생성

1. [GCP 콘솔](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 → `llm-inference-lab`
3. 프로젝트 ID 확인: `llm-inference-lab-[숫자]`

### 결제 계정 연결

:::warning 중요
API 활성화를 위해서는 **활성화된 결제 계정**이 필요합니다!
:::

```bash
# 결제 계정 확인
gcloud billing accounts list

# 결제 계정이 없는 경우:
# 1. https://console.cloud.google.com/billing 접속
# 2. "결제 계정 만들기" 클릭  
# 3. 신용카드 등록 (무료 크레딧 $300 제공)

# 프로젝트에 결제 계정 연결 확인
PROJECT_ID="your-project-id"  # 실제 프로젝트 ID로 변경
gcloud billing projects describe $PROJECT_ID
```

## 🛠️ 2. gCloud CLI 설치

### macOS 설치

```bash
# gCloud CLI 다운로드 및 설치
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 대화형 설정 가이드

설치 중 나타나는 질문들에 대한 권장 답변:

```
질문: "Modify profile to update your $PATH and enable shell command completion?"
권장: Y (PATH 자동 설정)

질문: "Do you want to help improve the Google Cloud CLI?"  
선택: Y/N (개인 선호에 따라)

질문: "Do you want to configure a default Compute Region and Zone?"
권장: Y, 그 후 us-central1-a 선택

질문: "Do you want to authenticate with your Google account now?"
권장: Y (바로 인증 진행)
```

### 인증 및 프로젝트 설정

```bash
# Google 계정 인증
gcloud auth login

# 프로젝트 설정
PROJECT_ID="llm-inference-lab-123456"  # 실제 프로젝트 ID로 변경
gcloud config set project $PROJECT_ID

# 설정 확인
gcloud config list
```

## ⚡ 3. 필수 API 활성화

```bash
# Compute Engine API 활성화
gcloud services enable compute.googleapis.com

# 활성화 확인
gcloud services list --enabled
```

## 🌐 4. 네트워크 및 보안 설정

### 방화벽 규칙 생성

```bash
# SSH 접근 허용 (기본으로 이미 있을 수 있음)
gcloud compute firewall-rules create allow-ssh \
    --allow tcp:22 \
    --source-ranges 0.0.0.0/0 \
    --description="Allow SSH access"

# HTTP 테스트용 포트 허용
gcloud compute firewall-rules create allow-http-8000 \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags test-server \
    --description="Allow HTTP access for testing"
```

### SSH 키 준비

```bash
# SSH 키 생성 (없는 경우)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gcp-key

# 키 권한 설정
chmod 400 ~/.ssh/gcp-key

# 공개 키 확인
cat ~/.ssh/gcp-key.pub
```

## 💻 5. 테스트 인스턴스 생성

### 기본 인스턴스 생성

```bash
# 현재 사용 가능한 이미지 확인
gcloud compute images list \
    --project=ubuntu-os-cloud \
    --filter="family:ubuntu-2204-lts" \
    --limit=5

# 인스턴스 생성
gcloud compute instances create test-server \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --tags=test-server

# 인스턴스 목록 확인  
gcloud compute instances list
```

## 🔗 6. SSH 접속 및 테스트

### SSH 접속

```bash
# gCloud를 이용한 SSH 접속 (키 파일 지정)
gcloud compute ssh test-server \
    --zone=us-central1-a \
    --ssh-key-file ~/.ssh/gcp-key

# 또는 외부 IP로 직접 접속
EXTERNAL_IP=$(gcloud compute instances describe test-server \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "External IP: $EXTERNAL_IP"

ssh -i ~/.ssh/gcp-key $(whoami)@$EXTERNAL_IP
```

### 인스턴스 내부에서 HTTP 서버 테스트

인스턴스에 접속한 후 다음 명령어 실행:

```bash
# 시스템 업데이트
sudo apt update

# Python 설치 확인
python3 --version

# 간단한 HTTP 서버 실행
python3 -m http.server 8000
```

### 외부에서 접근 테스트

로컬 터미널에서:

```bash
# HTTP 접근 테스트
curl http://$EXTERNAL_IP:8000

# 브라우저에서도 접근 가능
# http://EXTERNAL_IP:8000
```

## 📊 7. 상태 확인

### 리소스 상태 확인

```bash
# 인스턴스 상태
gcloud compute instances list

# 방화벽 규칙 확인  
gcloud compute firewall-rules list

# 프로젝트 정보
gcloud compute project-info describe

# 현재 설정 확인
gcloud config list
```

### 예상 비용

```
기본 인스턴스 비용 (e2-medium):
- 인스턴스: ~$0.02/시간
- 스토리지: ~$0.003/시간
- 네트워크: 송신 트래픽 기준

월 예상 비용: ~$15-20 (24시간 운영 시)
```

## 🧹 8. 리소스 정리

테스트 완료 후 비용 절약을 위해:

```bash
# 인스턴스 중지 (과금 중단, 디스크 비용은 유지)
gcloud compute instances stop test-server --zone=us-central1-a

# 인스턴스 완전 삭제
gcloud compute instances delete test-server --zone=us-central1-a

# 방화벽 규칙 삭제 (선택사항)
gcloud compute firewall-rules delete allow-http-8000
```

## ✅ 완료 체크리스트

- [ ] GCP 프로젝트 생성 및 결제 계정 연결
- [ ] gCloud CLI 설치 및 인증
- [ ] 필수 API 활성화
- [ ] 방화벽 규칙 설정
- [ ] SSH 키 생성 및 설정
- [ ] 테스트 인스턴스 생성
- [ ] SSH 접속 성공
- [ ] 외부에서 HTTP 서버 접근 성공

## 🔄 다음 단계

기본 환경 구축이 완료되었습니다! 이제 [LLM 추론 서비스 구축](llm-inference-setup.md)으로 넘어가세요.

## 💡 문제 해결

### 자주 발생하는 문제들

**Q: SSH 접속이 안 됩니다**
```bash
# 방화벽 규칙 확인
gcloud compute firewall-rules list | grep ssh

# SSH 키 권한 확인
ls -la ~/.ssh/gcp-key  # 권한이 400인지 확인
```

**Q: HTTP 서버에 접근할 수 없습니다**
```bash
# 방화벽 규칙 확인
gcloud compute firewall-rules describe allow-http-8000

# 인스턴스 태그 확인
gcloud compute instances describe test-server --zone=us-central1-a | grep tags
```

**Q: API 활성화가 안 됩니다**
- 결제 계정이 연결되어 있는지 확인
- 프로젝트 권한이 충분한지 확인

---

:::tip 팁
실제 개발할 때는 인스턴스를 항상 켜둘 필요가 없습니다. 필요할 때만 시작하고 사용 후에는 중지하여 비용을 절약하세요!
:::