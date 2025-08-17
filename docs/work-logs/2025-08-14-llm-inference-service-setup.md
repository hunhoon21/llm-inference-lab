# 2025-08-14: GCP에서 LLM 추론 서비스 구축

## 📋 오늘의 목표
GCP Compute Engine에 GPU 인스턴스를 생성하고 vLLM을 사용하여 LLM 추론 서비스를 구축, 기존 클라이언트와 연동 테스트

## 🎯 프로젝트 현황
- **이전 단계**: GCP 기본 환경 구축 완료 (2025-08-11)
- **현재 목표**: 실제 LLM 추론 서비스 구축
- **최종 목표**: 안정적인 추론 API 서비스 및 클라이언트 연동

## 🏗️ 아키텍처 설계

### 시스템 구성도
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local Client  │    │  GCP Compute    │    │   Model Hub     │
│                 │    │   (GPU)         │    │  (HuggingFace)  │
│ • llm_client.py │───▶│ • vLLM Server   │◀───│ • Llama Models  │
│ • Batch Test    │    │ • FastAPI       │    │ • Mistral       │
│ • Performance   │    │ • NVIDIA GPU    │    │ • CodeLlama     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 핵심 구성요소
- **GPU 인스턴스**: NVIDIA L4/T4 GPU가 포함된 Compute Engine
- **vLLM 서버**: 고성능 LLM 추론 엔진
- **FastAPI**: RESTful API 인터페이스
- **모델**: HuggingFace에서 다운로드한 오픈소스 LLM
- **클라이언트**: 기존 개발된 Python 클라이언트

## 🚀 GPU 인스턴스 설정

### 1. GPU 할당량 요청
```bash
# 현재 할당량 확인
gcloud compute project-info describe --project=$PROJECT_ID

# GPU 할당량 요청 (웹 콘솔에서 수행)
# 1. https://console.cloud.google.com/iam-admin/quotas 접속
# 2. "Compute Engine API" 필터
# 3. "GPUs (all regions)" 검색
# 4. 요청할 GPU 유형과 수량 선택:
#    - NVIDIA_L4: 1개 (권장)
#    - NVIDIA_T4: 1개 (대안)
# 5. 증가 요청 제출
```

#### 💡 GPU 할당량 승인 팁
```
승인 과정:
- 일반적으로 24-48시간 소요
- 신규 계정의 경우 더 오래 걸릴 수 있음
- 요청 사유에 "머신러닝 연구/개발" 명시
- 예상 사용 시간과 목적 구체적으로 기술
```

### 2. Deep Learning VM 이미지 확인
```bash
# 사용 가능한 Deep Learning VM 이미지 조회
gcloud compute images list \
    --project=deeplearning-platform-release \
    --filter="family:pytorch-latest-gpu" \
    --limit=5

# PyTorch + CUDA가 사전 설치된 이미지 선택
IMAGE_FAMILY="pytorch-latest-gpu"
IMAGE_PROJECT="deeplearning-platform-release"
```

### 3. GPU 인스턴스 생성
```bash
# L4 GPU 인스턴스 생성 (권장)
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

# 대안: T4 GPU 인스턴스 (비용 절약)
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

### 4. 방화벽 규칙 설정
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

## 🤖 vLLM 설치 및 구성

### 1. 인스턴스 접속 및 환경 확인
```bash
# GPU 인스턴스에 SSH 접속
gcloud compute ssh llm-inference-server --zone=us-central1-a

# GPU 확인
nvidia-smi

# Python 환경 확인
python3 --version
pip3 --version

# CUDA 확인
nvcc --version
```

### 2. vLLM 설치
```bash
# 인스턴스 내부에서 실행
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

### 3. 간단한 vLLM 서버 구축
```bash
# 서버 스크립트 생성
cat > vllm_server.py << 'EOF'
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
EOF

chmod +x vllm_server.py
```

### 4. 서버 실행 및 테스트
```bash
# 백그라운드에서 서버 실행
nohup python vllm_server.py > vllm_server.log 2>&1 &

# 서버 상태 확인
sleep 30  # 모델 로딩 대기
curl http://localhost:8000/health

# 간단한 추론 테스트
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "The future of AI is",
       "max_tokens": 50,
       "temperature": 0.7
     }'
```

## 🔗 클라이언트 연동 및 테스트

### 1. 외부 IP 확인 및 클라이언트 설정
```bash
# 로컬 머신에서 실행
# GPU 인스턴스의 외부 IP 확인
EXTERNAL_IP=$(gcloud compute instances describe llm-inference-server \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "LLM Server IP: $EXTERNAL_IP"
```

### 2. 기존 클라이언트로 연동 테스트
```bash
# 로컬 머신에서 기존 클라이언트 사용
cd client/

# 서버 URL 업데이트
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --single \
    --prompt "Explain machine learning in simple terms"

# 배치 테스트 실행
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --batch \
    --input example_prompts.txt \
    --output results.csv \
    --concurrent 2
```

### 3. 성능 벤치마크
```bash
# 대기시간 및 처리량 측정
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --benchmark \
    --requests 10 \
    --concurrent 3 \
    --prompt "Write a short story about AI"

# 결과 분석
# - 평균 대기시간
# - 초당 요청 처리량 (RPS)
# - 초당 토큰 생성량 (TPS)
```

## 📊 모니터링 및 최적화

### 1. GPU 사용률 모니터링
```bash
# GPU 인스턴스에서 실행
# 실시간 GPU 사용률 확인
watch -n 1 nvidia-smi

# 메모리 사용량 추적
while true; do
    echo "$(date): $(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits)"
    sleep 5
done > gpu_memory.log
```

### 2. vLLM 성능 튜닝
```python
# vllm_server.py에서 최적화 옵션
llm = LLM(
    model=model_name,
    tensor_parallel_size=1,
    dtype="half",           # 메모리 절약
    max_model_len=2048,     # 최대 시퀀스 길이 제한
    gpu_memory_utilization=0.8,  # GPU 메모리 사용률 조정
    swap_space=4,           # 스왑 공간 (GB)
)
```

### 3. 서버 안정성 향상
```bash
# Systemd 서비스 생성 (자동 재시작)
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

## 🧪 다양한 모델 테스트

### 1. 모델 변경 및 테스트
```python
# 다른 모델들 테스트해보기
models_to_test = [
    "microsoft/DialoGPT-medium",      # 대화형 (가벼움)
    "microsoft/DialoGPT-large",       # 대화형 (더 큰 모델)
    "codellama/CodeLlama-7b-hf",      # 코드 생성 (7B)
    "mistralai/Mistral-7B-v0.1",      # 일반 용도 (7B)
]
```

### 2. 모델별 성능 비교
```bash
# 각 모델의 메모리 사용량 및 속도 측정
# 1. 모델 변경
# 2. 서버 재시작
# 3. 동일한 프롬프트로 벤치마크
# 4. 결과 비교 분석
```

## 💰 비용 최적화

### 1. 인스턴스 관리
```bash
# 사용하지 않을 때 인스턴스 중지
gcloud compute instances stop llm-inference-server --zone=us-central1-a

# 필요할 때 다시 시작
gcloud compute instances start llm-inference-server --zone=us-central1-a

# 완전 삭제 (주의!)
gcloud compute instances delete llm-inference-server --zone=us-central1-a
```

### 2. 예상 비용 (월 기준)
```
GPU 인스턴스 비용 (24시간 운영):
- L4 GPU + g2-standard-4: ~$400-500/월
- T4 GPU + n1-standard-4: ~$300-400/월

비용 절약 팁:
- 사용하지 않을 때 인스턴스 중지
- Preemptible 인스턴스 사용 (50-70% 할인)
- Spot 인스턴스 활용
- 적절한 GPU 타입 선택
```

## 🧹 리소스 정리

### 개발 완료 후 정리
```bash
# 서버 중지
gcloud compute instances stop llm-inference-server --zone=us-central1-a

# 방화벽 규칙 삭제
gcloud compute firewall-rules delete allow-llm-api
gcloud compute firewall-rules delete allow-llm-monitoring

# 인스턴스 삭제 (선택)
gcloud compute instances delete llm-inference-server --zone=us-central1-a
```

## 📝 오늘의 성과
- [ ] GPU 할당량 요청 및 승인 대기
- [ ] Deep Learning VM 기반 GPU 인스턴스 생성
- [ ] vLLM 설치 및 기본 설정 완료
- [ ] FastAPI 기반 추론 서버 구축
- [ ] 외부 접근을 위한 방화벽 설정
- [ ] 기존 클라이언트와 연동 테스트
- [ ] 성능 벤치마크 및 모니터링 설정
- [ ] 서버 안정성 및 자동 재시작 구성

## 🔄 다음 단계
1. **고급 모델 테스트**
   - Llama 2/3 모델 로드
   - Code Llama, Mistral 등 특화 모델
   - 모델별 성능 비교

2. **프로덕션 최적화**
   - 로드 밸런싱 구성
   - 캐싱 레이어 추가
   - API 키 인증 구현

3. **모니터링 고도화**
   - Prometheus + Grafana 연동
   - 알림 시스템 구축
   - 로그 수집 및 분석

## 💡 오늘 배운 점
- GPU 할당량 요청이 사전에 필요함
- Deep Learning VM이 환경 구축에 매우 유용
- vLLM이 추론 성능 최적화에 효과적
- GPU 메모리 관리가 모델 선택의 핵심
- 비용 관리를 위한 인스턴스 제어가 중요

## ⚠️ 주의사항
- GPU 할당량 승인까지 24-48시간 소요
- GPU 인스턴스는 높은 비용 발생 (시간당 $1-2)
- 사용하지 않을 때 반드시 인스턴스 중지
- 큰 모델일수록 GPU 메모리 요구량 증가
- 방화벽 설정 시 보안 고려사항 확인