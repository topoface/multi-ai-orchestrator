# 🎯 당신이 할 일 (30분)

**날짜**: 2026-01-19
**사전 작업 완료**: Git 초기화 ✅, 커밋 생성 ✅, 스크립트 준비 ✅

---

## ✅ 이미 완료된 것 (Claude가 처리함)

- ✅ Git 레포 초기화
- ✅ 모든 파일 커밋 완료
- ✅ 브랜치 main으로 설정
- ✅ setup_gcp.sh 스크립트 생성
- ✅ setup_github.sh 스크립트 생성
- ✅ 완전한 가이드 문서 작성

---

## 📋 당신이 할 3가지 (순서대로)

### ⭐ Task 1: GCP 인프라 구축 (15분)

**1.1 Cloud Shell 열기**

```
https://console.cloud.google.com/?project=phsysics
```

→ 상단 툴바에서 "Activate Cloud Shell" 아이콘 클릭

**1.2 스크립트 업로드**

- Cloud Shell 우상단 "⋮" 메뉴 → "Upload"
- 파일 선택: `/home/wishingfly/multi-ai-orchestrator/setup_gcp.sh`

**1.3 실행**

```bash
chmod +x setup_gcp.sh
./setup_gcp.sh
```

**1.4 Key 복사 (중요!)**

```bash
cat sa-key.json
```

→ 전체 내용 복사 (메모장에 임시 저장)
→ GitHub Secrets에 사용됨

```bash
rm sa-key.json  # 보안을 위해 삭제
```

---

### ⭐ Task 2: GitHub 레포 생성 및 푸시 (10분)

**2.1 GitHub 레포 생성**

```
https://github.com/new
```

설정:

- Owner: `topoface`
- Repository name: `multi-ai-orchestrator`
- Visibility: `Public` (권장) 또는 `Private`
- ❌ **중요**: "Initialize this repository with..." 모두 체크 해제!
- "Create repository" 클릭

**2.2 로컬에서 푸시**

WSL에서 실행:

```bash
cd /home/wishingfly/multi-ai-orchestrator
git remote add origin https://github.com/topoface/multi-ai-orchestrator.git
git push -u origin main
```

인증 요청 시:

```bash
# GitHub 토큰 필요할 수 있음
# Settings → Developer settings → Personal access tokens
# 또는
gh auth login  # GitHub CLI 사용
```

---

### ⭐ Task 3: GitHub Secrets 설정 (5분)

**3.1 Secrets 페이지 열기**

```
https://github.com/topoface/multi-ai-orchestrator/settings/secrets/actions
```

**3.2 Secrets 추가** (New repository secret 클릭)

**Secret #1**: `ANTHROPIC_API_KEY`

```
sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Secret #2**: `GEMINI_API_KEY`

```
AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Secret #3**: `GCP_SA_KEY`

```
[Task 1.4에서 복사한 sa-key.json 전체 내용]
```

**Secret #4**: `PERPLEXITY_API_KEY` (선택, 나중에)

```
(아직 없음 - 건너뛰기)
```

---

## 🧪 완료 후 테스트

### 방법 1: GitHub CLI

```bash
gh issue create \
  --title "[Debate] 테스트: RTL 최적화 방법" \
  --body "Claude와 Gemini가 RTL 곱셈 최적화 방법에 대해 토론합니다." \
  --label "ai-debate"
```

### 방법 2: 웹 UI

```
https://github.com/topoface/multi-ai-orchestrator/issues/new
```

- Title: `[Debate] 테스트: RTL 최적화 방법`
- Body: 자유롭게 작성
- Labels: `ai-debate` 선택
- Submit

### 기대 결과

- ✅ GitHub Actions 자동 실행
- ✅ Claude + Gemini 토론 진행 (4 라운드)
- ✅ 결과가 Issue 댓글로 작성됨
- ✅ docs/brain/DECISIONS.md 자동 업데이트
- ✅ 합의도 85% 이상 시 Issue 자동 종료

---

## 📊 진행 체크리스트

```
로컬 작업 (Claude 완료):
✅ Git 초기화
✅ 모든 파일 커밋
✅ 브랜치 main 설정
✅ 스크립트 생성

당신의 작업:
□ Cloud Shell에서 setup_gcp.sh 실행
□ sa-key.json 복사 및 저장
□ GitHub 레포 생성 (topoface/multi-ai-orchestrator)
□ git push origin main
□ GitHub Secrets 3개 추가 (ANTHROPIC, GEMINI, GCP_SA_KEY)
□ 테스트 Issue 생성
□ Actions 실행 확인
□ 첫 AI 토론 성공 확인!
```

---

## 🆘 문제 발생 시

### "already exists" 에러

→ 무시하고 다음 단계 진행 (이미 생성된 리소스)

### git push 인증 실패

```bash
gh auth login
# 또는
git config credential.helper store
```

### Actions 실행 안 됨

→ Secrets 3개 모두 추가했는지 확인

---

## 📞 상세 가이드

막히면 이 문서들 참고:

- `SETUP_INSTRUCTIONS.md` (이 폴더)
- `HANDOFF.md` (전체 인수인계)
- `QUICK_HANDOFF.md` (빠른 요약)

---

**예상 완료 시간**: 30분
**성공하면**: Multi-AI 토론 시스템 완전 작동! 🎉

시작하세요! 막히면 바로 물어보세요.
