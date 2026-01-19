#!/bin/bash
# Claude API 크레딧 구매 페이지 열기

echo "💳 Claude API 크레딧 구매 페이지를 엽니다..."
echo ""

CLAUDE_BILLING_URL="https://console.anthropic.com/settings/billing"

echo "📍 Claude 크레딧 구매 페이지:"
echo "   $CLAUDE_BILLING_URL"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Windows에서 실행 중인지 확인 (WSL)
if grep -qi microsoft /proc/version; then
    echo "🪟 Windows 브라우저로 자동 열기..."
    /mnt/c/Windows/System32/cmd.exe /c start "$CLAUDE_BILLING_URL" 2>/dev/null &
    echo "✅ 브라우저가 열렸습니다!"
elif command -v xdg-open &> /dev/null; then
    # Linux
    echo "🐧 Linux 브라우저로 자동 열기..."
    xdg-open "$CLAUDE_BILLING_URL" &
    echo "✅ 브라우저가 열렸습니다!"
elif command -v open &> /dev/null; then
    # macOS
    echo "🍎 macOS 브라우저로 자동 열기..."
    open "$CLAUDE_BILLING_URL"
    echo "✅ 브라우저가 열렸습니다!"
else
    echo "⚠️  자동 열기 실패. 위 URL을 수동으로 복사하세요."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💰 크레딧 구매 방법:"
echo ""
echo "   1️⃣  페이지에서 'Buy credits' 버튼 클릭"
echo "   2️⃣  금액 선택:"
echo "      • \$5 = 500만 토큰 (~100회 대화)"
echo "      • \$10 = 1000만 토큰 (~200회 대화) ⭐ 추천"
echo "      • \$20 = 2000만 토큰 (~400회 대화)"
echo ""
echo "   3️⃣  카드 정보 입력 → 'Purchase' 클릭"
echo "   4️⃣  완료! 즉시 사용 가능"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 팁:"
echo "   • API 크레딧은 Claude Pro 구독과 별개입니다"
echo "   • 크레딧은 사용한 만큼만 차감됩니다"
echo "   • 만료 기간 없음 (계정에 남아있음)"
echo "   • 자동 충전 설정도 가능합니다"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 다음 단계:"
echo "   크레딧 구매 완료 후:"
echo "   1. GCP 인증: gcloud auth application-default login"
echo "   2. 테스트: python scripts/auto-debate.py \"Python vs JavaScript\" --quick"
echo ""
