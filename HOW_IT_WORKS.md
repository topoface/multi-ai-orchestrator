# 🔍 동작 원리 상세 설명

## 🎯 전체 흐름도

```
사용자 질문: "RTL 곱셈을 어떻게 최적화하지?"
        ↓
┌───────────────────────────────────────────────────┐
│ 1️⃣ 토론 시작 (debate_engine.py)                    │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│ Round 1: Claude 제안                               │
│   → Anthropic API 호출                             │
│   → "방법 A: 파이프라인 최적화"                      │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│ Round 1: Gemini 검토                               │
│   → Gemini API 호출                                │
│   → "방법 B: 병렬 처리가 더 나음"                    │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│ 합의도 계산                                         │
│   → 키워드 유사도: 40%                              │
│   → 의미론적 유사도: 50% (임베딩)                    │
│   → 최종: 45% (계속 토론)                           │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│ Round 2: 반복...                                   │
│   → 합의도 72%                                     │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│ Round 3: 절충안                                    │
│   → 합의도 88% ✓ (85% 이상!)                       │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│ 2️⃣ 결과 저장 (decision_logger.py)                  │
│   → docs/brain/DECISIONS.md 업데이트                │
│   → debate_20250117_210530.json 생성               │
└───────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────┐
│ 3️⃣ Vertex AI 동기화 (vertex_learner.py)            │
│   → 텍스트 → 임베딩 (768차원 벡터)                  │
│   → BigQuery 저장 (검색용)                          │
│   → GCS 백업 (원본 보관)                            │
└───────────────────────────────────────────────────┘
        ↓
        완료! 🎉
```

---

## 🧠 핵심 컴포넌트 동작

### 1. Debate Engine (토론 엔진)

**파일**: `.claude/skills/debate-request/debate_engine.py`

**하는 일**:
```python
# 1. Claude API 호출
claude_response = anthropic.messages.create(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": "RTL 곱셈 최적화 방법?"}]
)

# 2. Gemini API 호출
gemini_response = genai_model.generate_content(
    "Claude는 A를 제안했는데, 당신 생각은?"
)

# 3. 합의도 계산
consensus = calculate_similarity(claude_text, gemini_text)

# 4. 결과 저장
save_result({
    "topic": "RTL 곱셈 최적화",
    "consensus": 0.88,
    "claude_position": "...",
    "gemini_position": "..."
})
```

---

### 2. Vertex AI Learner (지식 학습)

**파일**: `.claude/agents/vertex-learner/vertex_learner.py`

**하는 일**:
```python
# 1. 텍스트를 읽음
text = "RTL 곱셈 최적화는 파이프라인 기법을..."

# 2. 임베딩 생성 (Vertex AI API)
embedding = embedding_model.get_embeddings([text])[0]
# → [0.123, -0.456, 0.789, ...] (768개 숫자)

# 3. BigQuery 저장
bigquery.insert_rows({
    "content": text,
    "embedding": embedding,  # 검색에 사용
    "metadata": {"type": "decision", "date": "2025-01-17"}
})

# 4. GCS 백업
gcs.upload(text, "decisions/decision_20250117.txt")
```

**왜 이렇게?**
- BigQuery: 임베딩으로 **의미론적 검색** 가능
- GCS: 원본 텍스트 **영구 보관**

---

### 3. GitHub Sync (동기화)

**파일**: `.claude/skills/github-sync/sync_manager.py`

**GitHub → Vertex AI**:
```python
# 1. 변경된 파일 찾기
changed_files = git_diff("docs/brain/")
# → ["DECISIONS.md", "CONTEXT.md"]

# 2. 각 파일 임베딩 생성
for file in changed_files:
    text = read_file(file)
    embedding = generate_embedding(text)
    bigquery.insert(text, embedding)
    gcs.backup(text)
```

**Vertex AI → GitHub**:
```python
# 1. GCS에서 최신 결정 가져오기
latest_decisions = gcs.list("decisions/", limit=5)

# 2. docs/brain/DECISIONS.md 업데이트
for decision in latest_decisions:
    append_to_file("docs/brain/DECISIONS.md", decision)

# 3. 자동 커밋
git_commit("Update decisions from Vertex AI")
```

---

### 4. GitHub Actions (자동화)

**파일**: `.github/workflows/ai-debate-trigger.yml`

**Issue 생성 시 자동 실행**:
```yaml
on:
  issues:
    types: [opened, labeled]

jobs:
  run-debate:
    runs-on: ubuntu-latest
    steps:
      - name: Issue 내용 읽기
        run: |
          TOPIC=$(gh issue view $ISSUE_NUMBER --json title)

      - name: 토론 실행
        run: |
          python .github/scripts/multi_ai_runner.py \
            --topic "$TOPIC" \
            --issue-number $ISSUE_NUMBER

      - name: 결과를 Issue에 댓글
        run: |
          gh issue comment $ISSUE_NUMBER --body "$RESULT"

      - name: 합의 도달 시 Issue 종료
        run: |
          if [ $CONSENSUS -ge 85 ]; then
            gh issue close $ISSUE_NUMBER
          fi
```

---

## 🔍 실제 코드 예시

### 예시 1: 토론 시작

```python
# scripts/auto-debate.py
from debate_engine import DebateEngine

# 토론 엔진 생성
engine = DebateEngine(
    topic="RTL 곱셈 최적화",
    max_rounds=4
)

# 토론 실행
result = engine.conduct_debate()

# 결과:
# {
#   "topic": "RTL 곱셈 최적화",
#   "rounds": 3,
#   "consensus_score": 0.88,
#   "claude_final_position": "파이프라인 + 병렬 조합",
#   "gemini_final_position": "동일한 접근",
#   "status": "adopted"
# }
```

---

### 예시 2: 검색

```python
# .claude/skills/vertex-search/vertex_search.py
from vertex_learner import VertexLearner

learner = VertexLearner()

# 검색어 임베딩
query_embedding = learner.get_embedding("NoiseComputer 곱셈")

# BigQuery 유사도 검색
results = bigquery.query(f"""
    SELECT content,
           ML.DISTANCE(embedding, {query_embedding}, 'COSINE') as distance
    FROM knowledge_base.embeddings
    WHERE distance < 0.3  -- 유사도 70% 이상
    ORDER BY distance ASC
    LIMIT 10
""")

# 결과:
# [
#   {"content": "NoiseComputer 256x256...", "similarity": 0.92},
#   {"content": "RTL 곱셈 최적화...", "similarity": 0.85},
#   ...
# ]
```

---

## 📊 데이터 흐름

### 토론 → 저장 → 검색

```
1️⃣ 토론 진행
   ↓
debate_result.json 생성
   {
     "topic": "RTL 곱셈",
     "consensus": 0.88,
     "claude_position": "방법 A+B",
     "gemini_position": "동의"
   }

2️⃣ 파일 저장
   ↓
docs/brain/DECISIONS.md 업데이트
   ## Decision: RTL 곱셈 최적화
   **Consensus**: 88%
   방법 A와 B를 조합...

3️⃣ Vertex AI 동기화
   ↓
임베딩 생성 (768차원 벡터)
   [0.123, -0.456, 0.789, ...]
   ↓
BigQuery 저장
   content        | embedding       | metadata
   "방법 A와 B..." | [0.123, ...]   | {"type":"decision"}
   ↓
GCS 백업
   gs://bucket/decisions/decision_20250117.json

4️⃣ 나중에 검색
   ↓
"곱셈 최적화" 검색
   ↓
임베딩 생성 → BigQuery 유사도 검색
   ↓
과거 결정 찾기: "RTL 곱셈 최적화" (92% 유사도)
```

---

## 🎛️ 설정 파일

### debate_config.yaml

```yaml
debate:
  max_rounds: 4              # 최대 4라운드
  consensus_threshold: 0.85  # 85% 이상이면 자동 채택
  expert_threshold: 0.70     # 70% 미만이면 Perplexity 호출

participants:
  claude:
    model: claude-sonnet-4-5-20250929
    temperature: 0.7         # 창의성 (0=확정적, 1=창의적)
    max_tokens: 4096

  gemini:
    model: gemini-2.0-flash-exp
    temperature: 0.7
    max_tokens: 4096

  perplexity:
    model: llama-3.1-sonar-large-128k-online
    temperature: 0.5         # 전문가는 더 확정적
    enabled: true

agreement_scoring:
  embedding_weight: 0.6      # 의미론적 유사도 가중치
  keyword_weight: 0.4        # 키워드 유사도 가중치
```

---

### vertex_config.yaml

```yaml
project_id: phsysics
location: us-central1

bigquery:
  dataset: my_physics_agent_stackoverflow_data
  table: questions_embeddings
  knowledge_dataset: knowledge_base
  knowledge_table: embeddings

gcs:
  bucket: multi-ai-memory-bank-phsysics
  folders:
    context: context/
    decisions: decisions/
    session_logs: session_logs/

embedding:
  model: textembedding-gecko@003
  dimensions: 768            # 임베딩 벡터 크기
  batch_size: 100           # 한 번에 100개씩 처리

search:
  similarity_threshold: 0.7  # 최소 유사도 70%
  max_results: 10           # 최대 10개 결과
```

---

## 🚀 실행 흐름 요약

### 로컬 실행
```bash
python scripts/auto-debate.py "주제"
   ↓
debate_engine.py 실행
   ↓ (API 호출)
Claude ↔ Gemini 토론
   ↓
결과 저장 (docs/brain/)
   ↓
완료!
```

### GitHub 실행
```bash
Issue 생성 "[Debate] 주제"
   ↓
GitHub Actions 트리거
   ↓
multi_ai_runner.py 실행
   ↓
Claude ↔ Gemini 토론
   ↓
결과 커밋 + Issue 댓글
   ↓
vertex-sync.yml 트리거
   ↓
Vertex AI 동기화
   ↓
완료!
```

---

## 💡 핵심 포인트

1. **모든 토론은 자동 저장** (GitHub + Vertex AI)
2. **임베딩으로 의미론적 검색** 가능
3. **GitHub Actions로 완전 자동화** 가능
4. **API 키만 있으면 로컬에서 무료** 사용
5. **모든 코드는 Python으로 작성** (수정 쉬움)

---

## 🔧 커스터마이징

### 토론 라운드 변경
```yaml
# config/debate_config.yaml
max_rounds: 2  # 빠른 토론
```

### 합의 기준 변경
```yaml
consensus_threshold: 0.90  # 90% 이상 요구
```

### 모델 변경
```yaml
participants:
  claude:
    model: claude-opus-4-5  # 더 강력한 모델
```

### 검색 정확도 조정
```yaml
search:
  similarity_threshold: 0.8  # 80% 이상만
  max_results: 20           # 더 많은 결과
```
