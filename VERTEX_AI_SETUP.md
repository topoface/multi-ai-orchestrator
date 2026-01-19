# 🚀 Vertex AI Agent Builder 설정 가이드

**목표**: 웹/모바일에서 접속 가능한 Multi-AI 챗봇 만들기

**소요 시간**: 1-2시간

---

## ✅ 사전 준비

### 1. API 키 확인

```bash
# 터미널에서 확인
echo $ANTHROPIC_API_KEY
echo $GEMINI_API_KEY
```

없으면:
- Claude: https://console.anthropic.com/
- Gemini: https://makersuite.google.com/app/apikey

### 2. GCP 프로젝트 확인

```bash
gcloud config get-value project
# → phsysics
```

---

## 📦 1단계: Cloud Functions 배포 (30분)

### 1.1 환경 변수 설정

```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export GEMINI_API_KEY="AIzaSyxxxxx"
export GCP_PROJECT_ID="phsysics"
export GCP_REGION="us-central1"
```

### 1.2 배포 실행

```bash
cd /home/wishingfly/multi-ai-orchestrator
./deploy.sh
```

**출력 예시**:
```
🚀 Multi-AI Orchestrator Cloud Functions 배포
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Debate Function 배포 중...
✅ Debate Function 배포 완료!
   URL: https://us-central1-phsysics.cloudfunctions.net/multi-ai-debate

2️⃣  Search Function 배포 중...
✅ Search Function 배포 완료!
   URL: https://us-central1-phsysics.cloudfunctions.net/multi-ai-search

🎉 모든 Cloud Functions 배포 완료!
```

**⚠️ URL을 메모하세요!** (나중에 사용)

### 1.3 테스트

```bash
# Debate 테스트
curl -X POST https://us-central1-phsysics.cloudfunctions.net/multi-ai-debate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python vs JavaScript"}'

# Search 테스트
curl -X POST https://us-central1-phsysics.cloudfunctions.net/multi-ai-search \
  -H "Content-Type: application/json" \
  -d '{"query": "NoiseComputer"}'
```

---

## 🤖 2단계: Vertex AI Agent Builder 설정 (30-60분)

### 2.1 Agent Builder 접속

1. GCP Console → https://console.cloud.google.com/
2. 검색창에 "Vertex AI Agent Builder" 입력
3. "Agent Builder" 클릭

### 2.2 새 Agent 만들기

**1단계: Create Agent**
```
이름: Multi-AI Orchestrator
설명: 여러 AI가 협업하는 토론 시스템
언어: Korean
리전: us-central1
```

**2단계: Data Store 연결 (RAG)**
```
Type: Unstructured Data
Data Source:
  ├── BigQuery: phsysics.knowledge_base.embeddings
  └── Cloud Storage: gs://multi-ai-memory-bank-phsysics/
```

### 2.3 Dialogflow CX 설정

Agent Builder가 자동으로 Dialogflow CX Agent를 만듭니다.

**1. Dialogflow CX 콘솔 열기**
```
Agent Builder → 당신의 Agent → "Open in Dialogflow CX"
```

**2. Webhook 추가**

좌측 메뉴 → "Manage" → "Webhooks" → "Create"

```
Display name: multi-ai-debate
Webhook URL: https://us-central1-phsysics.cloudfunctions.net/multi-ai-debate
Timeout: 300 seconds
```

"Save" 클릭

**3. 또 다른 Webhook 추가**

```
Display name: multi-ai-search
Webhook URL: https://us-central1-phsysics.cloudfunctions.net/multi-ai-search
Timeout: 60 seconds
```

### 2.4 Flow 설정

**1. Start Flow 편집**

"Build" → "Start" flow 클릭

**2. Route 추가 - 토론 요청**

"+ Add route" 클릭:

```
Intent: (새로 만들기)
  Display name: debate-request
  Training phrases:
    - 토론해줘
    - AI 토론 시작
    - [topic]에 대해 토론
    - [topic] 의견 궁금해
    - debate [topic]

Parameter:
  Name: topic
  Entity: @sys.any
  Required: true
  Prompt: "무엇에 대해 토론할까요?"

Fulfillment:
  Webhook: multi-ai-debate
  Tag: debate

  Parameter preset:
    topic: $session.params.topic
```

"Save" 클릭

**3. Route 추가 - 검색 요청**

또 다른 Route 추가:

```
Intent: search-request
  Training phrases:
    - [query] 검색해줘
    - [query] 찾아줘
    - search [query]
    - 과거 결정 찾기

Parameter:
  Name: query
  Entity: @sys.any
  Required: true
  Prompt: "무엇을 검색할까요?"

Fulfillment:
  Webhook: multi-ai-search
  Tag: search

  Parameter preset:
    query: $session.params.query
```

"Save" 클릭

**4. Default Welcome Route 수정**

"Default Welcome Intent" 클릭:

```
Fulfillment → Text response:

  안녕하세요! 👋 Multi-AI 협업 시스템입니다.

  다음 기능을 사용할 수 있습니다:

  🤖 **AI 토론**: "RTL 곱셈 최적화에 대해 토론해줘"
  🔍 **지식 검색**: "NoiseComputer 검색해줘"

  무엇을 도와드릴까요?
```

---

## 🌐 3단계: 웹 UI 활성화 (10분)

### 3.1 Integration 설정

Dialogflow CX → "Manage" → "Integrations"

### 3.2 Dialogflow Messenger 활성화

"Dialogflow Messenger" 클릭 → "Enable"

```
✅ Allow file uploads: ON
✅ Allow audio input: ON (선택)
```

"Save" 클릭

### 3.3 웹 URL 받기

Integration 페이지에서:

```
Integration URL:
https://dialogflow.cloud.google.com/messenger/xxxxx
```

**⭐ 이 URL이 당신의 웹 챗봇 주소입니다!**

---

## 📱 4단계: 테스트 (10분)

### 4.1 웹 브라우저에서 접속

```
https://dialogflow.cloud.google.com/messenger/xxxxx
```

### 4.2 테스트 시나리오

**테스트 1: 인사**
```
You: 안녕
Agent: 안녕하세요! Multi-AI 협업 시스템입니다...
```

**테스트 2: 검색**
```
You: NoiseComputer 검색해줘
Agent: 🔍 'NoiseComputer' 검색 결과 (3개):
       1. 관련도 92%
       NoiseComputer 256x256 구조...
```

**테스트 3: 토론**
```
You: RTL 곱셈 최적화에 대해 토론해줘
Agent: 토론 중입니다... (10초 대기)

       🤖 Multi-AI 토론 완료!
       📊 토론 주제: RTL 곱셈 최적화
       합의도: 88%

       💭 Claude 의견: 파이프라인 방식...
       💭 Gemini 의견: 병렬 처리...
```

### 4.3 모바일 테스트

핸드폰 브라우저에서 같은 URL 접속
→ 자동으로 반응형 UI

---

## 🎨 5단계: 커스터마이징 (선택)

### 5.1 챗봇 스타일 변경

Dialogflow Messenger 설정:

```
Theme color: #4285F4 (파란색)
Bot avatar: [이미지 URL]
```

### 5.2 웹사이트 임베드

웹사이트에 챗봇 추가:

```html
<script src="https://www.gstatic.com/dialogflow-console/fast/messenger/bootstrap.js?v=1"></script>
<df-messenger
  chat-title="Multi-AI Assistant"
  agent-id="your-agent-id"
  language-code="ko">
</df-messenger>
```

---

## 🔧 트러블슈팅

### 문제 1: Cloud Functions 배포 실패

```bash
# 권한 확인
gcloud auth list

# 프로젝트 확인
gcloud config get-value project

# 재배포
./deploy.sh
```

### 문제 2: Webhook 타임아웃

Dialogflow CX → Webhooks → timeout을 300초로 증가

### 문제 3: 검색 결과 없음

BigQuery 테이블 확인:
```bash
bq query "SELECT COUNT(*) FROM phsysics.knowledge_base.embeddings"
```

0이면 데이터 업로드 필요:
```bash
python3 scripts/vertex_github_bridge.py --to-vertex --initial-sync
```

---

## 📊 완료 체크리스트

- [ ] Cloud Functions 2개 배포 완료
- [ ] Vertex AI Agent Builder 생성
- [ ] Data Store 연결 (BigQuery + GCS)
- [ ] Dialogflow CX Webhooks 설정
- [ ] Flow + Routes 설정
- [ ] 웹 UI 활성화
- [ ] 웹 브라우저 테스트 성공
- [ ] 모바일 테스트 성공
- [ ] 토론 기능 작동 확인
- [ ] 검색 기능 작동 확인

---

## 🎉 완료!

이제 **어디서든 접속 가능한 Multi-AI 챗봇**이 완성되었습니다!

**웹 URL**: `https://dialogflow.cloud.google.com/messenger/xxxxx`

다음 단계:
1. URL 북마크
2. 팀원들과 공유
3. 실제 프로젝트에서 사용

---

## 💰 예상 비용

```
기존: $60/월 (API 구독)
추가:
├── Cloud Functions: ~$2-5/월
├── Dialogflow CX: ~$0-10/월 (1,000 요청 무료)
└── Agent Builder: ~$0 (미리보기 무료)

총: ~$62-75/월
```

매우 저렴합니다!

---

## 📚 참고 자료

- [Vertex AI Agent Builder 문서](https://cloud.google.com/dialogflow/vertex/docs)
- [Dialogflow CX 가이드](https://cloud.google.com/dialogflow/cx/docs)
- [Cloud Functions 문서](https://cloud.google.com/functions/docs)

---

**문제 발생 시**: 로그 확인

```bash
# Cloud Functions 로그
gcloud functions logs read multi-ai-debate --region=us-central1 --limit=50

# Dialogflow 로그
GCP Console → Dialogflow CX → Logs
```
