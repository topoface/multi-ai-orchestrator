# Multi-AI Orchestrator 빠른 설정 가이드

**작성일**: 2026-01-19
**예상 시간**: 30분

---

## 🎯 3단계로 완료하기

### ✅ 사전 준비 (완료됨)

- BigQuery Dataset `knowledge_base` 생성 완료
- 로컬 코드 구현 완료 (85%)
- API 키 설정 완료 (.env)

---

## 📋 Step 1: GCP 인프라 구축 (15분)

### 방법 A: Cloud Shell에서 스크립트 실행 (권장)

1. **Cloud Shell 열기**:
   - https://console.cloud.google.com/?project=phsysics
   - 상단 툴바에서 "Activate Cloud Shell" 클릭

2. **스크립트 업로드**:

   ```bash
   # 로컬 파일을 Cloud Shell로 업로드
   # Cloud Shell 웹 UI에서 "Upload File" 버튼 클릭
   # → setup_gcp.sh 선택
   ```

3. **실행**:

   ```bash
   chmod +x setup_gcp.sh
   ./setup_gcp.sh
   ```

4. **sa-key.json 복사**:

   ```bash
   cat sa-key.json
   # 전체 내용 복사 (GitHub Secrets에 사용)

   rm sa-key.json  # 복사 후 삭제
   ```

### 방법 B: 수동 실행

Cloud Shell에서 아래 명령어를 하나씩 실행:

```bash
# 1. BigQuery Table
bq mk --table \
  --schema='[
    {"name":"content","type":"STRING","mode":"REQUIRED"},
    {"name":"embedding","type":"FLOAT64","mode":"REPEATED"},
    {"name":"metadata","type":"JSON","mode":"NULLABLE"},
    {"name":"created_at","type":"TIMESTAMP","mode":"NULLABLE"},
    {"name":"source","type":"STRING","mode":"NULLABLE"}
  ]' \
  phsysics:knowledge_base.embeddings

# 2. GCS Bucket
gsutil mb -p phsysics -l us-central1 gs://multi-ai-memory-bank-phsysics/
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/context/.keep
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/decisions/.keep
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/session_logs/.keep

# 3. Service Account
gcloud iam service-accounts create multi-ai-orchestrator \
  --project=phsysics \
  --display-name="Multi-AI Orchestrator"

# 4. 권한 부여
gcloud projects add-iam-policy-binding phsysics \
  --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding phsysics \
  --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# 5. Key 생성
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=multi-ai-orchestrator@phsysics.iam.gserviceaccount.com

cat sa-key.json  # 복사
rm sa-key.json   # 삭제
```

---

## 📋 Step 2: GitHub 레포 생성 및 푸시 (10분)

### 2.1 GitHub 레포 생성

1. https://github.com/new 접속
2. 설정:
   - **Owner**: topoface
   - **Repository name**: multi-ai-orchestrator
   - **Visibility**: Public (권장)
   - **❌ Initialize 체크 해제** (README, license, gitignore 모두 해제)
3. "Create repository" 클릭

### 2.2 로컬 코드 푸시

```bash
cd /home/wishingfly/multi-ai-orchestrator
./setup_github.sh
```

**또는 수동**:

```bash
cd /home/wishingfly/multi-ai-orchestrator
git init
git add .
git commit -m "Initial commit: Multi-AI Orchestrator v1.0"
git branch -M main
git remote add origin https://github.com/topoface/multi-ai-orchestrator.git
git push -u origin main
```

---

## 📋 Step 3: GitHub Secrets 설정 (5분)

1. **GitHub Secrets 페이지 열기**:
   - https://github.com/topoface/multi-ai-orchestrator/settings/secrets/actions

2. **Secrets 추가** (New repository secret):

   **Secret 1: ANTHROPIC_API_KEY**

   ```bash
   # 로컬에서 확인:
   grep ANTHROPIC_API_KEY /home/wishingfly/multi-ai-orchestrator/.env
   # 값 복사해서 추가
   ```

   **Secret 2: GEMINI_API_KEY**

   ```bash
   # 로컬에서 확인:
   grep GEMINI_API_KEY /home/wishingfly/multi-ai-orchestrator/.env
   # 값 복사해서 추가
   ```

   **Secret 3: GCP_SA_KEY**

   ```
   # Step 1에서 복사한 sa-key.json 전체 내용
   # JSON 형식 전체를 붙여넣기
   ```

   **Secret 4: PERPLEXITY_API_KEY** (선택)

   ```
   # 나중에 추가 가능
   ```

---

## 🧪 테스트

### 방법 1: GitHub Issue 생성

```bash
# GitHub CLI 설치되어 있다면:
gh issue create \
  --title "[Debate] Test Multi-AI System" \
  --body "Testing the automated Multi-AI debate system. This should trigger Claude + Gemini collaboration." \
  --label "ai-debate"

# Actions 실행 확인
gh run watch
```

### 방법 2: 웹 UI에서 생성

1. https://github.com/topoface/multi-ai-orchestrator/issues/new
2. Title: `[Debate] Test Multi-AI System`
3. Body: `Testing automated debate`
4. Labels: `ai-debate`
5. Submit

### 기대 결과

- GitHub Actions 자동 실행
- Claude + Gemini 토론 진행
- 결과가 Issue 댓글로 작성됨
- 합의도 85% 이상이면 자동 종료

---

## 📊 완료 체크리스트

```
□ BigQuery Dataset 생성 ✅
□ BigQuery Table 생성
□ GCS Bucket 생성
□ Service Account 생성
□ 권한 부여
□ SA Key 생성 및 복사
□ GitHub 레포 생성
□ 로컬 코드 푸시
□ GitHub Secrets 설정 (3-4개)
□ 테스트 Issue 생성
□ Actions 실행 확인
□ 첫 AI 토론 성공!
```

---

## 🆘 문제 해결

### "already exists" 에러

```bash
# 무시하고 다음 단계 진행
# 이미 생성된 리소스임
```

### Git push 실패

```bash
# 인증 확인
gh auth status

# 다시 로그인
gh auth login
```

### Actions 실행 안 됨

```bash
# Secrets 확인
# Settings → Secrets → Actions
# 4개 모두 추가되었는지 확인
```

---

## 📞 도움말

- **상세 문서**: `/home/wishingfly/multi-ai-orchestrator/HANDOFF.md`
- **빠른 문서**: `/home/wishingfly/multi-ai-orchestrator/QUICK_HANDOFF.md`
- **프로젝트 계획**: `~/.claude/plans/expressive-bubbling-riddle.md`

---

**예상 완료 시간**: 30분
**성공 기준**: GitHub Issue 생성 시 자동으로 AI 토론 실행 및 결과 댓글 작성
