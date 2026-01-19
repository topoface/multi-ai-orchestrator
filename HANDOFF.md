# Multi-AI Orchestrator 인수인계 문서

**작성일**: 2026-01-19
**작성자**: Claude Sonnet 4.5
**인수자**: 다른 AI (Gemini / Claude / Perplexity)

---

## 📊 전체 진행 현황

### ✅ 완료된 Phase (Phase 1-6 + 일부 Phase 7)

```
Phase 1: 디렉토리 구조 ✅ 100%
Phase 2: Skills 구현 ✅ 100%
Phase 3: Subagents 구현 ✅ 100%
Phase 4: Hooks 구현 ✅ 100%
Phase 5: GitHub Actions ✅ 100%
Phase 6: Vertex AI 연동 ✅ 90% (BigQuery 테이블 미확인)
Phase 7: 테스트 ⚠️ 50% (로컬만 완료, GitHub 미완료)
```

**총 진행률**: ~85%

---

## 🎯 프로젝트 개요

**목표**: Vertex AI(phsysics) 중심의 Multi-AI 토론 시스템 구축

**아키텍처**:

```
사용자 → Vertex AI (메인 대화, RAG 기억)
           ↓ (확신 없을 때)
GitHub Issue → AI 토론 (Claude CLI ↔ Gemini API ↔ Perplexity)
           ↓ (토론 결과)
Vertex AI 학습 + GitHub 커밋 (히스토리)
```

**프로젝트 위치**: `/home/wishingfly/multi-ai-orchestrator/`

---

## ✅ 완료된 작업 (상세)

### Phase 1: 디렉토리 구조 ✅

**상태**: 완료
**위치**: `/home/wishingfly/multi-ai-orchestrator/`

**생성된 파일**:

```
multi-ai-orchestrator/
├── .github/
│   ├── workflows/
│   │   ├── ai-debate-trigger.yml ✅
│   │   ├── vertex-sync.yml ✅
│   │   └── knowledge-update.yml ✅
│   ├── ISSUE_TEMPLATE/
│   │   ├── debate-request.yml ✅
│   │   └── knowledge-query.yml ✅
│   └── scripts/
│       ├── multi_ai_runner.py ✅
│       └── post_debate_comment.py ✅
├── .claude/
│   ├── skills/ (4개 skill, 모두 완성) ✅
│   ├── agents/ (3개 agent, 모두 완성) ✅
│   └── hooks/ (3개 hook, 모두 완성) ✅
├── docs/brain/ ✅
│   ├── CONTEXT.md ✅
│   ├── DECISIONS.md ✅
│   ├── DEBATES.md ✅
│   └── debate_*.json (3개 테스트 결과) ✅
├── scripts/ ✅
│   ├── auto-debate.py ✅
│   ├── vertex_github_bridge.py ✅
│   └── vertex_uploader.py ✅
├── config/
│   ├── vertex_config.yaml ✅
│   └── debate_config.yaml ✅
├── .env (API 키 설정 완료) ✅
├── requirements.txt ✅
├── README.md ✅
├── SETUP.md ✅
└── venv/ (Python 가상환경) ✅
```

---

### Phase 2: Skills 구현 ✅

#### 1. vertex-search Skill ✅

**파일**: `.claude/skills/vertex-search/vertex_search.py` (181줄)
**상태**: 완전 구현됨
**기능**:

- BigQuery COSINE_SIMILARITY 벡터 검색
- GCS 메타데이터 키워드 검색
- 결과 통합 및 관련도 정렬
- GitHub 링크 포함

**사용법**:

```bash
/vertex-search NoiseComputer 곱셈 규칙
python .claude/skills/vertex-search/vertex_search.py "your query"
```

#### 2. debate-request Skill ✅

**파일**: `.claude/skills/debate-request/debate_engine.py` (368줄)
**상태**: 완전 구현됨, **로컬 테스트 완료**
**기능**:

- Claude API 호출 (Anthropic SDK)
- Gemini API 호출 (Vertex AI SDK)
- Perplexity API 호출
- 4 라운드 토론 프로토콜
- 합의도 계산 (Jaccard similarity)
- 자동 결과 저장 (JSON + DECISIONS.md)

**테스트 증거**:

```bash
ls docs/brain/debate_*.json
# debate_20260117_213709.json (9.7KB)
# debate_20260117_214607.json (1.9KB)
# debate_20260117_215618.json (32.6KB)
```

**사용법**:

```bash
/debate "RTL 곱셈 최적화 방법?"
python scripts/auto-debate.py "Your topic" --expert
```

#### 3. github-sync Skill ✅

**파일**: `.claude/skills/github-sync/sync_manager.py`
**상태**: 구현 완료
**기능**: GitHub ↔ Vertex AI 양방향 동기화

#### 4. decision-logger Skill ✅

**파일**: `.claude/skills/decision-logger/logger.py`
**상태**: 구현 완료
**기능**: 결정 사항 자동 기록

---

### Phase 3: Subagents ✅

#### 1. github-orchestrator ✅

**파일**: `.claude/agents/github-orchestrator/orchestrator.py`
**상태**: 구현 완료

#### 2. debate-manager ✅

**파일**: `.claude/agents/debate-manager/debate_manager.py`
**상태**: 구현 완료

#### 3. vertex-learner ✅

**파일**: `.claude/agents/vertex-learner/vertex_learner.py`
**상태**: 구현 완료

---

### Phase 4: Hooks ✅

#### 1. sync-to-vertex.py ✅

**위치**: `.claude/hooks/sync-to-vertex.py`
**트리거**: PostToolUse (Edit/Write 후)
**기능**: docs/brain/ 파일 변경 시 GCS 자동 업로드

#### 2. trigger-debate.py ✅

**위치**: `.claude/hooks/trigger-debate.py`
**트리거**: UserPromptSubmit
**기능**: 토론 키워드 감지 시 자동 토론 시작

#### 3. save-debate-result.py ✅

**위치**: `.claude/hooks/save-debate-result.py`
**트리거**: Stop
**기능**: 세션 로그 Vertex AI 자동 저장

**⚠️ 주의**: Hooks는 `~/.claude/settings.local.json`에 등록되어야 작동함 (아직 미등록)

---

### Phase 5: GitHub Actions ✅

#### 1. ai-debate-trigger.yml ✅

**위치**: `.github/workflows/ai-debate-trigger.yml`
**트리거**: Issue 생성 (제목 `[Debate]` 또는 레이블 `ai-debate`)
**작업**: Multi-AI 토론 → 결과 커밋 → Issue 댓글 → 종료

#### 2. vertex-sync.yml ✅

**위치**: `.github/workflows/vertex-sync.yml`
**트리거**: docs/brain/ 파일 push
**작업**: Vertex AI 임베딩 생성 → BigQuery 저장

#### 3. knowledge-update.yml ✅

**위치**: `.github/workflows/knowledge-update.yml`
**트리거**: 매일 자정 (cron) 또는 수동
**작업**: Vertex AI → GitHub 동기화

---

### Phase 6: Vertex AI 연동 ✅

#### GCP 설정 ✅

- **프로젝트**: phsysics
- **리전**: us-central1
- **인증**: application_default_credentials.json 존재
- **활성 프로젝트**: `gcloud config get-value project` → phsysics ✅

#### API 키 설정 ✅

**파일**: `.env`

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...fAqUcAAA
GEMINI_API_KEY=AIzaSyDqzRTH...QbKOswn8
GCP_PROJECT_ID=phsysics
GCP_REGION=us-central1
PERPLEXITY_API_KEY=(미설정)
```

#### Vertex AI 설정 ✅

**파일**: `config/vertex_config.yaml`

```yaml
project_id: phsysics
location: us-central1

bigquery:
  dataset: my_physics_agent_stackoverflow_data
  table: questions_embeddings
  knowledge_dataset: knowledge_base # 새로 생성 필요!
  knowledge_table: embeddings # 새로 생성 필요!

gcs:
  bucket: multi-ai-memory-bank-phsysics
  folders:
    context: context/
    decisions: decisions/
    session_logs: session_logs/

embedding:
  model: textembedding-gecko@003
  dimensions: 768
```

---

### Phase 7: 테스트 ⚠️ (일부 완료)

#### 로컬 테스트 ✅

**증거**: `docs/brain/` 폴더에 3개의 debate JSON 파일 존재

```bash
debate_20260117_213709.json  # 9.7KB
debate_20260117_214607.json  # 1.9KB
debate_20260117_215618.json  # 32.6KB
```

**테스트 방법**:

```bash
cd /home/wishingfly/multi-ai-orchestrator
source venv/bin/activate
python scripts/auto-debate.py "테스트 토론 주제"
```

---

## ❌ 미완료 작업 (다음 AI가 해야 할 일)

### 1. GitHub 레포 생성 및 연결 ❌

**문제**: 현재 `multi-ai-orchestrator` 폴더가 Git 레포가 **아님**

**해야 할 작업**:

```bash
# 1. GitHub에서 레포 생성
# GitHub 웹사이트에서 새 레포 생성: multi-ai-orchestrator (Public)

# 2. Git 초기화 및 연결
cd /home/wishingfly/multi-ai-orchestrator
git init
git add .
git commit -m "Initial commit: Multi-AI Orchestrator v1.0"
git branch -M main
git remote add origin https://github.com/[USERNAME]/multi-ai-orchestrator.git
git push -u origin main
```

**예상 시간**: 10분

---

### 2. GitHub CLI 설치 및 인증 ❌

**문제**: `gh` 명령어 없음

**해야 할 작업**:

```bash
# Ubuntu/Debian
sudo apt install gh

# 또는 공식 방법
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# 인증
gh auth login
```

**예상 시간**: 10분

---

### 3. GitHub Secrets 설정 ❌

**위치**: GitHub 웹사이트 → Settings → Secrets and variables → Actions

**설정할 Secrets**:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...fAqUcAAA  # .env에서 복사
GEMINI_API_KEY=AIzaSyDqzRTH...QbKOswn8     # .env에서 복사
PERPLEXITY_API_KEY=(필요시 생성)
GCP_SA_KEY=(Service Account JSON 파일 전체 내용)
```

**GCP_SA_KEY 생성 방법**:

```bash
# Service Account 생성
gcloud iam service-accounts create multi-ai-orchestrator \
    --project=phsysics \
    --display-name="Multi-AI Orchestrator"

# 권한 부여
gcloud projects add-iam-policy-binding phsysics \
    --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding phsysics \
    --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Key 생성
gcloud iam service-accounts keys create sa-key.json \
    --iam-account=multi-ai-orchestrator@phsysics.iam.gserviceaccount.com

# 파일 내용을 GitHub Secrets에 복사
cat sa-key.json
```

**예상 시간**: 15분

---

### 4. BigQuery 테이블 생성 ❌

**문제**: `phsysics.knowledge_base.embeddings` 테이블이 **존재하지 않을 가능성**

**확인 방법**:

```bash
bq show phsysics:knowledge_base.embeddings
```

**생성 방법** (없을 경우):

```bash
# Dataset 생성
bq mk --dataset --location=us-central1 phsysics:knowledge_base

# Table 생성
bq mk --table phsysics:knowledge_base.embeddings \
  content:STRING,\
  embedding:FLOAT64,\
  metadata:JSON,\
  created_at:TIMESTAMP,\
  source:STRING
```

**또는 Python 스크립트**:

```python
from google.cloud import bigquery

client = bigquery.Client(project='phsysics')

# Dataset 생성
dataset_id = 'knowledge_base'
dataset = bigquery.Dataset(f'phsysics.{dataset_id}')
dataset.location = 'us-central1'
client.create_dataset(dataset, exists_ok=True)

# Table 생성
schema = [
    bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
    bigquery.SchemaField("metadata", "JSON"),
    bigquery.SchemaField("created_at", "TIMESTAMP"),
    bigquery.SchemaField("source", "STRING"),
]

table_id = f'phsysics.{dataset_id}.embeddings'
table = bigquery.Table(table_id, schema=schema)
client.create_table(table, exists_ok=True)
print(f"✅ Table {table_id} created")
```

**예상 시간**: 10분

---

### 5. GCS 버킷 확인 및 폴더 생성 ❌

**확인 방법**:

```bash
gsutil ls gs://multi-ai-memory-bank-phsysics/
```

**생성 방법** (없을 경우):

```bash
# 버킷 생성
gsutil mb -p phsysics -l us-central1 gs://multi-ai-memory-bank-phsysics/

# 폴더 생성 (빈 파일로 폴더 표시)
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/context/.keep
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/decisions/.keep
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/session_logs/.keep

# 확인
gsutil ls gs://multi-ai-memory-bank-phsysics/
```

**예상 시간**: 5분

---

### 6. Hooks 등록 ❌

**위치**: `~/.claude/settings.local.json`

**추가할 설정**:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/home/wishingfly/multi-ai-orchestrator/.claude/hooks/sync-to-vertex.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/home/wishingfly/multi-ai-orchestrator/.claude/hooks/trigger-debate.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/home/wishingfly/multi-ai-orchestrator/.claude/hooks/save-debate-result.py"
          }
        ]
      }
    ]
  }
}
```

**Hook 실행 권한 부여**:

```bash
chmod +x /home/wishingfly/multi-ai-orchestrator/.claude/hooks/*.py
```

**예상 시간**: 5분

---

### 7. GitHub Actions 통합 테스트 ❌

**테스트 방법**:

```bash
# 1. Issue 생성 (레포 생성 후)
gh issue create \
  --title "[Debate] NoiseComputer 256x256 선택 이유" \
  --body "256x256 구조를 선택한 기술적 근거를 AI 토론으로 정리해주세요." \
  --label "ai-debate"

# 2. Actions 실행 확인
gh run list --workflow=ai-debate-trigger.yml

# 3. 결과 검증
# - Issue 댓글에 토론 결과 작성 확인
# - docs/brain/ 자동 커밋 확인
# - Issue 종료 (합의도 85% 이상)
```

**예상 시간**: 20분

---

### 8. Perplexity API 키 생성 (선택적) ❌

**필요성**: 낮은 합의도 토론 시 전문가 판정용

**생성 방법**:

1. https://www.perplexity.ai/settings/api 접속
2. API 키 생성
3. `.env`에 추가: `PERPLEXITY_API_KEY=pplx-...`
4. GitHub Secrets에도 추가

**예상 시간**: 5분

---

## 🚀 빠른 시작 가이드 (다음 AI용)

### 1단계: 현재 상태 확인 (5분)

```bash
# 프로젝트 폴더로 이동
cd /home/wishingfly/multi-ai-orchestrator

# 파일 구조 확인
ls -la

# API 키 확인
cat .env

# GCP 프로젝트 확인
gcloud config get-value project

# 로컬 테스트 결과 확인
ls -lh docs/brain/debate_*.json
```

---

### 2단계: GitHub 레포 연결 (10분)

```bash
# GitHub에서 레포 생성 (웹사이트)
# Repository name: multi-ai-orchestrator
# Public

# Git 초기화
cd /home/wishingfly/multi-ai-orchestrator
git init
git add .
git commit -m "Initial commit: Multi-AI Orchestrator v1.0"
git branch -M main
git remote add origin https://github.com/[USERNAME]/multi-ai-orchestrator.git
git push -u origin main
```

---

### 3단계: GCP 인프라 구축 (20분)

```bash
# BigQuery 테이블 확인/생성
bq show phsysics:knowledge_base.embeddings || \
  python scripts/create_bigquery_table.py

# GCS 버킷 확인/생성
gsutil ls gs://multi-ai-memory-bank-phsysics/ || \
  bash scripts/create_gcs_bucket.sh

# Service Account 생성
bash scripts/create_service_account.sh
```

---

### 4단계: GitHub Secrets 설정 (10분)

```bash
# GitHub 웹사이트에서 수동 설정
# Settings → Secrets and variables → Actions
# ANTHROPIC_API_KEY, GEMINI_API_KEY, GCP_SA_KEY 추가
```

---

### 5단계: 통합 테스트 (15분)

```bash
# Issue 생성
gh issue create \
  --title "[Debate] 테스트 토론" \
  --body "RTL 곱셈 최적화 방법을 토론해주세요." \
  --label "ai-debate"

# Actions 실행 확인
gh run watch

# 결과 확인
cat docs/brain/DECISIONS.md
```

---

## 📁 핵심 파일 위치

### 구현 코드

```
.claude/skills/debate-request/debate_engine.py    # 토론 엔진 (368줄)
.claude/skills/vertex-search/vertex_search.py     # RAG 검색 (181줄)
.github/workflows/ai-debate-trigger.yml           # GitHub Actions
.github/scripts/multi_ai_runner.py                # Actions 진입점
```

### 설정 파일

```
.env                                # API 키
config/vertex_config.yaml           # Vertex AI 설정
config/debate_config.yaml           # 토론 설정
```

### 결과 저장소

```
docs/brain/DECISIONS.md             # 결정 사항 로그
docs/brain/debate_*.json            # 토론 결과 JSON
```

---

## 🔑 중요 정보 정리

### API 키

```bash
ANTHROPIC_API_KEY: sk-ant-api03-...fAqUcAAA
GEMINI_API_KEY: AIzaSyDqzRTH...QbKOswn8
PERPLEXITY_API_KEY: (미생성)
```

### GCP 프로젝트

```
Project ID: phsysics
Region: us-central1
Active Project: phsysics (gcloud 인증 완료)
```

### BigQuery

```
기존 테이블: phsysics.my_physics_agent_stackoverflow_data.questions_embeddings (4,362개)
생성 필요: phsysics.knowledge_base.embeddings
```

### GCS

```
버킷 이름: multi-ai-memory-bank-phsysics
폴더: context/, decisions/, session_logs/
```

---

## ⚠️ 주의사항

### 1. API 키 보안

- `.env` 파일은 **절대 GitHub에 커밋 금지**
- `.gitignore`에 이미 추가됨 ✅
- GitHub Secrets에만 저장

### 2. GCP 비용

```
예상 비용: $0.22/월
- BigQuery: 100MB 무료
- GCS: 5GB 무료 (충분함)
- Vertex AI Embeddings: 처음 1000개 무료
```

### 3. 토론 비용

```
1회 토론 비용 (4 라운드):
- Claude: $0.015 (입력 1K tokens × 8회)
- Gemini: 무료 (Gemini 2.0 Flash)
- Perplexity: $0.005 (선택적)

월 100회 토론: ~$2
```

### 4. Hooks 실행

- Hooks는 Claude Code CLI에서만 작동
- `~/.claude/settings.local.json` 등록 필수
- Python 3.10+ 필요

---

## 🐛 알려진 이슈

### 1. debate_engine.py의 합의도 계산

**문제**: 현재 Jaccard similarity만 사용, 임베딩 유사도 미사용

**해결 방법**:

```python
# calculate_consensus 함수에 임베딩 유사도 추가
# vertex_config.yaml의 agreement_scoring.embedding_weight 활용
```

**우선순위**: 중간 (현재도 작동하지만 정확도 향상 가능)

### 2. Perplexity API 키 미설정

**영향**: expert 모드 사용 불가, 낮은 합의도 토론 시 판정 불가
**해결**: Perplexity Pro 구독 → API 키 생성

**우선순위**: 낮음 (Claude + Gemini만으로도 충분)

### 3. GitHub Actions 미테스트

**영향**: Issue 기반 토론 자동화 작동 안 함
**해결**: GitHub 레포 생성 후 테스트

**우선순위**: 높음

---

## 📝 다음 작업 순서 (권장)

```
1. GitHub 레포 생성 및 연결 (10분) ⭐⭐⭐
2. BigQuery 테이블 생성 확인 (10분) ⭐⭐⭐
3. GCS 버킷 확인 (5분) ⭐⭐
4. GCP Service Account 생성 (15분) ⭐⭐⭐
5. GitHub Secrets 설정 (10분) ⭐⭐⭐
6. GitHub Actions 테스트 (20분) ⭐⭐⭐
7. Hooks 등록 (5분) ⭐
8. Perplexity API 생성 (선택, 5분) ⭐

총 예상 시간: 1-1.5시간
```

---

## 📞 연락처 및 참고자료

### 프로젝트 문서

- Plan 파일: `/home/wishingfly/.claude/plans/expressive-bubbling-riddle.md`
- README: `/home/wishingfly/multi-ai-orchestrator/README.md`
- SETUP: `/home/wishingfly/multi-ai-orchestrator/SETUP.md`

### 외부 문서

- Vertex AI 문서: https://cloud.google.com/vertex-ai/docs
- BigQuery ML: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-cosine-distance
- Claude API: https://docs.anthropic.com/
- Gemini API: https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini

---

## ✅ 완료 체크리스트 (다음 AI용)

```
Phase 7 완료 (나머지 50%):
□ GitHub 레포 생성 및 연결
□ GitHub CLI 설치
□ GCP Service Account 생성
□ GitHub Secrets 설정
□ BigQuery 테이블 확인/생성
□ GCS 버킷 확인/생성
□ Hooks 등록
□ GitHub Actions 테스트 (Issue 생성)
□ Vertex AI 동기화 테스트
□ 전체 통합 테스트 (E2E)

선택 사항:
□ Perplexity API 키 생성
□ 합의도 계산 개선 (임베딩 추가)
□ PR 자동 생성 기능 활성화
□ 자동 테스트 추가
```

---

## 🎓 핵심 개념 설명 (다음 AI가 알아야 할 것)

### 1. 토론 프로토콜

```
Round 1: Claude 제안 → Gemini 검토
Round 2: Gemini 대안 → Claude 반박
Round 3: 양측 절충안 → 합의도 계산
Round 4: Perplexity 판정 (합의도 70% 미만 시)

합의 기준:
≥85%: 자동 채택
70-85%: 사용자 검토
<70%: 토론 연장 or Perplexity
```

### 2. 합의도 계산

```python
# 현재: Jaccard similarity (키워드 기반)
consensus = len(claude_words ∩ gemini_words) / len(claude_words ∪ gemini_words)

# 향후: 임베딩 유사도 추가
consensus = 0.6 × embedding_similarity + 0.4 × keyword_similarity
```

### 3. Vertex AI RAG 검색

```python
# BigQuery 벡터 검색
ML.DISTANCE(embedding, query_embedding, 'COSINE') < threshold

# GCS 키워드 검색
if query.lower() in content.lower()
```

### 4. GitHub Actions 워크플로우

```
Issue 생성 [ai-debate]
  ↓
Actions 트리거
  ↓
multi_ai_runner.py 실행
  ↓
debate_engine.py 토론
  ↓
결과 커밋 + Issue 댓글
  ↓
합의도 85% 이상 시 Issue 종료
```

---

## 🔮 향후 개선 사항 (선택)

### 단기 (1주일)

1. 임베딩 기반 합의도 계산 추가
2. PR 자동 생성 기능 활성화
3. Vertex AI 학습 자동화

### 중기 (1개월)

1. Multi-AI 토론 대시보드 (Streamlit)
2. 토론 품질 메트릭 추가
3. 자동 테스트 커버리지 80%+

### 장기 (3개월)

1. 실시간 토론 (WebSocket)
2. 다른 프로젝트로 확장
3. 토론 결과 논문 작성

---

**인수인계 완료일**: 2026-01-19
**다음 체크포인트**: GitHub 레포 생성 후 첫 Issue 토론 성공

행운을 빕니다! 🚀
