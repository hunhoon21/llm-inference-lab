---
sidebar_position: 1
---

# GPU 관리

GPU 리소스를 효율적으로 관리하고 최적화하는 방법을 다룹니다.

## 🎯 개요

GPU는 LLM 추론에서 가장 비싼 리소스입니다. 효율적인 관리를 통해 성능을 최대화하고 비용을 최소화할 수 있습니다.

## 📊 GPU 타입 비교

### GCP GPU 옵션

| GPU 타입 | 메모리 | 성능 | 시간당 비용 | 권장 용도 |
|----------|--------|------|-------------|-----------|
| T4 | 16GB | 중간 | ~$0.35 | 개발/테스트 |
| L4 | 24GB | 높음 | ~$0.60 | 프로덕션 |
| A100 | 40GB | 최고 | ~$2.93 | 대규모 모델 |

### 모델별 GPU 메모리 요구사항

- **7B 모델**: 14-16GB (FP16)
- **13B 모델**: 26-30GB  
- **70B 모델**: 140GB+ (여러 GPU 필요)

## 🔧 최적화 전략

### 1. 메모리 최적화

```python
# vLLM 메모리 설정
LLM(
    model="model-name",
    gpu_memory_utilization=0.85,  # GPU 메모리 85% 사용
    dtype="half",                 # FP16 사용
    max_model_len=2048,          # 컨텍스트 길이 제한
)
```

### 2. 배치 처리 최적화

```bash
# 적절한 배치 크기 찾기
# 작게 시작해서 점진적으로 증가
concurrent_requests=1  # 시작값
```

## 💰 비용 관리

### Preemptible 인스턴스 사용

```bash
# 70% 할인 가능한 Preemptible 인스턴스
gcloud compute instances create llm-server-preemptible \
    --preemptible \
    --accelerator=type=nvidia-l4,count=1 \
    # ... 기타 옵션
```

### 자동 중지 스크립트

```bash
#!/bin/bash
# auto_stop.sh - 비활성 시 자동 중지

IDLE_TIME=300  # 5분
while true; do
    # API 요청 체크 로직
    if [ "API가 5분간 비활성" ]; then
        gcloud compute instances stop $(hostname) --zone=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google" | cut -d/ -f4)
        break
    fi
    sleep 60
done
```

## 📈 모니터링

### 실시간 모니터링

```bash
# GPU 사용률 모니터링
watch -n 1 nvidia-smi

# 메모리 사용률 로깅
nvidia-smi --query-gpu=timestamp,memory.used,memory.total --format=csv -l 5
```

### 알림 설정

Cloud Monitoring을 통한 GPU 사용률 알림 설정이 필요한 경우 별도 문서에서 다룹니다.

## 🚀 성능 튜닝

### vLLM 파라미터 최적화

```python
# 고성능 설정
LLM(
    model="model-name",
    tensor_parallel_size=1,           # GPU 수에 맞춤
    pipeline_parallel_size=1,         # 파이프라인 병렬화
    max_num_batched_tokens=8192,      # 배치 토큰 수
    max_num_seqs=256,                 # 최대 시퀀스 수
)
```

더 자세한 내용은 추후 업데이트 예정입니다.