# 2025-08-05: EC2에 LLM 추론 서비스 구축

## 📋 오늘의 목표
EC2 인스턴스에 Llama3-7B + vLLM 조합으로 LLM 추론 서비스를 구축하고, HTTP API를 통해 추론 요청을 처리할 수 있는 환경 완성

## 🔧 AWS 인프라 설정

### 1. EC2 인스턴스 설정
**인스턴스 타입 선택**
- **추천**: `g5.xlarge` (NVIDIA A10G GPU, 4 vCPU, 16GB RAM)
  - 비용: ~$1.006/시간
  - Llama3-7B에 적합한 16GB GPU 메모리
- **대안**: `g5.2xlarge` (24GB GPU 메모리) - 더 여유있지만 비용 2배

**AMI 선택**
```bash
# Deep Learning AMI (Ubuntu 20.04) 사용 - CUDA/Python 환경 사전 구성
# AMI ID: ami-0c02fb55956c7d316 (us-east-1 기준)
```

**스토리지 설정**
- EBS 볼륨: 50GB (gp3)
  - Llama3-7B 모델: ~13GB
  - vLLM + 의존성: ~10GB
  - 시스템 + 여유공간: ~27GB

### 2. 보안 그룹 설정
```bash
# 보안 그룹 생성
aws ec2 create-security-group \
  --group-name llm-inference-sg \
  --description "Security group for LLM inference service"

# SSH 접근 허용 (22번 포트)
aws ec2 authorize-security-group-ingress \
  --group-name llm-inference-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# vLLM API 접근 허용 (8000번 포트)
aws ec2 authorize-security-group-ingress \
  --group-name llm-inference-sg \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

### 3. 키 페어 생성
```bash
# 키 페어 생성
aws ec2 create-key-pair \
  --key-name llm-inference-key \
  --query 'KeyMaterial' \
  --output text > llm-inference-key.pem

# 권한 설정
chmod 400 llm-inference-key.pem
```

### 4. EC2 인스턴스 시작
```bash
# 인스턴스 실행
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --count 1 \
  --instance-type g5.xlarge \
  --key-name llm-inference-key \
  --security-groups llm-inference-sg \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=llm-inference-server}]'
```

## 🚀 서버 환경 구축

### 1. EC2 인스턴스 접속
```bash
# 퍼블릭 IP 확인 후 접속
ssh -i llm-inference-key.pem ubuntu@<PUBLIC_IP>
```

### 2. 시스템 업데이트 및 기본 설정
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y htop nvtop git curl wget

# NVIDIA 드라이버 확인
nvidia-smi
```

### 3. Python 환경 설정
```bash
# Conda 환경 생성 (이미 설치된 환경 활용)
conda create -n vllm python=3.10 -y
conda activate vllm

# 또는 venv 사용
python3.10 -m venv vllm-env
source vllm-env/bin/activate
```

### 4. vLLM 설치
```bash
# CUDA 11.8 버전용 PyTorch 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# vLLM 설치
pip install vllm

# 추가 의존성
pip install transformers accelerate
```

## 🤖 Llama3-7B 모델 준비

### 1. HuggingFace 토큰 설정
```bash
# HuggingFace CLI 설치
pip install huggingface_hub

# 토큰 설정 (https://huggingface.co/settings/tokens 에서 발급)
huggingface-cli login
# 또는 환경변수로 설정
export HF_TOKEN="your_token_here"
```

### 2. 모델 다운로드 (선택사항)
```bash
# 모델 사전 다운로드 (vLLM이 자동으로 다운로드하므로 선택사항)
huggingface-cli download meta-llama/Meta-Llama-3-8B --cache-dir ./models
```

## 🔥 vLLM 서비스 실행

### 1. vLLM 서버 시작
```bash
# 기본 설정으로 서버 시작
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.8 \
  --max-model-len 4096

# 백그라운드 실행 (선택사항)
nohup python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.8 \
  --max-model-len 4096 > vllm.log 2>&1 &
```

### 2. 서비스 상태 확인
```bash
# 프로세스 확인
ps aux | grep vllm

# GPU 사용량 확인
nvidia-smi

# 포트 확인
netstat -tlnp | grep 8000

# API 테스트
curl http://localhost:8000/v1/models
```

## 🧪 API 테스트

### 1. 로컬 테스트
```bash
# 완성도 테스트
curl -X POST "http://localhost:8000/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3-8B",
    "prompt": "The capital of France is",
    "max_tokens": 50,
    "temperature": 0.7
  }'
```

### 2. 외부 접근 테스트
```bash
# 로컬 머신에서 테스트
curl -X POST "http://<EC2_PUBLIC_IP>:8000/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3-8B",
    "prompt": "Hello, how are you?",
    "max_tokens": 100
  }'
```

## 📊 모니터링 설정

### 1. 시스템 리소스 모니터링
```bash
# 실시간 모니터링 스크립트 생성
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    echo "GPU Usage:"
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
    echo "CPU/Memory:"
    top -bn1 | grep "Cpu(s)" | head -1
    free -h | grep Mem
    echo "Disk Usage:"
    df -h / | tail -1
    echo "vLLM Process:"
    ps aux | grep vllm | grep -v grep
    echo "========================"
    sleep 60
done
EOF

chmod +x monitor.sh
# 백그라운드 실행
./monitor.sh > monitoring.log 2>&1 &
```

### 2. 로그 수집
```bash
# 로그 디렉토리 생성
mkdir -p ~/logs

# vLLM 로그 확인
tail -f vllm.log

# 시스템 로그 확인
tail -f /var/log/syslog
```

## 🎯 성능 튜닝 옵션

### 1. vLLM 최적화 파라미터
```bash
# 메모리 최적화된 실행
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 2048 \
  --swap-space 4 \
  --disable-log-requests
```

### 2. 시스템 최적화
```bash
# GPU 클럭 최적화
sudo nvidia-smi -pm 1
sudo nvidia-smi -ac 1215,1410

# CPU 거버너 설정
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## 🚨 문제 해결

### 자주 발생하는 문제들
1. **CUDA Out of Memory**: `--gpu-memory-utilization` 값을 낮추기 (0.7 → 0.6)
2. **모델 다운로드 실패**: HF_TOKEN 설정 확인, 네트워크 상태 점검
3. **포트 접근 불가**: 보안 그룹 8000번 포트 오픈 확인
4. **vLLM 시작 실패**: CUDA 버전 호환성 확인, PyTorch 재설치

### 디버깅 명령어
```bash
# 상세 로그로 실행
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level debug

# 환경 정보 확인
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Version: {torch.version.cuda}')"
python -c "import vllm; print(f'vLLM version: {vllm.__version__}')"
```

## 📝 오늘의 성과
- [ ] EC2 g5.xlarge 인스턴스 생성 및 설정
- [ ] 보안 그룹 및 네트워크 구성
- [ ] vLLM 환경 설치 및 설정
- [ ] Llama3-7B 모델 로드 및 서비스 시작
- [ ] HTTP API 엔드포인트 테스트 완료
- [ ] 기본 모니터링 환경 구축

## 🔄 다음 단계 (내일 계획)
1. 클라이언트 애플리케이션 개발
2. 성능 벤치마킹 및 최적화
3. 에러 핸들링 및 로깅 개선
4. 비용 분석 및 최적화 방안 검토