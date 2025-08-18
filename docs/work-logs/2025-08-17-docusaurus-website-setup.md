# 2025-08-17: Docusaurus 웹사이트 구축

## 📋 오늘의 목표
기존 워크로그를 사용자가 직접 따라할 수 있는 Docusaurus 웹사이트로 변환하여 실제 활용 가능한 튜토리얼 사이트 구축

## 🎯 프로젝트 현황
- **이전 단계**: LLM 추론 서비스 구축 완료 (2025-08-14)
- **현재 목표**: 사용자 친화적 문서화 사이트 구축
- **새로운 워크플로우**: 개발자용 워크로그 + 사용자용 튜토리얼 병행 관리

## 🏗️ 선택한 접근 방법

### 방법 1 채택: 점진적 전환
```
llm-inference-lab/
├── docs/work-logs/          # 기존 개발자용 상세 기록 유지
├── website/                 # 새로운 Docusaurus 사이트
│   ├── docs/
│   │   ├── getting-started/
│   │   ├── tutorials/
│   │   └── guides/
│   └── blog/               # 실험 일지
└── README.md
```

**선택 이유:**
- 기존 작업 손실 없음
- Git 히스토리 보존
- 개발자용/사용자용 콘텐츠 병행 가능

## 🚀 Docusaurus 설정

### 1. 초기 설정
```bash
# Docusaurus 프로젝트 생성
npx create-docusaurus@latest website classic

# TypeScript 선택
# 성공적으로 website/ 폴더에 생성
```

### 2. 프로젝트 정보 커스터마이징
```javascript
// docusaurus.config.ts 주요 설정
{
  title: 'LLM Inference Lab',
  tagline: '실무진이 직접 검증한 LLM 추론 서비스 구축 가이드',
  url: 'https://hunhoon21.github.io',
  baseUrl: '/llm-inference-lab/',
  organizationName: 'hunhoon21',
  projectName: 'llm-inference-lab',
}
```

### 3. 네비게이션 구조 설계
```javascript
// sidebars.ts 구성
tutorialSidebar: [
  'intro',
  {
    type: 'category',
    label: '시작하기',
    items: ['getting-started/prerequisites', 'getting-started/account-setup'],
  },
  {
    type: 'category', 
    label: '튜토리얼',
    items: [
      'tutorials/gcp-basic-setup',
      'tutorials/llm-inference-setup', 
      'tutorials/client-integration',
    ],
  },
  {
    type: 'category',
    label: '가이드',
    items: [
      'guides/gpu-management',
      'guides/cost-optimization',
      'guides/troubleshooting',
    ],
  },
],
```

## 📝 콘텐츠 변환 작업

### 기존 워크로그 → 사용자 친화적 튜토리얼

#### 1. 인트로 페이지 (`intro.md`)
- 프로젝트 목표 및 학습 경로 안내
- 예상 비용, 소요 시간, 사전 지식 명시
- 기여 방법 및 GitHub 링크

#### 2. 시작하기 섹션
**`getting-started/prerequisites.md`**
- 로컬 환경 요구사항
- 클라우드 계정 설정
- 예상 비용 및 시간
- 사전 지식 요구사항

**`getting-started/account-setup.md`**
- GCP 계정 설정 단계별 가이드
- **탭 컴포넌트 활용**: macOS/Linux/Windows별 설치 방법
- gCloud CLI 설치 및 인증
- 비용 모니터링 설정

#### 3. 핵심 튜토리얼 섹션
**`tutorials/gcp-basic-setup.md`** (2025-08-11 워크로그 기반)
- 실제 경험 반영된 GPU 할당량 승인 팁
- 1분 내 승인받은 실제 사유 메시지 예시 포함
- 최신 Ubuntu 2204 이미지 사용
- SSH 키 파일 옵션 일관성 적용

**`tutorials/llm-inference-setup.md`** (2025-08-14 워크로그 기반)
- GPU 인스턴스 생성 (L4/T4 선택 가능)
- **탭 컴포넌트**: GPU 타입별 생성 명령어
- vLLM 설치 및 FastAPI 서버 구축
- 실제 Python 코드 예시 포함

**`tutorials/client-integration.md`**
- 기존 Python 클라이언트 연동 방법
- 단일/배치 처리 가이드
- 성능 벤치마킹 방법

#### 4. 가이드 섹션
- `gpu-management.md`: GPU 리소스 최적화
- `cost-optimization.md`: 비용 절약 전략
- `troubleshooting.md`: 주요 문제 해결법

## 🎨 사용자 친화적 기능

### 1. Interactive Components
```markdown
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
<TabItem value="l4" label="L4 GPU (권장)">
// L4 GPU 설정 코드
</TabItem>
<TabItem value="t4" label="T4 GPU (비용 절약)">
// T4 GPU 설정 코드  
</TabItem>
</Tabs>
```

### 2. 경고 및 팁 박스
```markdown
:::warning 중요
GPU 인스턴스는 높은 비용이 발생합니다!
:::

:::tip 1분 내 승인받은 실제 사유
구체적인 사유 메시지 예시...
:::
```

### 3. 복사 가능한 코드 블록
- 모든 터미널 명령어에 복사 버튼
- 실행 가능한 Python 코드 예시
- 설정 파일 템플릿

## 🧪 테스트 및 검증

### 개발 서버 실행
```bash
cd website
npm start
# ✅ 성공: http://localhost:3000/llm-inference-lab/
```

### 주요 검증 항목
- [x] 모든 페이지 렌더링 정상
- [x] 네비게이션 구조 직관적
- [x] 탭 컴포넌트 작동
- [x] 코드 블록 하이라이팅
- [x] 내부 링크 연결 정상

## 🔄 앞으로의 워크플로우

### 새로운 실험 진행 시
```bash
1. 실험 + docs/work-logs/2025-XX-XX-experiment.md 작성
2. 검증 완료 후 website/docs/tutorials/new-tutorial.md 생성
3. 두 브랜치에서 각각 커밋
4. 동시에 개발자용/사용자용 콘텐츠 관리
```

### 기존 내용 업데이트 시
```bash
1. work-logs/기존-파일.md 수정
2. website/docs/tutorials/관련-튜토리얼.md 동시 업데이트
3. 동일 브랜치에서 함께 커밋
```

## 📊 콘텐츠 변환 원칙

### Work-logs (개발자용)
- ✅ 모든 시행착오 기록
- ✅ 상세한 기술적 설명  
- ✅ 개인적 회고, 배운 점
- ✅ 날짜별 진행 과정

### Docusaurus (사용자용)
- ✅ 단계별 명확한 가이드
- ✅ 복사 가능한 코드 블록
- ✅ 플랫폼별 선택지 (탭)
- ✅ 시각적 강조 (경고박스)
- ✅ 전후 관계 명확한 네비게이션

## 💡 핵심 개선사항

### 1. 실제 경험 반영
- GPU 할당량 승인: 24-48시간 → 1-5분 (적절한 사유 작성 시)
- 성공한 할당량 요청 메시지 예시 제공
- 최신 Deep Learning VM 이미지 (pytorch-2-7-cu128-ubuntu-2204-nvidia-570)

### 2. 사용자 편의성 강화
- 플랫폼별 설치 가이드 (macOS/Linux/Windows)
- GPU 타입별 선택 가이드 (L4/T4)
- 단계별 체크리스트 제공
- 예상 비용 및 시간 명시

### 3. 실무 중심 접근
- 실제 운영 시 고려사항
- 비용 최적화 전략
- 문제 해결 방법
- 성능 최적화 팁

## 📝 오늘의 성과
- [x] Docusaurus 프로젝트 설정 완료
- [x] 한국어 네비게이션 구조 설계
- [x] 기존 2개 워크로그를 사용자 친화적 튜토리얼로 변환
- [x] Interactive 컴포넌트 (탭, 경고박스) 적용
- [x] 개발 서버 실행 성공
- [x] 앞으로의 워크플로우 확립

## 🔄 다음 단계
1. **GitHub Pages 배포 설정**
   - GitHub Actions 워크플로우 구성
   - 자동 빌드 및 배포 파이프라인

2. **콘텐츠 확장**
   - 더 많은 실험 워크로그 추가 시 튜토리얼 변환
   - 블로그 섹션에 실험 후기 추가

3. **사용자 피드백 수집**
   - GitHub Discussions 활성화
   - 실제 사용자들의 따라하기 결과 수집

## 💡 오늘 배운 점
- **이중 관리 방식의 효과**: 개발자용 상세 기록 + 사용자용 정제된 가이드
- **Docusaurus의 강력함**: TypeScript 지원, 컴포넌트 기반 문서화
- **실제 경험의 가치**: 1분 GPU 할당량 승인 같은 실무 팁의 중요성
- **사용자 관점 중요성**: 기술적 정확성보다 따라하기 쉬운 가이드가 더 중요

## ⚠️ 주의사항
- 워크로그와 튜토리얼 내용 동기화 필요
- GitHub Pages 배포 시 baseUrl 설정 주의
- 실제 사용자 테스트 전까지는 베타 버전으로 명시
- 비용 관련 정보는 주기적 업데이트 필요

---

**🎉 결론**: 성공적으로 개발자 중심의 워크로그를 사용자가 직접 따라할 수 있는 실용적인 튜토리얼 사이트로 전환 완료!