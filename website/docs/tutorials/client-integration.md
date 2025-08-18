---
sidebar_position: 3
---

# 클라이언트 연동

Python 클라이언트를 사용하여 LLM 추론 서비스와 연동하는 방법을 학습합니다.

## 🎯 학습 목표

- LLM 클라이언트 설치 및 설정
- 단일 요청 및 배치 처리
- 성능 벤치마킹
- 오류 처리 및 재시도 로직

## 📋 사전 요구사항

- [LLM 추론 서비스 구축](llm-inference-setup.md) 완료
- Python 3.8+ 설치
- 기본적인 Python 지식

## 🚀 1. 클라이언트 설치

### 프로젝트 클론

```bash
# 프로젝트 클론 (또는 기존 디렉토리 사용)
git clone https://github.com/hunhoon21/llm-inference-lab.git
cd llm-inference-lab/client
```

### 의존성 설치

```bash
# 가상환경 생성 (권장)
python3 -m venv client-env
source client-env/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

## 🔧 2. 클라이언트 설정

### 서버 IP 확인

```bash
# GPU 인스턴스의 외부 IP 확인
EXTERNAL_IP=$(gcloud compute instances describe llm-inference-server \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "LLM Server IP: $EXTERNAL_IP"
```

### 연결 테스트

```bash
# 서버 상태 확인
curl http://$EXTERNAL_IP:8000/health

# 간단한 생성 테스트
curl -X POST "http://$EXTERNAL_IP:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Hello, world!",
       "max_tokens": 20
     }'
```

## 💻 3. 단일 요청 테스트

### 기본 사용법

```bash
# 단일 프롬프트 테스트
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --single \
    --prompt "Explain what is machine learning in simple terms"

# 파라미터 조정
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --single \
    --prompt "Write a short story about AI" \
    --max-tokens 200 \
    --temperature 0.8
```

### 프롬프트 파일 사용

```bash
# example_prompts.txt 파일의 첫 번째 프롬프트 사용
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --single \
    --input example_prompts.txt \
    --line 1
```

## 📦 4. 배치 처리

### 여러 프롬프트 처리

```bash
# 배치 처리 실행
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --batch \
    --input example_prompts.txt \
    --output results.csv \
    --concurrent 2
```

### JSON 형식 입력

```bash
# JSON 프롬프트 파일 사용
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --batch \
    --input example_prompts.json \
    --output results_json.csv \
    --concurrent 3
```

### 결과 확인

```bash
# CSV 결과 파일 확인
cat results.csv

# 특정 열만 확인
cut -d',' -f1,2,3 results.csv | head -5
```

## 📊 5. 성능 벤치마킹

### 기본 벤치마크

```bash
# 10개 요청으로 성능 측정
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --benchmark \
    --requests 10 \
    --concurrent 2 \
    --prompt "Write a short paragraph about artificial intelligence"
```

### 상세 벤치마크

```bash
# 더 많은 요청으로 정확한 측정
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --benchmark \
    --requests 50 \
    --concurrent 5 \
    --max-tokens 100 \
    --prompt "Explain the benefits of cloud computing"
```

### 결과 해석

벤치마크 결과에서 확인할 수 있는 지표들:

- **평균 지연시간**: 요청당 평균 응답 시간
- **처리량 (RPS)**: 초당 요청 처리 수
- **토큰 생성률 (TPS)**: 초당 토큰 생성 수
- **오류율**: 실패한 요청의 비율

## 🔄 6. 고급 사용법

### 스트리밍 응답 (미구현 시)

현재 서버가 스트리밍을 지원하지 않는 경우, 이를 추가하는 방법:

```python
# 서버 측 스트리밍 추가 예시
@app.post("/generate_stream")
async def generate_stream(request: GenerateRequest):
    # 스트리밍 로직 구현
    pass
```

### 사용자 정의 프롬프트

```bash
# 대화형 모드 (구현 시)
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --interactive
```

### 오류 처리 및 재시도

클라이언트는 자동으로 다음 상황을 처리합니다:

- 네트워크 타임아웃
- 서버 오류 (5xx)
- 연결 실패

```bash
# 타임아웃 설정
python llm_client.py \
    --base-url "http://$EXTERNAL_IP:8000" \
    --single \
    --prompt "Long complex prompt..." \
    --timeout 60
```

## 📈 7. 성능 최적화

### 동시 요청 수 조정

```bash
# 서버 성능에 따라 동시 요청 수 조정
# GPU 메모리가 충분한 경우
python llm_client.py --concurrent 8

# GPU 메모리가 부족한 경우  
python llm_client.py --concurrent 2
```

### 배치 크기 최적화

```bash
# 작은 배치로 테스트
python llm_client.py \
    --batch \
    --input example_prompts.txt \
    --concurrent 1 \
    --max-tokens 50

# 성능이 좋으면 점진적으로 증가
python llm_client.py \
    --batch \
    --input example_prompts.txt \
    --concurrent 4 \
    --max-tokens 100
```

## 🐛 8. 문제 해결

### 연결 문제

```bash
# 서버 상태 확인
curl http://$EXTERNAL_IP:8000/health

# 방화벽 확인
gcloud compute firewall-rules list | grep llm
```

### 성능 문제

```bash
# GPU 메모리 확인 (서버에서)
nvidia-smi

# 서버 로그 확인
tail -f vllm_server.log
```

### 타임아웃 문제

```bash
# 더 긴 타임아웃 설정
python llm_client.py \
    --timeout 120 \
    --max-tokens 500
```

## 📊 9. 결과 분석

### CSV 결과 파일 구조

```csv
prompt,response,latency,tokens_generated,timestamp,error
"Hello","Hi there!",1.23,3,"2025-08-17T...",
```

### 성능 분석

```bash
# 평균 지연시간 계산
awk -F',' 'NR>1 {sum+=$3; count++} END {print "Average latency:", sum/count}' results.csv

# 성공률 계산
awk -F',' 'NR>1 {total++; if($6=="") success++} END {print "Success rate:", success/total*100"%"}' results.csv
```

## ✅ 완료 체크리스트

- [ ] 클라이언트 설치 및 설정
- [ ] 서버 연결 테스트 성공
- [ ] 단일 요청 테스트 성공
- [ ] 배치 처리 테스트 성공
- [ ] 성능 벤치마크 실행
- [ ] 결과 분석 완료

## 🔄 다음 단계

클라이언트 연동이 완료되었습니다! 이제 다음 주제들을 탐색해보세요:

- [GPU 관리](../guides/gpu-management.md)
- [비용 최적화](../guides/cost-optimization.md)
- [문제 해결](../guides/troubleshooting.md)

---

:::tip 팁
실제 운영 환경에서는 API 키 인증, 로드 밸런싱, 모니터링 등을 추가로 고려해야 합니다!
:::