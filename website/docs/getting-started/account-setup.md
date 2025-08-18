---
sidebar_position: 2
---

# 계정 설정

클라우드 서비스 계정을 설정하고 필요한 도구들을 설치합니다.

## 🌐 GCP 계정 설정 (권장)

### 1. Google 계정 생성
기존 Google 계정을 사용하거나 새로 생성하세요.

### 2. GCP 콘솔 접속
[https://console.cloud.google.com/](https://console.cloud.google.com/)

### 3. 결제 정보 등록
- 신용카드 정보 입력
- **$300 무료 크레딧** 자동 적용
- 무료 크레딧 소진 전까지는 과금되지 않음

### 4. 프로젝트 생성
- 프로젝트 이름: `llm-inference-lab`
- 프로젝트 ID 기록 (나중에 사용)

## 🛠️ 필수 도구 설치

### gCloud CLI (GCP)
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
<TabItem value="macos" label="macOS">

```bash
# Homebrew로 설치 (권장)
brew install google-cloud-sdk

# 또는 공식 설치 스크립트
curl https://sdk.cloud.google.com | bash
```

</TabItem>
<TabItem value="linux" label="Linux">

```bash
# 공식 설치 스크립트
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

</TabItem>
<TabItem value="windows" label="Windows">

1. [공식 설치 파일](https://cloud.google.com/sdk/docs/install) 다운로드
2. 설치 프로그램 실행
3. PowerShell 또는 CMD에서 `gcloud` 명령어 확인

</TabItem>
</Tabs>

### SSH 키 생성

```bash
# SSH 키 생성
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gcp-key

# 키 권한 설정  
chmod 400 ~/.ssh/gcp-key

# 공개 키 확인
cat ~/.ssh/gcp-key.pub
```

## 🔧 초기 설정

### gCloud 인증

```bash
# Google 계정으로 로그인
gcloud auth login

# 프로젝트 설정
gcloud config set project PROJECT_ID  # 실제 프로젝트 ID로 변경

# 기본 리전/존 설정
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a

# 설정 확인
gcloud config list
```

### 권한 확인

```bash
# 현재 계정 확인
gcloud auth list

# 프로젝트 정보 확인
gcloud projects describe PROJECT_ID

# 활성화된 API 확인
gcloud services list --enabled
```

## 💰 비용 모니터링 설정

### 예산 알림 설정

1. [예산 관리](https://console.cloud.google.com/billing/budgets) 페이지 접속
2. "예산 만들기" 클릭
3. 월 예산: $100 설정
4. 알림 임계값: 50%, 90%, 100% 설정
5. 이메일 알림 활성화

### 비용 추적

```bash
# 현재 사용량 확인
gcloud billing projects describe PROJECT_ID

# 활성 리소스 확인
gcloud compute instances list
gcloud compute disks list
```

## 🔒 보안 설정

### IAM 권한 확인

```bash
# 현재 사용자 권한 확인
gcloud projects get-iam-policy PROJECT_ID

# 필요한 권한:
# - Compute Engine Admin
# - Storage Admin  
# - Service Account User
```

### API 키 관리

```bash
# API 키 생성 (필요한 경우)
gcloud auth application-default login

# 서비스 계정 생성
gcloud iam service-accounts create llm-inference-service \
    --display-name="LLM Inference Service Account"
```

## ✅ 설정 완료 확인

다음 명령어들이 모두 정상 작동하면 설정 완료:

```bash
# gCloud 설정 확인
gcloud config list
gcloud auth list
gcloud projects list

# 권한 확인
gcloud compute zones list
gcloud compute machine-types list --zones=us-central1-a

# SSH 키 확인
ls -la ~/.ssh/gcp-key*
```

## 🆘 문제 해결

### 인증 문제
```bash
# 인증 초기화
gcloud auth revoke --all
gcloud auth login
```

### 권한 문제
- GCP 콘솔에서 IAM 권한 확인
- 프로젝트 소유자/편집자 권한 필요

### API 활성화 문제
- 결제 계정 연결 확인
- 프로젝트 상태 확인

---

설정이 완료되었다면 [GCP 기본 환경 구축](../tutorials/gcp-basic-setup.md) 튜토리얼을 시작하세요!