# 🧪 LLM Inference Lab
**추론서비스 전문가 관점**에서 LLM 추론 서비스의 안정적 운영을 실험하고 기록하는 튜토리얼입니다.

## 🎯 프로젝트 목표
- **실험 중심**: 다양한 모델×런타임×파라미터 조합 벤치마킹
- **운영 전문성**: 추론서비스의 안정적 운영을 위한 실무 노하우 축적
- **투명한 기록**: 모든 시행착오와 의사결정 과정을 솔직하게 공개
- **실무 적용**: 실제 프로덕션 환경에서 바로 활용 가능한 가이드 제공

## 🚀 현재 진행 상황

| 단계 | 상태 | 완료일 | 작업 로그 |
|------|------|--------|-----------|
| 📋 프로젝트 설정 | ✅ 완료 | 2025-08-03 | [상세 로그](docs/work-logs/2025-08-03-setup.md) |
| **Lab-001: Llama3-7B + vLLM + EC2** | | | |
| └ ☁️ EC2 환경 설정 | 📋 예정 | - | - |
| └ 🤖 Llama3-7B 모델 준비 | 📋 예정 | - | - |
| └ 🚀 vLLM 추론서비스 구축 | 📋 예정 | - | - |
| └ 💻 클라이언트 개발 | ✅ 완료 | 2025-08-07 | [클라이언트 개발](docs/work-logs/2025-08-07-client-development.md) |

## 🧪 실험 로드맵

### Phase 1: 기본 추론 서비스 구축
- **Lab-001**: Llama3-7B + vLLM + EC2 (기준선 설정)
- **Lab-002**: 동일 모델 + TGI 성능 비교
- **Lab-003**: 파라미터 튜닝 실험 (배치 크기, 양자화 등)

### Phase 2: 안정적 운영 및 최적화
- **Lab-004**: 모니터링 및 장애 대응 시스템 구축
- **Lab-005**: 성능 최적화 및 비용 효율성 개선
- **Lab-006**: 운영 자동화 및 스케일링 전략

## 📚 핵심 참고 자료
추론서비스 운영을 위해 참고한 주요 자료들:

**프로덕션 모범사례:**
- [Databricks Blog](https://www.databricks.com/blog/llm-inference-performance-engineering-best-practices) - 실제 운영 환경 고려사항
- [NVIDIA Developer](https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/) - 하드웨어 레벨 최적화

**기술 구현:**
- [vLLM Blog](https://blog.vllm.ai/2023/06/20/vllm.html) - PagedAttention 기술
- [LaunchDarkly](https://launchdarkly.com/blog/llm-inference-optimization/) - 최적화 기법

**오픈소스 프로젝트:**
- [vllm-project/vllm](https://github.com/vllm-project/vllm) - 고성능 추론 엔진
- [tensorzero/tensorzero](https://github.com/tensorzero/tensorzero) - 서비스 아키텍처 참고

## 📝 실험 및 운영 기록
모든 실험 과정, 운영 경험, 시행착오는 [작업 로그](docs/work-logs/)에서 확인할 수 있습니다.
