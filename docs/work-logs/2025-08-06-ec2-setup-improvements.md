# 2025-08-06: EC2 LLM 설정 가이드 개선 및 실용성 보강

## 📋 오늘의 목표
어제 작성한 EC2 LLM 설정 가이드를 검토하고, 실제 환경에서 유용한 세부사항들을 추가하여 실용성을 높이기

## 🔧 AWS 인프라 설정 보강

### 1. EC2 인스턴스 타입 비교 분석

**상세 인스턴스 비교표**
| 인스턴스 타입 | GPU | GPU 메모리 | vCPU | 메모리 | 시간당 비용 | 적합한 모델 크기 |
|--------------|-----|-----------|------|--------|-------------|----------------|
| g5.xlarge    | A10G | 24GB      | 4    | 16GB   | $1.006      | 7B~13B |
| g5.2xlarge   | A10G | 24GB      | 8    | 32GB   | $1.212      | 13B~30B |
| g4dn.xlarge  | T4   | 16GB      | 4    | 16GB   | $0.526      | 3B~7B |
| p3.2xlarge   | V100 | 16GB      | 8    | 61GB   | $3.06       | 7B~13B (고성능) |

**인스턴스 선택 가이드**
```bash
# 개발/테스트 용도 (비용 우선)
# g4dn.xlarge 추천 - Llama3-7B는 양자화 필요

# 일반 운영 용도 (균형)
# g5.xlarge 추천 - 24GB GPU 메모리로 여유있음

# 고성능 추론 용도 (성능 우선)  
# p3.2xlarge 추천 - V100의 높은 연산 성능
```

### 2. 비용 최적화 전략 구체화

**스팟 인스턴스 활용**
```bash
# 스팟 가격 확인
aws ec2 describe-spot-price-history \
  --instance-types g5.xlarge \
  --product-descriptions "Linux/UNIX" \
  --max-items 5

# 스팟 인스턴스 요청
aws ec2 request-spot-instances \
  --spot-price "0.30" \
  --instance-count 1 \
  --type "persistent" \
  --launch-specification file://spot-specification.json

# spot-specification.json 예시
{
  "ImageId": "ami-0c02fb55956c7d316",
  "KeyName": "llm-inference-key",
  "SecurityGroups": ["llm-inference-sg"],
  "InstanceType": "g5.xlarge",
  "Placement": {
    "AvailabilityZone": "us-east-1a"
  },
  "BlockDeviceMappings": [
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 50,
        "VolumeType": "gp3",
        "DeleteOnTermination": true
      }
    }
  ]
}
```

**자동 시작/중지 스케줄링**
```bash
# CloudWatch Events를 통한 자동화
# 평일 9시 시작, 18시 중지로 약 60% 비용 절약

# 시작 스케줄 (월-금 9:00 KST)
aws events put-rule \
  --name "start-llm-server" \
  --schedule-expression "cron(0 0 ? * MON-FRI *)"

# 중지 스케줄 (월-금 18:00 KST)  
aws events put-rule \
  --name "stop-llm-server" \
  --schedule-expression "cron(0 9 ? * MON-FRI *)"
```

### 3. 네트워크 및 보안 강화

**VPC 기반 설정 (프로덕션 환경)**
```bash
# VPC 생성
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' \
  --output text)

# 퍼블릭 서브넷 생성
SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' \
  --output text)

# 인터넷 게이트웨이 생성 및 연결
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

aws ec2 attach-internet-gateway \
  --vpc-id $VPC_ID \
  --internet-gateway-id $IGW_ID

# 라우트 테이블 설정
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' \
  --output text)

aws ec2 create-route \
  --route-table-id $ROUTE_TABLE_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

aws ec2 associate-route-table \
  --subnet-id $SUBNET_ID \
  --route-table-id $ROUTE_TABLE_ID
```

**개선된 보안 그룹**
```bash
# 보안 그룹 생성 (VPC 기반)
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
  --group-name llm-inference-sg \
  --description "Enhanced security group for LLM service" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

# SSH 접근 (특정 IP만 허용)
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 22 \
  --cidr <YOUR_IP>/32

# API 접근 (필요한 경우만)
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 10.0.0.0/16  # VPC 내부에서만 접근

# HTTPS 접근 (ALB 사용 시)
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

## 🚀 서버 환경 구축 개선사항

### 1. 자동화 설치 스크립트

**완전 자동화된 설치 스크립트**
```bash
#!/bin/bash
# setup-llm-server.sh - 원클릭 설치 스크립트

set -euo pipefail  # 엄격한 에러 처리

# 색상 출력을 위한 함수
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 인수 파싱
MODEL_NAME=${1:-"meta-llama/Meta-Llama-3-8B"}
GPU_MEMORY_UTILIZATION=${2:-0.8}
MAX_MODEL_LEN=${3:-4096}

log_info "Installing LLM Inference Server"
log_info "Model: $MODEL_NAME"
log_info "GPU Memory Utilization: $GPU_MEMORY_UTILIZATION"
log_info "Max Model Length: $MAX_MODEL_LEN"

# 1. 시스템 정보 수집
log_info "Collecting system information..."
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(arch)"

# 2. NVIDIA 드라이버 확인
if ! command -v nvidia-smi &> /dev/null; then
    log_error "NVIDIA drivers not found!"
    log_info "Installing NVIDIA drivers..."
    sudo apt update
    sudo apt install -y nvidia-driver-535
    log_warn "Please reboot the system and run this script again"
    exit 1
fi

log_info "NVIDIA Driver version: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader)"

# 3. 시스템 패키지 업데이트
log_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 4. 필수 패키지 설치
log_info "Installing essential packages..."
sudo apt install -y htop nvtop git curl wget python3-pip python3-venv \
                    software-properties-common apt-transport-https ca-certificates

# 5. Python 가상환경 설정
log_info "Setting up Python virtual environment..."
python3 -m venv vllm-env
source vllm-env/bin/activate

# 6. Python 패키지 설치
log_info "Installing Python packages..."
pip install --upgrade pip setuptools wheel

# CUDA 버전 확인 후 PyTorch 설치
CUDA_VERSION=$(nvidia-smi | grep -o 'CUDA Version: [0-9.]*' | cut -d' ' -f3 | cut -d'.' -f1,2)
log_info "Detected CUDA version: $CUDA_VERSION"

if [[ $CUDA_VERSION == "11.8" ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
elif [[ $CUDA_VERSION == "12.1" ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    log_warn "Unsupported CUDA version. Installing CPU version of PyTorch"
    pip install torch torchvision torchaudio
fi

# vLLM 및 의존성 설치
pip install vllm transformers accelerate huggingface_hub

# 7. HuggingFace 토큰 확인
if [ -z "${HF_TOKEN:-}" ]; then
    log_warn "HF_TOKEN environment variable not set"
    read -p "Enter your HuggingFace token (or press Enter to skip): " token
    if [ -n "$token" ]; then
        echo "export HF_TOKEN='$token'" >> ~/.bashrc
        export HF_TOKEN="$token"
    fi
fi

# 8. 서비스 스크립트 생성
log_info "Creating service scripts..."

cat > start-llm-server.sh << EOF
#!/bin/bash
source vllm-env/bin/activate
python -m vllm.entrypoints.openai.api_server \\
  --model $MODEL_NAME \\
  --host 0.0.0.0 \\
  --port 8000 \\
  --gpu-memory-utilization $GPU_MEMORY_UTILIZATION \\
  --max-model-len $MAX_MODEL_LEN \\
  --disable-log-requests \\
  --served-model-name llama3-8b
EOF

chmod +x start-llm-server.sh

cat > stop-llm-server.sh << 'EOF'
#!/bin/bash
pkill -f "vllm.entrypoints.openai.api_server"
echo "LLM server stopped"
EOF

chmod +x stop-llm-server.sh

# 9. Systemd 서비스 생성 (선택사항)
cat > llm-inference.service << EOF
[Unit]
Description=LLM Inference Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME
ExecStart=$HOME/start-llm-server.sh
ExecStop=$HOME/stop-llm-server.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

log_info "To install as system service, run:"
log_info "sudo cp llm-inference.service /etc/systemd/system/"
log_info "sudo systemctl enable llm-inference.service"

# 10. 방화벽 설정
log_info "Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
echo "y" | sudo ufw enable || true

# 11. 설치 완료
log_info "Installation completed successfully!"
log_info "To start the server: ./start-llm-server.sh"
log_info "To stop the server: ./stop-llm-server.sh"
log_info "To test the API: curl http://localhost:8000/v1/models"

# 12. 시스템 정보 출력
log_info "System Summary:"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
echo "GPU Memory: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader)"
echo "Python: $(python --version)"
echo "PyTorch: $(python -c 'import torch; print(torch.__version__)')"
echo "CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available())')"
```

### 2. 환경별 설정 템플릿

**개발 환경 설정**
```bash
# dev-config.sh
export MODEL_NAME="meta-llama/Meta-Llama-3-8B"
export GPU_MEMORY_UTILIZATION="0.7"
export MAX_MODEL_LEN="2048"
export LOG_LEVEL="INFO"
export DISABLE_LOG_REQUESTS="true"

# 개발용 추가 파라미터
export TENSOR_PARALLEL_SIZE="1"
export PIPELINE_PARALLEL_SIZE="1"
export QUANTIZATION="awq"  # 메모리 절약
```

**프로덕션 환경 설정**
```bash
# prod-config.sh
export MODEL_NAME="meta-llama/Meta-Llama-3-8B"
export GPU_MEMORY_UTILIZATION="0.9"
export MAX_MODEL_LEN="4096"
export LOG_LEVEL="WARNING"
export DISABLE_LOG_REQUESTS="true"

# 프로덕션 최적화 파라미터
export TENSOR_PARALLEL_SIZE="1"
export PIPELINE_PARALLEL_SIZE="1"
export ENGINE_USE_RAY="true"
export SWAP_SPACE="4"
```

## 🤖 Llama3-7B 모델 최적화

### 1. 모델 다운로드 최적화

**대역폭 최적화 다운로드**
```bash
# 병렬 다운로드로 속도 향상
export HF_HUB_DOWNLOAD_MAX_WORKERS=4

# 재시작 가능한 다운로드
huggingface-cli download meta-llama/Meta-Llama-3-8B \
  --cache-dir ./models \
  --resume-download \
  --local-dir-use-symlinks False

# 다운로드 진행률 확인
du -sh ~/.cache/huggingface/hub/
```

**모델 파일 구조 이해**
```bash
# 모델 구성 요소 확인
ls -la ~/.cache/huggingface/hub/models--meta-llama--Meta-Llama-3-8B/snapshots/*/

# 주요 파일들:
# - pytorch_model-*.bin (모델 가중치)
# - config.json (모델 설정)
# - tokenizer.json (토크나이저)
# - generation_config.json (생성 설정)
```

### 2. 메모리 사용량 최적화

**동적 배치 크기 조절**
```python
# memory_optimizer.py
import torch
import psutil
from vllm import LLM

def get_optimal_batch_size():
    """시스템 리소스 기반으로 최적 배치 크기 결정"""
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
    system_memory = psutil.virtual_memory().total / (1024**3)  # GB
    
    if gpu_memory >= 24:
        return 64
    elif gpu_memory >= 16:
        return 32
    elif gpu_memory >= 12:
        return 16
    else:
        return 8

def get_optimal_model_len():
    """GPU 메모리 기반으로 최적 모델 길이 결정"""
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    
    if gpu_memory >= 24:
        return 8192
    elif gpu_memory >= 16:
        return 4096
    elif gpu_memory >= 12:
        return 2048
    else:
        return 1024

print(f"Recommended batch size: {get_optimal_batch_size()}")
print(f"Recommended max model length: {get_optimal_model_len()}")
```

## 🔥 vLLM 서비스 고급 설정

### 1. 다중 모델 서빙

**모델 서빙 설정**
```bash
# 여러 모델을 동시에 서빙
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B \
  --model microsoft/DialoGPT-medium \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.8
```

### 2. 로드밸런싱 및 고가용성

**Nginx 로드밸런서 설정**
```nginx
# /etc/nginx/sites-available/llm-inference
upstream llm_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001 backup;
}

server {
    listen 80;
    server_name your-domain.com;

    location /v1/ {
        proxy_pass http://llm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 3. API 응답 캐싱

**Redis 기반 캐싱**
```python
# api_cache.py
import redis
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_key(prompt, model, **kwargs):
    """캐시 키 생성"""
    data = {'prompt': prompt, 'model': model, **kwargs}
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

def get_cached_response(prompt, model, **kwargs):
    """캐시된 응답 조회"""
    key = cache_key(prompt, model, **kwargs)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None

def cache_response(prompt, model, response, ttl=3600, **kwargs):
    """응답 캐싱 (1시간 TTL)"""
    key = cache_key(prompt, model, **kwargs)
    redis_client.setex(key, ttl, json.dumps(response))
```

## 📊 고급 모니터링 및 알림

### 1. Prometheus 메트릭 수집

**커스텀 메트릭 수집기**
```python
# metrics_collector.py
from prometheus_client import start_http_server, Summary, Counter, Gauge
import time
import nvidia_ml_py3 as nvml
import psutil

# 메트릭 정의
REQUEST_TIME = Summary('llm_request_processing_seconds', 'Time spent processing LLM requests')
REQUEST_COUNT = Counter('llm_requests_total', 'Total LLM requests')
GPU_UTILIZATION = Gauge('gpu_utilization_percent', 'GPU utilization percentage')
GPU_MEMORY_USED = Gauge('gpu_memory_used_mb', 'GPU memory used in MB')

def collect_gpu_metrics():
    """GPU 메트릭 수집"""
    nvml.nvmlInit()
    handle = nvml.nvmlDeviceGetHandleByIndex(0)
    
    # GPU 사용률
    utilization = nvml.nvmlDeviceGetUtilizationRates(handle)
    GPU_UTILIZATION.set(utilization.gpu)
    
    # GPU 메모리
    memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
    GPU_MEMORY_USED.set(memory_info.used / 1024 / 1024)  # MB

if __name__ == '__main__':
    start_http_server(9090)
    while True:
        collect_gpu_metrics()
        time.sleep(10)
```

### 2. 로그 분석 및 알림

**로그 파싱 및 이상 탐지**
```python
# log_analyzer.py
import re
import smtplib
from email.mime.text import MimeText
from collections import defaultdict, deque
from datetime import datetime, timedelta

class LogAnalyzer:
    def __init__(self):
        self.error_count = defaultdict(int)
        self.recent_errors = deque(maxlen=100)
        self.last_alert = {}
    
    def parse_log_line(self, line):
        """로그 라인 파싱"""
        patterns = {
            'error': r'ERROR.*',
            'warning': r'WARNING.*',
            'memory_error': r'CUDA out of memory',
            'timeout': r'Request timeout'
        }
        
        for error_type, pattern in patterns.items():
            if re.search(pattern, line):
                self.error_count[error_type] += 1
                self.recent_errors.append({
                    'type': error_type,
                    'message': line,
                    'timestamp': datetime.now()
                })
                
                # 임계치 초과 시 알림
                if self.should_alert(error_type):
                    self.send_alert(error_type, line)
    
    def should_alert(self, error_type):
        """알림 발송 여부 결정"""
        thresholds = {
            'error': 10,
            'memory_error': 1,
            'timeout': 5
        }
        
        threshold = thresholds.get(error_type, 5)
        recent_count = sum(1 for e in self.recent_errors 
                          if e['type'] == error_type and 
                          e['timestamp'] > datetime.now() - timedelta(minutes=5))
        
        return recent_count >= threshold
    
    def send_alert(self, error_type, message):
        """이메일 알림 발송"""
        # 구현 생략
        pass
```

## 🧪 API 테스트 고도화

### 1. 성능 벤치마킹 도구

**멀티스레드 부하 테스트**
```python
# load_test.py
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import argparse

async def send_request(session, prompt, semaphore):
    """단일 요청 전송"""
    async with semaphore:
        try:
            start_time = time.time()
            async with session.post('http://localhost:8000/v1/completions',
                                  json={
                                      'model': 'meta-llama/Meta-Llama-3-8B',
                                      'prompt': prompt,
                                      'max_tokens': 100,
                                      'temperature': 0.7
                                  }) as response:
                result = await response.json()
                end_time = time.time()
                return {
                    'latency': end_time - start_time,
                    'status': response.status,
                    'tokens': len(result.get('choices', [{}])[0].get('text', '').split())
                }
        except Exception as e:
            return {'error': str(e)}

async def run_load_test(concurrent_requests=10, total_requests=100):
    """부하 테스트 실행"""
    semaphore = asyncio.Semaphore(concurrent_requests)
    connector = aiohttp.TCPConnector(limit=concurrent_requests*2)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        prompts = [f"Write a story about {i}" for i in range(total_requests)]
        
        start_time = time.time()
        tasks = [send_request(session, prompt, semaphore) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # 결과 분석
        successful_results = [r for r in results if isinstance(r, dict) and 'latency' in r]
        error_count = len(results) - len(successful_results)
        
        if successful_results:
            latencies = [r['latency'] for r in successful_results]
            tokens_per_request = [r['tokens'] for r in successful_results]
            
            print(f"=== Load Test Results ===")
            print(f"Total requests: {total_requests}")
            print(f"Concurrent requests: {concurrent_requests}")
            print(f"Successful requests: {len(successful_results)}")
            print(f"Failed requests: {error_count}")
            print(f"Total time: {end_time - start_time:.2f}s")
            print(f"Requests per second: {len(successful_results)/(end_time - start_time):.2f}")
            print(f"Average latency: {statistics.mean(latencies):.2f}s")
            print(f"95th percentile latency: {statistics.quantiles(latencies, n=20)[18]:.2f}s")
            print(f"Average tokens per request: {statistics.mean(tokens_per_request):.1f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--concurrent', type=int, default=10)
    parser.add_argument('--total', type=int, default=100)
    args = parser.parse_args()
    
    asyncio.run(run_load_test(args.concurrent, args.total))
```

### 2. API 응답 품질 테스트

**응답 품질 자동 평가**
```python
# quality_test.py
import openai
from textstat import flesch_reading_ease
import re

def evaluate_response_quality(prompt, response):
    """응답 품질 평가"""
    metrics = {}
    
    # 1. 길이 적절성
    metrics['length'] = len(response.split())
    metrics['length_score'] = 1.0 if 50 <= metrics['length'] <= 200 else 0.5
    
    # 2. 가독성 점수
    metrics['readability'] = flesch_reading_ease(response)
    metrics['readability_score'] = 1.0 if metrics['readability'] > 60 else 0.5
    
    # 3. 반복성 체크
    words = response.split()
    unique_words = set(words)
    metrics['repetition_ratio'] = len(unique_words) / len(words) if words else 0
    metrics['repetition_score'] = 1.0 if metrics['repetition_ratio'] > 0.7 else 0.5
    
    # 4. 관련성 (간단한 키워드 매칭)
    prompt_words = set(prompt.lower().split())
    response_words = set(response.lower().split())
    common_words = prompt_words.intersection(response_words)
    metrics['relevance_ratio'] = len(common_words) / len(prompt_words) if prompt_words else 0
    metrics['relevance_score'] = 1.0 if metrics['relevance_ratio'] > 0.3 else 0.5
    
    # 전체 품질 점수
    metrics['overall_score'] = (
        metrics['length_score'] + 
        metrics['readability_score'] + 
        metrics['repetition_score'] + 
        metrics['relevance_score']
    ) / 4
    
    return metrics

# 테스트 실행
test_prompts = [
    "Explain artificial intelligence in simple terms",
    "Write a short story about a robot",
    "What are the benefits of renewable energy?"
]

for prompt in test_prompts:
    # API 호출 (실제 구현 필요)
    response = "Sample response text here..."
    quality = evaluate_response_quality(prompt, response)
    print(f"Prompt: {prompt}")
    print(f"Quality Score: {quality['overall_score']:.2f}")
    print("---")
```

## 📝 오늘의 성과
- [x] EC2 인스턴스 타입별 상세 비교 분석 완료
- [x] 스팟 인스턴스 활용한 비용 최적화 방안 수립
- [x] VPC 기반 네트워크 보안 강화 방안 제시
- [x] 완전 자동화된 설치 스크립트 작성
- [x] 환경별 설정 템플릿 제공
- [x] 고급 모니터링 및 알림 시스템 설계
- [x] 성능 벤치마킹 및 품질 테스트 도구 개발
- [x] 멀티모델 서빙 및 로드밸런싱 방안 제시

## 🔄 다음 단계 (2025-08-07 계획)
1. **실제 환경 테스트**: 개선된 스크립트로 EC2 환경 구축
2. **성능 벤치마킹**: 다양한 설정에 대한 성능 비교 실험
3. **클라이언트 애플리케이션 개발**: Python/JavaScript 클라이언트 구현
4. **운영 환경 준비**: 모니터링, 로깅, 알림 시스템 구축
5. **문서화**: 운영 매뉴얼 및 트러블슈팅 가이드 작성

## 💡 주요 개선 사항
- **실용성**: 완전 자동화된 설치 프로세스
- **안정성**: 에러 처리 및 복구 매커니즘 강화
- **확장성**: 멀티 모델 서빙 및 로드밸런싱 지원
- **모니터링**: Prometheus 기반 메트릭 수집
- **품질 관리**: 자동화된 응답 품질 평가
- **비용 효율성**: 스팟 인스턴스 및 스케줄링 활용
