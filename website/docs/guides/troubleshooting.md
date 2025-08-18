---
sidebar_position: 3
---

# 문제 해결

LLM 추론 서비스 운영 중 발생할 수 있는 주요 문제들과 해결 방법입니다.

## 🚨 자주 발생하는 문제

### 1. GPU 할당량 문제

**증상**: `Quota exceeded` 오류

**해결법**:
- [GCP 할당량 페이지](https://console.cloud.google.com/iam-admin/quotas)에서 GPU 할당량 요청
- 구체적인 사유 작성 (연구/개발 목적)

### 2. SSH 접속 실패

**증상**: 연결 거부

**해결법**:
```bash
# 방화벽 규칙 확인
gcloud compute firewall-rules list | grep ssh

# SSH 키 권한 확인
chmod 400 ~/.ssh/gcp-key
```

### 3. vLLM 메모리 부족

**증상**: `CUDA out of memory`

**해결법**:
```python
# 메모리 사용량 줄이기
LLM(
    model="model-name",
    dtype="half",                    # FP16 사용
    gpu_memory_utilization=0.7,      # 메모리 사용률 줄이기
    max_model_len=1024,              # 컨텍스트 길이 줄이기
)
```

### 4. API 접근 불가

**증상**: 외부에서 API 호출 실패

**해결법**:
```bash
# 방화벽 확인
gcloud compute firewall-rules describe allow-llm-api

# 인스턴스 태그 확인
gcloud compute instances describe llm-inference-server \
    --zone=us-central1-a \
    --format="value(tags.items)"
```

## 🔧 빠른 해결책

### 서버 재시작

```bash
# 서버 프로세스 종료
pkill -f vllm_server.py

# 서버 재시작
nohup python vllm_server.py > vllm_server.log 2>&1 &
```

### 로그 확인

```bash
# 서버 로그
tail -f vllm_server.log

# GPU 상태
nvidia-smi

# API 테스트
curl http://localhost:8000/health
```

더 자세한 문제 해결 방법은 [GitHub Issues](https://github.com/hunhoon21/llm-inference-lab/issues)에서 확인하세요.