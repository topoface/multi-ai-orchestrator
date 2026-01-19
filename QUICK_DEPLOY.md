# ⚡ 초고속 배포 가이드

**목표**: 30분 안에 웹 챗봇 완성!

---

## 🚀 3단계로 끝내기

### 1️⃣ Cloud Functions 배포 (10분)

```bash
cd /home/wishingfly/multi-ai-orchestrator

# API 키 설정
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export GEMINI_API_KEY="AIzaSyxxxxx"

# 배포!
./deploy.sh
```

**URL 2개 나옴** → 메모하세요!

---

### 2️⃣ Agent Builder 설정 (15분)

**A. Agent 만들기**
```
1. https://console.cloud.google.com/
2. "Vertex AI Agent Builder" 검색
3. "Create Agent"
   - 이름: Multi-AI Orchestrator
   - 언어: Korean
```

**B. Data Store 연결**
```
Add Data Store:
  - BigQuery: phsysics.knowledge_base.embeddings
  - GCS: gs://multi-ai-memory-bank-phsysics/
```

**C. Webhook 설정**
```
Open in Dialogflow CX
→ Manage → Webhooks → Create

Webhook 1:
  Name: multi-ai-debate
  URL: [1단계에서 받은 debate URL]

Webhook 2:
  Name: multi-ai-search
  URL: [1단계에서 받은 search URL]
```

**D. Intent 추가**
```
Build → Start → Add route

Route 1 - 토론:
  Intent phrases: "토론해줘", "[주제] 토론"
  Webhook: multi-ai-debate

Route 2 - 검색:
  Intent phrases: "검색해줘", "[검색어] 찾아줘"
  Webhook: multi-ai-search
```

---

### 3️⃣ 웹 UI 활성화 (5분)

```
Manage → Integrations
→ Dialogflow Messenger → Enable
→ URL 받기!
```

**완성!** 🎉

웹 URL: `https://dialogflow.cloud.google.com/messenger/xxxxx`

---

## ✅ 테스트

웹 브라우저 열고:

```
You: 안녕
Bot: 안녕하세요! Multi-AI 협업 시스템입니다.

You: Python vs JavaScript 토론해줘
Bot: (토론 중...)
     🤖 토론 완료!
     합의도: 82%
     ...
```

---

## 🎯 끝!

**PC/핸드폰 어디서든 접속 가능!**

자세한 설명: `VERTEX_AI_SETUP.md` 참고

---

## 🔥 문제 해결

**배포 실패?**
```bash
gcloud auth login
gcloud config set project phsysics
./deploy.sh
```

**Webhook 오류?**
- Timeout을 300초로 설정
- Cloud Functions 로그 확인:
  ```bash
  gcloud functions logs read multi-ai-debate --limit=50
  ```

**검색 결과 없음?**
```bash
# 데이터 업로드
python3 scripts/vertex_github_bridge.py --to-vertex --initial-sync
```
