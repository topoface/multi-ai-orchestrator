#!/bin/bash
# GitHub Repository Setup Script
# Run this after GCP setup is complete

set -e  # Exit on error

echo "🚀 Starting GitHub Repository Setup"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "HANDOFF.md" ]; then
    echo "❌ Error: Not in multi-ai-orchestrator directory"
    echo "Please run: cd /home/wishingfly/multi-ai-orchestrator"
    exit 1
fi

# ===== 1. Git 초기화 =====
echo ""
echo "📝 Step 1/4: Initializing Git repository..."
if [ -d ".git" ]; then
    echo "⚠️  Git repository already exists, skipping init"
else
    git init
    echo "✅ Git initialized"
fi

# ===== 2. Git 설정 확인 =====
echo ""
echo "👤 Checking Git configuration..."
if [ -z "$(git config user.name)" ]; then
    echo "⚠️  Git user.name not set. Please run:"
    echo "   git config user.name \"Your Name\""
fi
if [ -z "$(git config user.email)" ]; then
    echo "⚠️  Git user.email not set. Please run:"
    echo "   git config user.email \"your@email.com\""
fi

# ===== 3. 파일 추가 및 커밋 =====
echo ""
echo "📦 Step 2/4: Adding files and creating commit..."
git add .
git commit -m "Initial commit: Multi-AI Orchestrator v1.0

Features:
- Multi-AI debate system (Claude + Gemini + Perplexity)
- Vertex AI RAG integration (BigQuery + GCS)
- GitHub Actions workflows for automated debates
- Custom Skills, Subagents, and Hooks
- 85% implementation complete, local testing successful

Components:
- debate_engine.py: 368 lines, fully tested
- vertex_search.py: 181 lines, RAG implementation
- 3 GitHub Actions workflows
- 4 Skills, 3 Subagents, 3 Hooks

Infrastructure:
- GCP Project: phsysics
- BigQuery: knowledge_base.embeddings
- GCS: multi-ai-memory-bank-phsysics

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>" || echo "⚠️  Nothing to commit or already committed"

git branch -M main

echo "✅ Commit created"

# ===== 4. Remote 설정 준비 =====
echo ""
echo "🌐 Step 3/4: Remote setup..."
echo ""
echo "⚠️  MANUAL STEP REQUIRED:"
echo "1. Go to https://github.com/new"
echo "2. Owner: topoface"
echo "3. Repository name: multi-ai-orchestrator"
echo "4. Visibility: Public (recommended) or Private"
echo "5. DO NOT initialize with README/license/gitignore"
echo "6. Click 'Create repository'"
echo ""
read -p "Press Enter after creating the GitHub repository..."

# ===== 5. Remote 추가 및 푸시 =====
echo ""
echo "📤 Step 4/4: Pushing to GitHub..."
git remote add origin https://github.com/topoface/multi-ai-orchestrator.git 2>/dev/null || \
    git remote set-url origin https://github.com/topoface/multi-ai-orchestrator.git

echo "Pushing to main branch..."
git push -u origin main

echo ""
echo "===================================="
echo "🎉 GitHub Repository Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to: https://github.com/topoface/multi-ai-orchestrator/settings/secrets/actions"
echo "2. Add these secrets:"
echo "   - ANTHROPIC_API_KEY (from .env)"
echo "   - GEMINI_API_KEY (from .env)"
echo "   - GCP_SA_KEY (from sa-key.json)"
echo ""
echo "3. Test the system:"
echo "   gh issue create --title '[Debate] Test' --body 'Test debate' --label 'ai-debate'"
echo "===================================="
