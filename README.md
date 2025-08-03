# 🧪 LLM Inference Lab
프로덕션에서 사용하기 위한 LLM 추론 서비스를 실험하고 최적화하는 과정을 기록하는 실험실입니다.

## 🎯 프로젝트 목표
- **실험 중심**: 다양한 모델×런타임×파라미터 조합 벤치마킹
- **프로덕션 관점**: 실제 서비스 운영 시 고려사항과 트레이드오프 탐구
- **투명한 기록**: 모든 시행착오와 의사결정 과정을 솔직하게 공개

## 🚀 현재 진행 상황

| 단계 | 상태 | 완료일 | 작업 로그 |
|------|------|--------|-----------|
| 📋 자료 조사 | ✅ 완료 | 2025-08-03 | [상세 로그](docs/work-logs/2025-08-03-project-setup.md) |

## 🧪 실험 로드맵

### Phase 1: 기본 추론 서비스 구축
- **Lab-001**: Llama3-7B + vLLM + EC2 (기준선 설정)
- **Lab-002**: 동일 모델 + TGI 성능 비교
- **Lab-003**: 파라미터 튜닝 실험 (배치 크기, 양자화 등)

### Phase 2: 프로덕션 최적화
- **Lab-004**: 오토스케일링 및 로드밸런싱
- **Lab-005**: 비용 최적화 전략
- **Lab-006**: 모니터링 및 장애 대응

## 📚 핵심 참고 자료
이 튜토리얼 작성 시 벤치마킹한 주요 자료들:

**프로덕션 모범사례:**
- [Databricks Blog](https://www.databricks.com/blog/llm-inference-performance-engineering-best-practices) - 실제 운영 환경 고려사항
- [NVIDIA Developer](https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/) - 하드웨어 레벨 최적화

**기술 구현:**
- [vLLM Blog](https://blog.vllm.ai/2023/06/20/vllm.html) - PagedAttention 기술
- [LaunchDarkly](https://launchdarkly.com/blog/llm-inference-optimization/) - 최적화 기법

**오픈소스 프로젝트:**
- [vllm-project/vllm](https://github.com/vllm-project/vllm) - 고성능 추론 엔진
- [tensorzero/tensorzero](https://github.com/tensorzero/tensorzero) - 서비스 아키텍처 참고

## 📝 작업 과정 기록
모든 실험 과정, 고민점, 실패 경험은 [작업 로그](docs/work-logs/)에서 확인할 수 있습니다.
