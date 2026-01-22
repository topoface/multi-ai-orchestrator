# Multi-AI Orchestrator - Product Requirements Document (PRD)

**작성일**: 2026-01-22
**버전**: 1.0
**상태**: Phase 1 진행 중

---

## 🎯 프로젝트 비전

**Self-Improving AI System (자가 학습 AI 시스템)**

Vertex AI가 모르는 질문 → 조력 AI 토론 → 합의된 답변 학습 → Vertex AI 지식 확장

```
반복할수록 Vertex AI가 똑똑해지는 선순환 구조
```

---

## 📋 개발 로드맵

### ✅ Phase 0: 기반 구축 (완료)

**기간**: 2026-01-17 ~ 2026-01-21
**상태**: 완료

**구현 내용**:

- [x] GitHub 레포 생성
- [x] 디렉토리 구조 구축
- [x] debate_engine.py 구현 (Claude + Gemini + Perplexity)
- [x] GitHub Actions 워크플로우
- [x] Hooks 구현 (sync-to-vertex, sync-to-supabase, auto-git-commit)
- [x] Supabase 연동

**결과물**:

- 작동하는 Multi-AI 토론 엔진
- 자동 동기화 시스템

---

### 🔥 Phase 1: 토론 시스템 검증 (현재)

**기간**: 2026-01-22 ~ 2026-01-23 (2일)
**상태**: 진행 중
**우선순위**: P0 (최우선)

#### 목표

로컬 실행으로 토론 시스템이 **확실히 작동**하는지 검증

#### 체크리스트

**1.1 토론 실행 검증**

- [ ] 로컬에서 토론 명령어 실행
  ```bash
  cd /home/wishingfly/multi-ai-orchestrator
  python .claude/skills/debate-request/debate_engine.py "vertex ai의 장기 기억 및 맥락 유지를 위해 파인튜닝이 좋은가? RAG가 좋은가? 각각의 장단점을 토론해서 합의된 결과를 내게 줘"
  ```
- [ ] Claude, Gemini, Perplexity 모두 정상 응답
- [ ] 3 라운드 내 합의 도달
- [ ] Perplexity 승인 확인
- [ ] 합의도 점수 계산 확인

**1.2 자동 저장 검증**

- [ ] `docs/brain/debate_*.json` 파일 생성 확인
- [ ] JSON 파일 구조 검증:
  - topic, timestamp, status
  - claude_final_position, gemini_final_position
  - perplexity_final_judgment
  - consensus_score
- [ ] 파일 크기 적절 (10~100KB)

**1.3 자동 동기화 검증**

- [ ] Supabase 저장 확인
  - 테이블: debates
  - ID, topic, status, consensus_score
- [ ] Vertex AI GCS 업로드 확인
  - 경로: `gs://multi-ai-memory-bank-phsysics/context/debate_*.json`
  - 메타데이터 확인
- [ ] Git 자동 커밋 확인
  - Hook: auto-git-commit.py 실행
  - 커밋 메시지 형식 확인

**1.4 에러 처리 검증**

- [ ] API 키 누락 시 명확한 에러 메시지
- [ ] 네트워크 오류 시 재시도 로직
- [ ] 토론 실패 시 로그 저장
- [ ] Hook 실패 시에도 메인 토론은 완료

**1.5 성능 검증**

- [ ] 토론 완료 시간 측정 (목표: 5분 이내)
- [ ] API 호출 횟수 확인
- [ ] 토큰 사용량 측정
  - Claude: 라운드당 ~1,000 토큰
  - Gemini: 라운드당 ~1,000 토큰
  - Perplexity: 라운드당 ~500 토큰

#### 성공 기준

- ✅ 토론 5회 실행하여 모두 성공
- ✅ 자동 동기화 5/5 성공
- ✅ 저장된 데이터 품질 확인
- ✅ 에러 없이 안정적 작동

#### 산출물

- `PHASE1_VALIDATION_REPORT.md` 문서
  - 실행 로그 5개
  - 성공/실패 분석
  - 발견된 이슈 목록

---

### 🚀 Phase 2: BigQuery 임베딩 시스템 (예정)

**기간**: Phase 1 완료 후 1주
**상태**: 대기
**우선순위**: P1 (중요하지만 급하지 않음)

#### 트리거 조건

Phase 1 검증 완료 **AND** 다음 중 하나:

- [ ] 토론 결과 10개 이상 축적
- [ ] Vertex AI 검색 속도 개선 필요
- [ ] 의미 기반 검색 필요성 확인

#### 목표

토론 결과의 **초고속 의미 기반 검색**

#### 구현 내용

**2.1 BigQuery 테이블 생성**

```sql
CREATE TABLE phsysics.knowledge_base.debate_embeddings (
  id STRING,
  topic STRING,
  debate_date TIMESTAMP,
  content TEXT,              -- 토론 전문
  summary TEXT,              -- 요약
  embedding ARRAY<FLOAT64>,  -- 768차원 벡터 (textembedding-gecko@003)
  consensus_score FLOAT64,
  status STRING,
  created_at TIMESTAMP
)
```

**2.2 임베딩 생성 자동화**

- Hook: `auto-generate-embedding.py` 추가
- 토론 완료 시 자동 실행
- Vertex AI Embedding API 호출
  - 모델: `textembedding-gecko@003`
  - 입력: topic + claude_final + gemini_final
  - 출력: 768차원 벡터
- BigQuery INSERT

**2.3 검색 API 구현**

```python
def search_similar_debates(query: str, top_k: int = 5):
    """
    질문과 유사한 과거 토론 검색

    Args:
        query: 검색 질문
        top_k: 상위 N개 결과

    Returns:
        유사도 순 토론 결과 리스트
    """
    # 1. 질문 임베딩
    query_embedding = generate_embedding(query)

    # 2. BigQuery 코사인 유사도 검색
    sql = f"""
    SELECT
      id, topic, content, consensus_score,
      ML.DISTANCE(embedding, {query_embedding}, 'COSINE') as similarity
    FROM phsysics.knowledge_base.debate_embeddings
    ORDER BY similarity ASC
    LIMIT {top_k}
    """

    # 3. 결과 반환
    return execute_query(sql)
```

**2.4 기존 토론 일괄 임베딩**

- 스크립트: `scripts/backfill_embeddings.py`
- 모든 `docs/brain/debate_*.json` 읽기
- 임베딩 생성 후 BigQuery INSERT
- 예상 시간: 10개당 ~30초

#### 비용 산정

- **임베딩 생성**: $0.025/1,000자
  - 토론 1개: 약 3,000자 → **$0.075 (105원)**
  - 월 30개: **$2.25 (3,150원)**
- **BigQuery 저장**: $0.02/GB
  - 1,000개 토론: ~100MB → **$0.002 (3원)**
- **BigQuery 쿼리**: $5/TB
  - 검색 1회: ~1MB → **$0.000005 (거의 공짜)**

**월 예상 비용**: **$2.5 (3,500원)**

#### 성공 기준

- ✅ 검색 속도: 0.5초 이내
- ✅ 의미 기반 검색 정확도: 80% 이상
- ✅ 동의어 검색 성공 (예: "RAG" ↔ "검색 증강 생성")
- ✅ 자동화 안정성: 100% 성공률

#### 산출물

- BigQuery 테이블 스키마
- `auto-generate-embedding.py` Hook
- `search_similar_debates()` API
- `PHASE2_EMBEDDING_REPORT.md` 문서

---

### 📊 Phase 3: Vertex AI 재학습 자동화 (미래)

**기간**: Phase 2 완료 후 2주
**상태**: 계획
**우선순위**: P2 (개선 사항)

#### 목표

토론 결과로 Vertex AI 자동 재학습 → 지식 확장

#### 구현 아이디어

1. **RAG 업데이트**
   - BigQuery 임베딩 → Vertex AI RAG Corpus 자동 추가
   - 검색 시 최신 토론 결과 반영

2. **파인튜닝 트리거** (선택적)
   - 토론 100개 축적 시 자동 파인튜닝 제안
   - 사용자 승인 후 실행

3. **지식 검증**
   - 같은 질문 재시도 → Vertex AI가 바로 답변하는지 확인

#### 예상 시점

- 토론 결과 50~100개 축적 후
- Phase 2 안정화 확인 후

---

## 📈 측정 지표 (KPI)

### Phase 1 지표

- **토론 성공률**: 목표 95% 이상
- **평균 합의도**: 목표 70% 이상
- **평균 실행 시간**: 목표 5분 이내
- **자동화 성공률**: 목표 100%

### Phase 2 지표 (추가)

- **검색 속도**: 목표 0.5초 이내
- **검색 정확도**: 목표 80% 이상
- **월 비용**: 목표 $5 이하

### Phase 3 지표 (추가)

- **Vertex AI 질문 자답률**: Day 1 → 70%, Day 30 → 95%
- **토론 호출 빈도**: Day 1 → 30%, Day 30 → 5%

---

## 🔄 운영 방식 (Phase 1 기준)

### 로컬 실행 (현재)

```bash
# 토론 실행
cd /home/wishingfly/multi-ai-orchestrator
python .claude/skills/debate-request/debate_engine.py "질문 내용"

# 자동으로:
# 1. docs/brain/ 저장
# 2. Supabase 저장
# 3. Vertex AI GCS 업로드
# 4. Git 커밋
```

### GitHub 연동 (미래 - Private 레포 이슈 해결 후)

- Issue 생성 → GitHub Actions 자동 실행
- Markdown 템플릿 사용
- 결과를 Issue 댓글로 자동 추가

---

## 🚧 알려진 제약사항

### Phase 1

1. **GitHub Issue Forms 미작동**
   - 원인: Private 레포에서 .yml 템플릿 미지원
   - 우회: 로컬 실행 사용
   - 해결: Markdown 템플릿 추가 완료

2. **Perplexity 가짜 합의 감지**
   - 문제: "좋습니다, 하지만..." 식 응답을 합의로 오인
   - 해결: 프롬프트 개선 완료 (2026-01-21)

3. **토론 주제 이탈**
   - 문제: 세부 구현으로 발산
   - 해결: 원래 질문 리마인더 추가 완료 (2026-01-21)

### Phase 2 (예상)

1. **임베딩 비용**
   - 월 30개 토론: ~$2.5 (3,500원)
   - 관리 방법: 월별 모니터링

2. **BigQuery 쿼리 최적화**
   - 1,000개 이상 시 인덱싱 필요

---

## 📞 의사결정 기록

### 2026-01-22: Phase 순서 결정

**결정**: Phase 1 완료 → Phase 2 진행
**이유**:

- 토론 시스템 안정성 우선 확보
- BigQuery 임베딩은 토론 10개+ 축적 후 효과 극대화
- 점진적 개선으로 리스크 최소화

**승인자**: 사용자

---

## 📝 다음 액션

### 즉시 (오늘)

1. [ ] Phase 1 토론 첫 실행
2. [ ] 결과 검증 (저장, 동기화)
3. [ ] 이슈 발견 시 즉시 수정

### 이번 주

1. [ ] 토론 5회 실행하여 안정성 검증
2. [ ] `PHASE1_VALIDATION_REPORT.md` 작성
3. [ ] Phase 2 Go/No-Go 결정

### 다음 주 (Phase 2 시작 시)

1. [ ] BigQuery 테이블 생성
2. [ ] 임베딩 Hook 구현
3. [ ] 기존 토론 일괄 임베딩

---

## 🎯 최종 목표

**3개월 후**:

- Vertex AI가 95% 질문에 즉시 답변
- 조력 AI 토론은 5%만 필요
- 자가 학습 루프 완전 자동화

**Self-Improving AI System 완성!** 🚀

---

**문서 업데이트**: Phase 진행 시마다 체크리스트 업데이트
**다음 리뷰**: Phase 1 완료 후
