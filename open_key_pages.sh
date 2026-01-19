#!/bin/bash
# 브라우저에서 API 키 페이지 자동으로 열기

echo "🌐 브라우저에서 API 키 페이지를 엽니다..."
echo ""

# Claude 페이지
CLAUDE_URL="https://console.anthropic.com/settings/keys"
echo "1️⃣  Claude API 키 페이지:"
echo "   $CLAUDE_URL"

# Gemini 페이지
GEMINI_URL="https://makersuite.google.com/app/apikey"
echo "2️⃣  Gemini API 키 페이지:"
echo "   $GEMINI_URL"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Windows에서 실행 중인지 확인 (WSL)
if grep -qi microsoft /proc/version; then
    echo "🪟 Windows 브라우저로 자동 열기..."

    # Windows 브라우저로 열기
    /mnt/c/Windows/System32/cmd.exe /c start "$CLAUDE_URL" 2>/dev/null &
    sleep 2
    /mnt/c/Windows/System32/cmd.exe /c start "$GEMINI_URL" 2>/dev/null &

    echo "✅ 브라우저에서 2개 탭이 열렸습니다!"
elif command -v xdg-open &> /dev/null; then
    # Linux
    echo "🐧 Linux 브라우저로 자동 열기..."
    xdg-open "$CLAUDE_URL" &
    sleep 1
    xdg-open "$GEMINI_URL" &
    echo "✅ 브라우저에서 2개 탭이 열렸습니다!"
elif command -v open &> /dev/null; then
    # macOS
    echo "🍎 macOS 브라우저로 자동 열기..."
    open "$CLAUDE_URL"
    sleep 1
    open "$GEMINI_URL"
    echo "✅ 브라우저에서 2개 탭이 열렸습니다!"
else
    echo "⚠️  자동 열기 실패. 위 URL을 수동으로 복사하세요."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 할 일:"
echo "   1. Claude 페이지에서 'Create Key' 클릭"
echo "   2. 키 복사"
echo "   3. Gemini 페이지에서 'Create API key' 클릭"
echo "   4. 키 복사"
echo ""
echo "🚀 그 다음:"
echo "   ./setup_keys.sh  (키 입력)"
echo "   ./deploy.sh      (배포)"
echo ""
