# Multi-AI Orchestrator 사용 가이드

## 🎯 사용 시나리오

### 시나리오 1: 기술 결정이 필요할 때

**상황**: "RTL 곱셈을 어떻게 최적화하지?"

**방법**:
```bash
# Claude Code에서
/debate "RTL 곱셈 최적화 방법"
```

**결과**:
1. Claude가 방법 A 제안
2. Gemini가 검토 & 대안 제시
3. 3-4 라운드 토론
4. 합의도 계산 (예: 87%)
5. 자동 저장: `docs/brain/DECISIONS.md`, Vertex AI

---

### 시나리오 2: 과거 결정 검색

**상황**: "예전에 NoiseComputer 관련해서 뭐 결정했었나?"

**방법**:
```bash
# Claude Code에서
/vertex-search NoiseComputer 결정사항
```

**결과**:
- BigQuery에서 유사도 검색
- GCS에서 메타데이터 검색
- 관련도 순으로 정렬된 결과 표시

---

### 시나리오 3: GitHub Issue로 토론 요청

**상황**: 팀원들과 공유하고 싶을 때

**방법**:
1. GitHub에서 Issue 생성
2. 제목: `[Debate] 인증 방식 선택`
3. 라벨: `ai-debate` 추가

**자동 진행**:
```
Issue 생성
   ↓
GitHub Actions 자동 실행
   ↓
Multi-AI 토론 (Claude ↔ Gemini)
   ↓
결과를 Issue에 댓글로 작성
   ↓
합의 도달 시 Issue 자동 종료
```

---

## 📖 주요 명령어

### 1. `/debate` - AI 토론 시작

```bash
# 기본 토론
/debate "어떤 데이터베이스를 쓸까?"

# 전문가 모드 (Perplexity 포함)
/debate --expert "보안 아키텍처 설계"

# 빠른 토론 (2라운드만)
/debate --quick "변수 이름 컨벤션"
```

**토론 프로세스**:
```
Round 1: Claude 제안 → Gemini 검토
Round 2: Gemini 대안 → Claude 반박
Round 3: 양측 절충안 제시
Round 4: Perplexity 판정 (합의 70% 미만일 때만)
```

**합의 기준**:
- 85% 이상: ✅ 자동 채택
- 70-85%: ⚠️ 사용자 검토 필요
- 70% 미만: 🔥 토론 연장 or Perplexity 호출

---

### 2. `/vertex-search` - 지식 검색

```bash
# 기본 검색
/vertex-search RTL 곱셈 규칙

# 이전 토론 결과 찾기
/vertex-search 이전 토론 결과
```

**검색 범위**:
- BigQuery: 4,362개 임베딩 (의미론적 검색)
- GCS: context/, decisions/, session_logs/
- GitHub: docs/brain/

---

### 3. `/github-sync` - 동기화

```bash
# 양방향 동기화
/github-sync

# GitHub → Vertex AI만
/github-sync --to-vertex

# Vertex AI → GitHub만
/github-sync --from-vertex

# 처음 전체 동기화
/github-sync --initial-sync
```

---

### 4. `/decision-log` - 결정 기록

```bash
# 최근 토론 결과 자동 로깅
/decision-log

# 수동으로 결정 기록
/decision-log --manual \
  --title "데이터베이스 선택" \
  --reason "성능과 확장성" \
  --alternatives "PostgreSQL, MongoDB, MySQL"
```

---

## 🔄 자동화 흐름

### 자동 동기화 (Hooks)

**1. 파일 편집 시**:
```
docs/brain/DECISIONS.md 수정
   ↓ (PostToolUse Hook)
자동으로 Vertex AI GCS 업로드
```

**2. 토론 키워드 감지**:
```
"어떻게 생각해?" 입력
   ↓ (UserPromptSubmit Hook)
💡 "/debate 사용을 고려해보세요" 알림
```

**3. 세션 종료 시**:
```
Claude Code 종료
   ↓ (Stop Hook)
세션 로그 Vertex AI에 자동 저장
```

---

### GitHub Actions 자동화

**1. Issue 생성 시**:
```yaml
[Debate] 제목 or ai-debate 라벨
   ↓
ai-debate-trigger.yml 실행
   ↓
Python으로 Multi-AI 토론
   ↓
결과를 docs/brain/ 커밋
   ↓
Issue에 결과 댓글
   ↓
합의 도달 시 Issue 종료
```

**2. docs/brain/ 변경 시**:
```yaml
DECISIONS.md push
   ↓
vertex-sync.yml 실행
   ↓
변경된 파일만 임베딩 생성
   ↓
BigQuery + GCS 저장
```

**3. 매일 자정 (cron)**:
```yaml
knowledge-update.yml 실행
   ↓
Vertex AI에서 최신 결정 가져오기
   ↓
docs/brain/ 업데이트
   ↓
자동 커밋
```

---

## 💾 데이터 저장 위치

### 1. GitHub (버전 관리)
```
docs/brain/
├── CONTEXT.md           # 프로젝트 전체 컨텍스트
├── DECISIONS.md         # 결정 사항 로그 (사람이 읽기 쉬움)
├── DEBATES.md           # 토론 히스토리
└── debate_*.json        # 상세 토론 전문 (최근 30개만)
```

### 2. Vertex AI BigQuery (검색용)
```sql
phsysics.knowledge_base.embeddings
├── content        # 텍스트 내용
├── embedding      # 768차원 벡터
├── metadata       # JSON (type, tags, date 등)
└── created_at     # 생성 시각
```

### 3. Vertex AI GCS (백업)
```
gs://multi-ai-memory-bank-phsysics/
├── context/          # docs/brain/ 백업
├── decisions/        # 토론 결과 JSON
└── session_logs/     # 세션 로그
```

---

## 🔍 실전 예시

### 예시 1: 로컬에서 토론

```bash
# 터미널에서
cd multi-ai-orchestrator

# API 키 설정
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export GEMINI_API_KEY="AIzaSyxxxxx"
export GOOGLE_APPLICATION_CREDENTIALS="./sa-key.json"

# 토론 실행
python scripts/auto-debate.py "Redis vs PostgreSQL for caching"
```

**출력 예시**:
```
🔥 Starting debate: Redis vs PostgreSQL for caching

=== Round 1 ===
  Claude proposing... ✓ (3.2s)
  Gemini reviewing... ✓ (2.8s)
  Consensus: 45%

=== Round 2 ===
  Gemini alternative... ✓ (3.5s)
  Claude rebuttal... ✓ (2.9s)
  Consensus: 72%

=== Round 3 ===
  Compromise... ✓ (4.1s)
  Consensus: 88% ✓

🎉 Debate concluded with consensus!

========================================
CLAUDE'S FINAL POSITION
Redis for read-heavy operations...

GEMINI'S FINAL POSITION
PostgreSQL with materialized views...
========================================

✓ Results saved to docs/brain/
```

---

### 예시 2: GitHub Issue로 요청

**Issue 생성**:
```
Title: [Debate] 인증 방식: JWT vs Session

Body:
사용자 인증을 어떻게 구현할지 결정이 필요합니다.

Context:
- 모바일 앱 + 웹 지원
- 10,000 동시 사용자 예상
- 보안이 중요

Alternatives:
1. JWT (Stateless)
2. Session (Redis 기반)
3. OAuth 2.0
```

**자동 실행**:
- GitHub Actions가 토론 시작
- 결과가 Issue 댓글로 추가
- 합의 도달 시 Issue 자동 종료

---

### 예시 3: 과거 결정 검색

**Claude Code에서**:
```
User: NoiseComputer 곱셈 최적화 관련해서 예전에 뭐 결정했었나요?