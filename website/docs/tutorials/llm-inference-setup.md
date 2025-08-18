---
sidebar_position: 2
---

# LLM 추론 서비스 구축

GPU 인스턴스에 vLLM을 설치하고 LLM 추론 서비스를 구축하는 방법을 학습합니다.

## 🎯 학습 목표

- GPU 할당량 요청 및 승인
- GPU 인스턴스 생성 및 설정
- vLLM 설치 및 구성
- FastAPI 기반 추론 서버 구축
- 외부에서 API 접근 테스트

## 📋 사전 요구사항

- [GCP 기본 환경 구축](gcp-basic-setup.md) 완료
- 기본적인 Python 지식
- Linux 명령어 사용법

## 🚀 1. GPU 할당량 요청

### 할당량 현황 확인

```bash
# 현재 할당량 확인
gcloud compute project-info describe --project=$PROJECT_ID
```

### GPU 할당량 요청

1. [할당량 페이지](https://console.cloud.google.com/iam-admin/quotas) 접속
2. "Compute Engine API" 필터 적용
3. "GPUs (all regions)" 검색
4. NVIDIA L4 또는 T4 GPU 선택
5. 할당량 증가 요청

### 🏆 빠른 승인을 위한 사유 작성법

:::tip 1분 내 승인받은 실제 사유
```
We are requesting additional GPU quota (NVIDIA L4) to support our Large Language Model (LLM) research and development.
The GPU resources will be used for model inference, benchmarking, and fine-tuning experiments in a controlled environment.
This is part of our ongoing R&D project to evaluate performance and scalability of LLMs on Google Cloud infrastructure.
```

**핵심 요소:**
- 구체적인 기술 용도 명시
- 연구/개발 목적 강조  
- 전문적이고 명확한 영문 작성
- GCP 인프라 활용 의지 표현
:::

## 🖥️ 2. GPU 인스턴스 생성

### Deep Learning VM 이미지 확인

```bash
# 사용 가능한 PyTorch 이미지 조회
gcloud compute images list \
    --project=deeplearning-platform-release \
    --filter="family:pytorch*" \
    --limit=10

# 최신 이미지 선택 (2025년 8월 기준)
IMAGE_FAMILY="pytorch-2-7-cu128-ubuntu-2204-nvidia-570"
IMAGE_PROJECT="deeplearning-platform-release"
```

### GPU 인스턴스 생성

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
<TabItem value="l4" label="L4 GPU (권장)">

```bash
# L4 GPU 인스턴스 생성
gcloud compute instances create llm-inference-server \
    --zone=us-central1-a \
    --machine-type=g2-standard-4 \
    --accelerator=type=nvidia-l4,count=1 \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=100GB \
    --boot-disk-type=pd-ssd \
    --maintenance-policy=TERMINATE \
    --restart-on-failure \
    --tags=llm-server
```

</TabItem>
<TabItem value="t4" label="T4 GPU (비용 절약)">

```bash
# T4 GPU 인스턴스 생성
gcloud compute instances create llm-inference-server \
    --zone=us-central1-f \
    --machine-type=n1-standard-4 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=100GB \
    --boot-disk-type=pd-ssd \
    --maintenance-policy=TERMINATE \
    --restart-on-failure \
    --tags=llm-server
```

</TabItem>
</Tabs>

### 방화벽 설정

```bash
# LLM API 서버용 포트 개방
gcloud compute firewall-rules create allow-llm-api \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags llm-server \
    --description="Allow LLM inference API access"

# 모니터링용 포트 (선택사항)
gcloud compute firewall-rules create allow-llm-monitoring \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --target-tags llm-server \
    --description="Allow LLM monitoring dashboard"
```

## 🤖 3. vLLM 설치 및 설정

### 인스턴스 접속

```bash
# GPU 인스턴스에 SSH 접속
gcloud compute ssh llm-inference-server \
    --zone=us-central1-a \
    --ssh-key-file ~/.ssh/gcp-key
```

### 환경 확인

```bash
# GPU 확인
nvidia-smi

# Python 환경 확인
python3 --version
pip3 --version

# CUDA 확인
nvcc --version
```

### vLLM 설치

```bash
# Python 가상환경 생성
python3 -m venv vllm-env
source vllm-env/bin/activate

# vLLM 설치 (CUDA 지원)
pip install vllm

# 의존성 패키지 설치
pip install fastapi uvicorn[standard] requests

# 설치 확인
python -c "import vllm; print(vllm.__version__)"
```

## 📡 4. FastAPI 서버 구축

### 서버 스크립트 생성

```python title="vllm_server.py"
#!/usr/bin/env python3
"""
vLLM FastAPI 서버
HuggingFace 모델을 로드하여 추론 API 제공
"""

import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vllm import LLM, SamplingParams
from typing import List, Optional
import uvicorn
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Inference API", version="1.0.0")

# 전역 변수
llm = None
model_name = "microsoft/DialoGPT-medium"  # 가벼운 모델로 시작

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 0.9
    stop: Optional[List[str]] = None

class GenerateResponse(BaseModel):
    text: str
    prompt: str
    model: str

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드"""
    global llm, model_name
    try:
        logger.info(f"Loading model: {model_name}")
        llm = LLM(
            model=model_name,
            tensor_parallel_size=1,  # GPU 1개 사용
            dtype="half",  # 메모리 절약
        )
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "LLM Inference API is running", "model": model_name}

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "model_loaded": llm is not None}

@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """텍스트 생성 API"""
    if llm is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # 샘플링 파라미터 설정
        sampling_params = SamplingParams(
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            stop=request.stop
        )
        
        # 추론 실행
        outputs = llm.generate([request.prompt], sampling_params)
        generated_text = outputs[0].outputs[0].text
        
        return GenerateResponse(
            text=generated_text,
            prompt=request.prompt,
            model=model_name
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```

### 서버 실행

```bash
# 백그라운드에서 서버 실행
nohup python vllm_server.py > vllm_server.log 2>&1 &

# 서버 상태 확인 (모델 로딩 대기)
sleep 30
curl http://localhost:8000/health
```

## 🧪 5. API 테스트

### 로컬 테스트

```bash
# 헬스 체크
curl http://localhost:8000/

# 텍스트 생성 테스트
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "The future of AI is",
       "max_tokens": 50,
       "temperature": 0.7
     }'
```

### 외부에서 접근 테스트

```bash
# 로컬 머신에서 실행
# GPU 인스턴스의 외부 IP 확인
EXTERNAL_IP=$(gcloud compute instances describe llm-inference-server \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "LLM Server IP: $EXTERNAL_IP"

# 외부에서 API 호출
curl -X POST "http://$EXTERNAL_IP:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Explain machine learning in simple terms",
       "max_tokens": 100
     }'
```

## 📊 6. 성능 모니터링

### GPU 사용률 확인

```bash
# 실시간 GPU 모니터링
watch -n 1 nvidia-smi

# 메모리 사용량 로깅
while true; do
    echo "$(date): $(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits)"
    sleep 5
done > gpu_memory.log
```

### 서버 로그 확인

```bash
# 서버 로그 실시간 확인
tail -f vllm_server.log

# 오류 로그 검색
grep -i error vllm_server.log
```

## 🔧 7. 성능 최적화

### vLLM 튜닝 옵션

```python
# 최적화된 설정 예시
llm = LLM(
    model=model_name,
    tensor_parallel_size=1,
    dtype="half",                    # 메모리 절약
    max_model_len=2048,             # 최대 시퀀스 길이 제한
    gpu_memory_utilization=0.8,     # GPU 메모리 사용률 조정
    swap_space=4,                   # 스왑 공간 (GB)
)
```

### 서비스 자동 재시작

```bash
# Systemd 서비스 생성
sudo tee /etc/systemd/system/vllm-server.service << EOF
[Unit]
Description=vLLM Inference Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER
Environment=PATH=/home/$USER/vllm-env/bin
ExecStart=/home/$USER/vllm-env/bin/python /home/$USER/vllm_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl enable vllm-server
sudo systemctl start vllm-server
sudo systemctl status vllm-server
```

## 💰 8. 비용 관리

### 예상 비용 (월 기준)

```
GPU 인스턴스 비용 (24시간 운영):
- L4 GPU + g2-standard-4: ~$400-500/월
- T4 GPU + n1-standard-4: ~$300-400/월

비용 절약 팁:
- 사용하지 않을 때 인스턴스 중지
- Preemptible 인스턴스 사용 (50-70% 할인)
- 적절한 GPU 타입 선택
```

### 리소스 정리

```bash
# 인스턴스 중지 (과금 중단)
gcloud compute instances stop llm-inference-server --zone=us-central1-a

# 인스턴스 삭제
gcloud compute instances delete llm-inference-server --zone=us-central1-a

# 방화벽 규칙 삭제
gcloud compute firewall-rules delete allow-llm-api
gcloud compute firewall-rules delete allow-llm-monitoring
```

## ✅ 완료 체크리스트

- [ ] GPU 할당량 승인
- [ ] GPU 인스턴스 생성
- [ ] vLLM 설치
- [ ] FastAPI 서버 구축
- [ ] 로컬 API 테스트 성공
- [ ] 외부 API 접근 성공
- [ ] 성능 모니터링 설정

## 🔄 다음 단계

LLM 추론 서비스 구축이 완료되었습니다! 이제 [클라이언트 연동](client-integration.md)으로 넘어가세요.

---

:::warning 주의사항
GPU 인스턴스는 높은 비용이 발생합니다. 사용하지 않을 때는 반드시 중지하세요!
:::