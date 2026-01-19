#!/bin/bash
# Multi-AI Orchestrator Cloud Functions 배포 스크립트

set -e

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Multi-AI Orchestrator Cloud Functions 배포"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 환경 변수 확인
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ ANTHROPIC_API_KEY가 설정되지 않았습니다${NC}"
    echo "export ANTHROPIC_API_KEY='your-key' 실행 후 다시 시도하세요"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY가 설정되지 않았습니다${NC}"
    echo "export GEMINI_API_KEY='your-key' 실행 후 다시 시도하세요"
    exit 1
fi

# GCP 프로젝트 설정
PROJECT_ID=${GCP_PROJECT_ID:-"phsysics"}
REGION=${GCP_REGION:-"us-central1"}

echo -e "${YELLOW}📍 프로젝트: $PROJECT_ID${NC}"
echo -e "${YELLOW}📍 리전: $REGION${NC}"
echo ""

# 1. Debate Function 배포
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Debate Function 배포 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd cloud-functions/debate

gcloud functions deploy multi-ai-debate \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=debate \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY,GEMINI_API_KEY=$GEMINI_API_KEY,MAX_ROUNDS=3,CONSENSUS_THRESHOLD=0.85 \
  --memory=512MB \
  --timeout=300s

DEBATE_URL=$(gcloud functions describe multi-ai-debate --region=$REGION --gen2 --format='value(serviceConfig.uri)')
echo -e "${GREEN}✅ Debate Function 배포 완료!${NC}"
echo -e "${GREEN}   URL: $DEBATE_URL${NC}"
echo ""

cd ../..

# 2. Search Function 배포
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Search Function 배포 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd cloud-functions/search

gcloud functions deploy multi-ai-search \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=search \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,GCP_LOCATION=$REGION,SIMILARITY_THRESHOLD=0.7,MAX_RESULTS=5 \
  --memory=512MB \
  --timeout=60s

SEARCH_URL=$(gcloud functions describe multi-ai-search --region=$REGION --gen2 --format='value(serviceConfig.uri)')
echo -e "${GREEN}✅ Search Function 배포 완료!${NC}"
echo -e "${GREEN}   URL: $SEARCH_URL${NC}"
echo ""

cd ../..

# 완료
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 모든 Cloud Functions 배포 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 엔드포인트 URL:"
echo "  - Debate: $DEBATE_URL"
echo "  - Search: $SEARCH_URL"
echo ""
echo "💡 다음 단계:"
echo "  1. Vertex AI Agent Builder에서 webhook URL 등록"
echo "  2. 웹 UI에서 테스트"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
