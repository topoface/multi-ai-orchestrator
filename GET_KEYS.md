# 🔑 API 키 받기 (2분!)

## 방법 1: 자동 스크립트 (가장 쉬움)

```bash
./setup_keys.sh
```

**하면 되는 것:**
1. URL 2개 클릭 (자동으로 브라우저 열림)
2. 키 복사
3. 터미널에 붙여넣기

끝!

---

## 방법 2: 수동 (복붙만)

### Claude API 키

**1. 이 URL 브라우저에 복사:**
```
https://console.anthropic.com/settings/keys
```

**2. "Create Key" 클릭**

**3. 키 복사 후:**
```bash
export ANTHROPIC_API_KEY="붙여넣기"
```

---

### Gemini API 키

**1. 이 URL 브라우저에 복사:**
```
https://makersuite.google.com/app/apikey
```

**2. "Create API key" 클릭**

**3. 키 복사 후:**
```bash
export GEMINI_API_KEY="붙여넣기"
```

---

## 완료 후

```bash
./deploy.sh
```

끝! 🎉

---

## 💡 팁

### Windows/WSL에서 브라우저 자동 열기
```bash
# setup_keys.sh 실행하면 자동으로 브라우저 열림
```

### 키 확인
```bash
echo $ANTHROPIC_API_KEY
echo $GEMINI_API_KEY
```

---

## 🔐 보안

API 키는:
- ❌ GitHub에 올리지 마세요
- ❌ 공유하지 마세요
- ✅ .env 파일에 저장 (자동 제외됨)
- ✅ 필요할 때만 생성

---

**소요 시간**: 2-3분
**필요한 것**: 브라우저만
