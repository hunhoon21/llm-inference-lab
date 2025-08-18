---
sidebar_position: 2
---

# 비용 최적화

LLM 추론 서비스 운영 비용을 효과적으로 관리하고 최적화하는 방법을 다룹니다.

## 💰 비용 구조 이해

### 주요 비용 요소

1. **GPU 인스턴스**: 전체 비용의 80-90%
2. **스토리지**: 모델 저장 및 로그
3. **네트워크**: 데이터 송신
4. **부가 서비스**: 로드밸런서, 모니터링

### 시간대별 비용 (GCP 기준)

| 리소스 | 시간당 비용 | 월 비용 (24/7) |
|--------|-------------|----------------|
| T4 GPU | $0.35 | ~$250 |
| L4 GPU | $0.60 | ~$430 |
| 스토리지 (100GB) | $0.004 | ~$3 |

## 🎯 비용 절약 전략

### 1. 적시 스케일링

```bash
# 업무 시간에만 운영
# 오전 9시 시작
gcloud compute instances start llm-inference-server --zone=us-central1-a

# 오후 6시 중지
gcloud compute instances stop llm-inference-server --zone=us-central1-a
```

### 2. Preemptible 인스턴스

```bash
# 70% 할인된 Preemptible 인스턴스 사용
gcloud compute instances create llm-server-spot \
    --preemptible \
    --accelerator=type=nvidia-l4,count=1 \
    --maintenance-policy=TERMINATE
```

**주의사항**: 24시간 이내 강제 종료될 수 있음

### 3. 적절한 GPU 선택

```
개발/테스트: T4 GPU (70% 절약)
프로덕션: L4 GPU (성능/비용 균형)
대규모: A100 GPU (높은 처리량 필요시만)
```

## 📊 모니터링 및 알림

### 예산 설정

1. [GCP 예산 관리](https://console.cloud.google.com/billing/budgets)
2. 월 예산 설정 (예: $100)
3. 알림 임계값: 50%, 90%, 100%

### 비용 추적

```bash
# 현재 월 사용량 확인
gcloud billing accounts describe BILLING_ACCOUNT_ID

# 리소스별 비용 확인
gcloud compute instances list --format="table(name,zone,status,machineType)"
```

## 🔧 자동화 스크립트

### 자동 중지 스크립트

```bash
#!/bin/bash
# cost_optimizer.sh

# 비활성 시간 체크 (5분)
IDLE_THRESHOLD=300

# API 요청 로그 체크
LAST_REQUEST=$(grep "POST /generate" /var/log/nginx/access.log | tail -1 | awk '{print $4}' | tr -d '[')

if [ -n "$LAST_REQUEST" ]; then
    CURRENT_TIME=$(date +%s)
    LAST_TIME=$(date -d "$LAST_REQUEST" +%s)
    IDLE_TIME=$((CURRENT_TIME - LAST_TIME))
    
    if [ $IDLE_TIME -gt $IDLE_THRESHOLD ]; then
        echo "Stopping instance due to inactivity"
        gcloud compute instances stop $(hostname) --zone=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google" | cut -d/ -f4)
    fi
fi
```

### 스케줄링 설정

```bash
# crontab 설정
# 매일 오후 6시 중지
0 18 * * * /path/to/stop_instance.sh

# 매일 오전 9시 시작 (Cloud Scheduler 사용 권장)
0 9 * * * gcloud compute instances start llm-inference-server --zone=us-central1-a
```

## 💡 최적화 팁

### 모델 선택

- **작은 모델 우선**: 7B 모델로 시작
- **성능 확인 후 스케일업**: 필요시에만 큰 모델 사용
- **특화 모델**: 용도에 맞는 모델 선택

### 하드웨어 최적화

```python
# 메모리 효율적인 설정
LLM(
    model="model-name",
    dtype="half",                    # FP16 사용 (메모리 50% 절약)
    gpu_memory_utilization=0.85,     # 메모리 사용률 최적화
    max_model_len=1024,              # 필요한 만큼만 컨텍스트 길이 설정
)
```

## 📈 ROI 계산

### 비용 대비 성능 측정

```
처리량 (요청/시간) ÷ 시간당 비용 = 비용 효율성

예시:
- T4: 100 요청/시간 ÷ $0.35 = 285.7 요청/$
- L4: 200 요청/시간 ÷ $0.60 = 333.3 요청/$
```

## 🎯 권장 설정

### 개발 환경

```
- GPU: T4
- 운영 시간: 8시간/일
- Preemptible: 사용
- 예상 비용: $70-100/월
```

### 프로덕션 환경

```
- GPU: L4
- 운영 시간: 24시간/일
- Preemptible: 미사용 (안정성 우선)
- 예상 비용: $400-500/월
```

더 자세한 비용 최적화 전략은 추후 업데이트 예정입니다.