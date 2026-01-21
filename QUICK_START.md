# ⚡ 빠른 시작 가이드

## 1️⃣ 설치 (5분)

```bash
cd multi-ai-orchestrator

# Python 패키지 설치
pip install -r requirements.txt

# API 키 설정 (.env 파일 생성)
cp .env.example .env
nano .env  # 여기에 API 키 입력
```

**.env 파일 내용**:

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Claude API 키
GEMINI_API_KEY=AIzaSyxxxxx      # Gemini API 키
PERPLEXITY_API_KEY=pplx-xxxxx   # Perplexity API 키 (선택)
GOOGLE_APPLICATION_CREDENTIALS=./sa-key.json
GCP_PROJECT_ID=phsysics
```

---

## 2️⃣ 첫 번째 토론 (1분)

```bash
# 간단한 테스트 토론
python scripts/auto-debate.py "Python vs JavaScript for backend" --rounds 2
```

**예상 출력**:

```
🔥 Starting debate: Python vs JavaScript for backend

=== Round 1 ===
  Claude proposing... ✓ (3.2s)
  Gemini reviewing... ✓ (2.8s)
  Consensus: 45%

=== Round 2 ===
  Gemini alternative... ✓ (3.5s)
  Claude rebuttal... ✓ (2.9s)
  Consensus: 78%

🎉 Debate concluded!

✓ Results saved to docs/brain/debate_20250117_210530.json
```

---

## 3️⃣ 결과 확인

```bash
# 토론 결과 보기
cat docs/brain/DECISIONS.md

# 상세 토론 내용
cat docs/brain/debate_*.json | jq .
```

---

## 📋 주요 사용 예시

### 예시 A: 로컬에서 바로 토론

```bash
# 기본 토론 (4라운드)
python scripts/auto-debate.py "어떤 데이터베이스를 선택할까?"

# 빠른 토론 (2라운드만)
python scripts/auto-debate.py "변수명 컨벤션" --quick

# 전문가 모드 (Perplexity 포함)
python scripts/auto-debate.py "보안 아키텍처" --expert
```

---

### 예시 B: 과거 결정 검색 (Vertex AI 필요)

```bash
# Vertex AI에서 검색
python .claude/skills/vertex-search/vertex_search.py "NoiseComputer 곱셈"
```

**출력**:

```
Found 3 results:

## Result 1 (Relevance: 92%)
**Source**: BigQuery
**Created**: 2025-01-15 10:30:00

NoiseComputer 256x256 구조에서 RTL 곱셈 최적화...

**GitHub**: https://github.com/...
---
```

---

### 예시 C: GitHub ↔ Vertex AI 동기화

```bash
# docs/brain/을 Vertex AI에 업로드
python scripts/vertex_github_bridge.py --to-vertex

# Vertex AI에서 최신 결정 다운로드
python scripts/vertex_github_bridge.py --from-vertex
```

---

## 🎯 3가지 사용 방법

### 방법 1: 커맨드라인 (가장 빠름)

```bash
python scripts/auto-debate.py "주제"
```

### 방법 2: GitHub Issue (팀 협업)

```markdown
Issue 생성:
Title: [Debate] 인증 방식 선택
Labels: ai-debate
→ GitHub Actions가 자동으로 토론 실행
```

### 방법 3: Claude Code Skill (통합)

```bash
# Claude Code에서
/debate "주제"
/vertex-search "검색어"
/github-sync
```

---

## 🔧 설정 커스터마이징

### 토론 설정 변경

**파일**: `config/debate_config.yaml`

```yaml
debate:
  max_rounds: 4 # 최대 라운드
  consensus_threshold: 0.85 # 자동 채택 기준
  expert_threshold: 0.70 # Perplexity 호출 기준

participants:
  claude:
    model: claude-sonnet-4-5-20250929
    temperature: 0.7
  gemini:
    model: gemini-2.0-flash # Production model for paid tier
    temperature: 0.7
```

---

### Vertex AI 설정 변경

**파일**: `config/vertex_config.yaml`

```yaml
project_id: phsysics
location: us-central1

embedding:
  model: textembedding-gecko@003
  dimensions: 768
  batch_size: 100

search:
  similarity_threshold: 0.7 # 최소 유사도
  max_results: 10 # 최대 결과 수
```

---

## 🚀 GitHub 연동 (선택)

### 1. GitHub 레포 생성

```bash
cd multi-ai-orchestrator
git init
git add .
git commit -m "Initial commit"

# GitHub CLI 사용
gh repo create multi-ai-orchestrator --public --source=. --push
```

### 2. GitHub Secrets 설정

GitHub 웹사이트 → Settings → Secrets and variables → Actions

추가할 Secrets:

- `ANTHROPIC_API_KEY`: Claude API 키
- `GEMINI_API_KEY`: Gemini API 키
- `PERPLEXITY_API_KEY`: Perplexity API 키
- `GCP_SA_KEY`: sa-key.json 파일 전체 내용

### 3. Issue로 토론 요청

```markdown
Title: [Debate] Redis vs PostgreSQL for caching
Labels: ai-debate

Body:
캐싱 레이어를 어떻게 구현할지 결정이 필요합니다.

요구사항:

- 100,000 동시 접속
- 밀리초 단위 응답
- 데이터 영속성 필요
```

→ GitHub Actions가 자동으로 토론 실행 & 결과 댓글 작성

---

## 📚 더 알아보기

- **전체 가이드**: [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **설치 가이드**: [SETUP.md](SETUP.md)
- **프로젝트 구조**: [README.md](README.md)

---

## 🎨 실제 토론 예시

**입력**:

```bash
python scripts/auto-debate.py "microservices vs monolith" --rounds 3
```

**출력**:

```
🔥 Starting debate: microservices vs monolith

=== Round 1 ===
Claude proposing...
POSITION: Microservices offer better scalability
REASONING: Independent deployment, technology flexibility...
EVIDENCE: Netflix, Uber case studies...
✓ (3.2s)

Gemini reviewing...
POSITION: Monolith is simpler for early stage
REASONING: Lower operational complexity, easier debugging...
EVIDENCE: Shopify initially used monolith...
✓ (2.8s)

Consensus: 35%

=== Round 2 ===
Gemini alternative...
POSITION: Start monolith, extract services later
REASONING: Avoid premature optimization...
✓ (3.1s)

Claude rebuttal...
POSITION: Agreed, but plan for microservices from day 1
REASONING: Database design, API boundaries matter...
✓ (2.7s)

Consensus: 72%

=== Round 3 ===
Both compromising...
FINAL CONSENSUS: Start with modular monolith, clear boundaries
✓ (4.2s)

Consensus: 91% ✓

🎉 Debate concluded with consensus!

================================================================================
FINAL DECISION: Modular Monolith Approach
================================================================================

CLAUDE'S POSITION:
Start with a well-structured monolith where modules have clear boundaries
and interfaces. Design as if they will become microservices, but deploy as
one unit initially. This provides:
- Simple deployment and debugging
- Easy to refactor into services later
- Avoids distributed system complexity early on

GEMINI'S POSITION:
Agreed with modular monolith. Key is proper domain-driven design with:
- Clear bounded contexts
- Well-defined APIs between modules
- Independent databases per module (or schema separation)
- Monitoring and observability from start

IMPLEMENTATION NOTES:
1. Use feature folders or module structure
2. Enforce boundaries with architectural tests
3. Set up CI/CD for easy extraction later
4. Monitor module dependencies

================================================================================

✓ Saved to docs/brain/DECISIONS.md
✓ Saved to docs/brain/debate_20250117_210530.json
```

---

## 💡 팁

### 토론 품질 향상

- 구체적인 컨텍스트 제공
- 요구사항 명시 (성능, 보안, 비용 등)
- 대안 미리 나열 (선택지가 많을수록 좋음)

### 비용 절감

- `--quick` 옵션으로 2라운드만 실행
- Perplexity는 정말 필요할 때만
- 로컬 테스트는 무료 (API 키만 있으면 됨)

### 검색 최적화

- 키워드 + 컨텍스트 조합
- "NoiseComputer 곱셈 최적화" > "곱셈"
- 태그 활용 (architecture, performance 등)
