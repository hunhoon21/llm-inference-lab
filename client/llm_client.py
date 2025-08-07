#!/usr/bin/env python3
"""
LLM Inference Client
실험 친화적인 CLI 클라이언트로 LLM 추론 서비스와 통신
"""

import json
import requests
import argparse
import sys
import time
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import concurrent.futures
from threading import Lock


@dataclass
class ClientConfig:
    """클라이언트 설정"""
    base_url: str = "http://localhost:8000"
    model_name: str = "meta-llama/Meta-Llama-3-8B"
    max_tokens: int = 100
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class RequestResult:
    """요청 결과"""
    prompt: str
    response: str
    latency: float
    tokens_generated: int
    timestamp: datetime
    error: Optional[str] = None


class LLMClient:
    """LLM 추론 서비스 클라이언트"""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        self.results_lock = Lock()
    
    def health_check(self) -> bool:
        """서버 상태 확인"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            # health 엔드포인트가 없을 수 있으므로 models로 시도
            try:
                response = self.session.get(
                    f"{self.config.base_url}/v1/models",
                    timeout=5
                )
                return response.status_code == 200
            except requests.RequestException:
                return False
    
    def get_models(self) -> Optional[List[str]]:
        """사용 가능한 모델 목록 조회"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/v1/models",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except requests.RequestException as e:
            print(f"Error fetching models: {e}")
            return None
    
    def generate_single(self, prompt: str, **kwargs) -> RequestResult:
        """단일 텍스트 생성 요청"""
        start_time = time.time()
        
        # 기본 파라미터
        params = {
            "model": self.config.model_name,
            "prompt": prompt,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        
        # 추가 파라미터 덮어쓰기
        params.update(kwargs)
        
        try:
            response = self.session.post(
                f"{self.config.base_url}/v1/completions",
                json=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            end_time = time.time()
            latency = end_time - start_time
            
            # 응답 파싱
            if "choices" in data and data["choices"]:
                response_text = data["choices"][0]["text"].strip()
                tokens_generated = len(response_text.split())  # 간단한 토큰 수 계산
            else:
                response_text = ""
                tokens_generated = 0
            
            return RequestResult(
                prompt=prompt,
                response=response_text,
                latency=latency,
                tokens_generated=tokens_generated,
                timestamp=datetime.now()
            )
            
        except requests.RequestException as e:
            end_time = time.time()
            latency = end_time - start_time
            
            return RequestResult(
                prompt=prompt,
                response="",
                latency=latency,
                tokens_generated=0,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def generate_batch(self, prompts: List[str], concurrent: int = 1, **kwargs) -> List[RequestResult]:
        """배치 텍스트 생성 요청"""
        results = []
        
        if concurrent <= 1:
            # 순차 처리
            for i, prompt in enumerate(prompts):
                print(f"Processing {i+1}/{len(prompts)}: {prompt[:50]}...")
                result = self.generate_single(prompt, **kwargs)
                results.append(result)
        else:
            # 병렬 처리
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
                future_to_prompt = {
                    executor.submit(self.generate_single, prompt, **kwargs): prompt 
                    for prompt in prompts
                }
                
                for i, future in enumerate(concurrent.futures.as_completed(future_to_prompt)):
                    print(f"Completed {i+1}/{len(prompts)}")
                    result = future.result()
                    with self.results_lock:
                        results.append(result)
        
        return results


def load_prompts_from_file(file_path: str) -> List[str]:
    """파일에서 프롬프트 로드"""
    path = Path(file_path)
    
    if path.suffix.lower() == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'prompts' in data:
                return data['prompts']
            else:
                raise ValueError("JSON file should contain a list or {'prompts': [...]} structure")
    
    elif path.suffix.lower() == '.txt':
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    
    else:
        raise ValueError("Supported file formats: .json, .txt")


def save_results(results: List[RequestResult], output_path: str) -> None:
    """결과를 파일로 저장"""
    path = Path(output_path)
    
    if path.suffix.lower() == '.json':
        # JSON 형식으로 저장
        data = []
        for result in results:
            result_dict = asdict(result)
            result_dict['timestamp'] = result.timestamp.isoformat()
            data.append(result_dict)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    elif path.suffix.lower() == '.csv':
        # CSV 형식으로 저장
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'prompt', 'response', 'latency', 'tokens_generated', 'error'])
            
            for result in results:
                writer.writerow([
                    result.timestamp.isoformat(),
                    result.prompt,
                    result.response,
                    result.latency,
                    result.tokens_generated,
                    result.error or ""
                ])
    
    else:
        raise ValueError("Supported output formats: .json, .csv")


def print_summary(results: List[RequestResult]) -> None:
    """결과 요약 출력"""
    if not results:
        print("No results to summarize")
        return
    
    successful_results = [r for r in results if r.error is None]
    failed_results = [r for r in results if r.error is not None]
    
    print("\n" + "="*50)
    print("📊 EXPERIMENT SUMMARY")
    print("="*50)
    print(f"Total requests: {len(results)}")
    print(f"Successful: {len(successful_results)}")
    print(f"Failed: {len(failed_results)}")
    
    if successful_results:
        latencies = [r.latency for r in successful_results]
        tokens = [r.tokens_generated for r in successful_results]
        
        print(f"\n⏱️  Latency:")
        print(f"  Average: {sum(latencies)/len(latencies):.2f}s")
        print(f"  Min: {min(latencies):.2f}s")
        print(f"  Max: {max(latencies):.2f}s")
        
        print(f"\n🔤 Tokens:")
        print(f"  Average per request: {sum(tokens)/len(tokens):.1f}")
        print(f"  Total generated: {sum(tokens)}")
        
        total_time = sum(latencies)
        print(f"\n🚀 Performance:")
        print(f"  Requests per second: {len(successful_results)/total_time:.2f}")
        print(f"  Tokens per second: {sum(tokens)/total_time:.1f}")
    
    if failed_results:
        print(f"\n❌ Errors:")
        error_counts = {}
        for result in failed_results:
            error = result.error or "Unknown error"
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in error_counts.items():
            print(f"  {error}: {count}")


def interactive_mode(client: LLMClient) -> None:
    """대화형 모드"""
    print("🚀 LLM Interactive Mode")
    print("Type 'quit' to exit, 'help' for commands")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\n💬 Prompt: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == 'help':
                print("""
Available commands:
- quit/exit/q: Exit interactive mode
- help: Show this help
- config: Show current configuration  
- models: List available models
""")
                continue
            
            elif user_input.lower() == 'config':
                print(f"""
Current Configuration:
  Server: {client.config.base_url}
  Model: {client.config.model_name}
  Max Tokens: {client.config.max_tokens}
  Temperature: {client.config.temperature}
  Timeout: {client.config.timeout}s
""")
                continue
            
            elif user_input.lower() == 'models':
                models = client.get_models()
                if models:
                    print("Available models:")
                    for model in models:
                        print(f"  - {model}")
                else:
                    print("Could not fetch models")
                continue
            
            if not user_input:
                continue
            
            print("🤔 Generating...")
            result = client.generate_single(user_input)
            
            if result.error:
                print(f"❌ Error: {result.error}")
            else:
                print(f"🤖 Response: {result.response}")
                print(f"⏱️  Latency: {result.latency:.2f}s")
                print(f"🔤 Tokens: {result.tokens_generated}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


def main():
    parser = argparse.ArgumentParser(description="LLM Inference Client for Experimentation")
    
    # 서버 설정
    parser.add_argument("--server", default="http://localhost:8000", 
                       help="Server URL")
    parser.add_argument("--model", default="meta-llama/Meta-Llama-3-8B",
                       help="Model name")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Request timeout in seconds")
    
    # 생성 파라미터
    parser.add_argument("--max-tokens", type=int, default=100,
                       help="Maximum tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="Sampling temperature")
    
    # 실행 모드
    parser.add_argument("--prompt", type=str,
                       help="Single prompt to process")
    parser.add_argument("--prompt-file", type=str,
                       help="File containing prompts (.txt or .json)")
    parser.add_argument("--interactive", action="store_true",
                       help="Start interactive mode")
    
    # 실험 설정
    parser.add_argument("--concurrent", type=int, default=1,
                       help="Number of concurrent requests")
    parser.add_argument("--repeat", type=int, default=1,
                       help="Repeat each prompt N times")
    parser.add_argument("--output", type=str,
                       help="Output file for results (.json or .csv)")
    
    # 유틸리티
    parser.add_argument("--check", action="store_true",
                       help="Check server health and exit")
    parser.add_argument("--models", action="store_true",
                       help="List available models and exit")
    
    args = parser.parse_args()
    
    # 설정 생성
    config = ClientConfig(
        base_url=args.server,
        model_name=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        timeout=args.timeout
    )
    
    # 클라이언트 생성
    client = LLMClient(config)
    
    # 유틸리티 커맨드 처리
    if args.check:
        if client.health_check():
            print("✅ Server is healthy")
            sys.exit(0)
        else:
            print("❌ Server is not responding")
            sys.exit(1)
    
    if args.models:
        models = client.get_models()
        if models:
            print("Available models:")
            for model in models:
                print(f"  - {model}")
        else:
            print("Could not fetch models")
        sys.exit(0)
    
    print(f"🔗 Connecting to: {config.base_url}")
    print(f"🤖 Model: {config.model_name}")
    
    # 서버 연결 확인
    if not client.health_check():
        print("⚠️  Warning: Server health check failed. Proceeding anyway...")
    
    # 실행 모드 결정
    if args.interactive:
        interactive_mode(client)
    elif args.prompt:
        # 단일 프롬프트 모드
        prompts = [args.prompt] * args.repeat
        results = client.generate_batch(prompts, args.concurrent)
        
        print_summary(results)
        
        if args.output:
            save_results(results, args.output)
            print(f"💾 Results saved to: {args.output}")
    
    elif args.prompt_file:
        # 파일 기반 배치 모드
        try:
            base_prompts = load_prompts_from_file(args.prompt_file)
            prompts = base_prompts * args.repeat
            
            print(f"📄 Loaded {len(base_prompts)} prompts from {args.prompt_file}")
            if args.repeat > 1:
                print(f"🔄 Each prompt will be repeated {args.repeat} times")
            print(f"📊 Total requests: {len(prompts)}")
            
            results = client.generate_batch(prompts, args.concurrent)
            
            print_summary(results)
            
            if args.output:
                save_results(results, args.output)
                print(f"💾 Results saved to: {args.output}")
            else:
                # 기본 출력 파일명 생성
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_output = f"results_{timestamp}.json"
                save_results(results, default_output)
                print(f"💾 Results saved to: {default_output}")
                
        except Exception as e:
            print(f"❌ Error loading prompts: {e}")
            sys.exit(1)
    
    else:
        # 기본적으로 interactive 모드
        interactive_mode(client)


if __name__ == "__main__":
    main()