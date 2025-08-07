# LLM 추론 클라이언트

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 1. 단일 프롬프트 테스트
```bash
python llm_client.py --prompt "인공지능에 대해 설명해주세요"
```

### 2. 대화형 모드
```bash
python llm_client.py --interactive
```

### 3. 배치 처리 (파일에서 프롬프트 로드)
```bash
# 텍스트 파일 사용
python llm_client.py --prompt-file example_prompts.txt

# JSON 파일 사용  
python llm_client.py --prompt-file example_prompts.json
```

### 4. 실험 설정
```bash
# 병렬 요청
python llm_client.py --prompt-file example_prompts.txt --concurrent 3

# 반복 실험
python llm_client.py --prompt "안녕하세요" --repeat 5

# 결과 저장
python llm_client.py --prompt-file example_prompts.txt --output results.json
```

### 5. 서버 설정
```bash
# 다른 서버 주소
python llm_client.py --server http://your-server:8000

# 다른 모델
python llm_client.py --model gpt-3.5-turbo

# 생성 파라미터 조정
python llm_client.py --max-tokens 200 --temperature 0.9
```

### 6. 유틸리티
```bash
# 서버 상태 확인
python llm_client.py --check

# 사용 가능한 모델 확인
python llm_client.py --models
```

## 예제 실행

```bash
# 기본 테스트
python llm_client.py --prompt-file example_prompts.txt --output test_results.json

# 성능 테스트
python llm_client.py --prompt "간단한 질문입니다" --repeat 10 --concurrent 3 --output performance.csv
```