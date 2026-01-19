#!/bin/bash
# API 키 설정 초간단 스크립트

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 API 키 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Claude API 키
echo "1️⃣  Claude API 키"
echo "   → https://console.anthropic.com/settings/keys 열기"
echo "   → 'Create Key' 클릭"
echo "   → 키 복사"
echo ""
read -p "Claude API Key 붙여넣기: " ANTHROPIC_KEY

# Gemini API 키
echo ""
echo "2️⃣  Gemini API 키"
echo "   → https://makersuite.google.com/app/apikey 열기"
echo "   → 'Create API key' 클릭"
echo "   → 키 복사"
echo ""
read -p "Gemini API Key 붙여넣기: " GEMINI_KEY

# .env 파일 생성
cat > .env << EOF
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
GEMINI_API_KEY=$GEMINI_KEY
GCP_PROJECT_ID=phsysics
GCP_REGION=us-central1
EOF

# 환경 변수 즉시 적용
export ANTHROPIC_API_KEY=$ANTHROPIC_KEY
export GEMINI_API_KEY=$GEMINI_KEY
export GCP_PROJECT_ID=phsysics

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 설정 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo ".env 파일 저장됨"
echo ""
echo "🚀 이제 배포 가능:"
echo "   ./deploy.sh"
echo ""
