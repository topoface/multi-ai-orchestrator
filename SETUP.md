# Setup Guide - Multi-AI Orchestrator

## Prerequisites

- Python 3.9+
- Google Cloud Project (phsysics)
- API Keys: Claude, Gemini, Perplexity (optional)
- GitHub account

## Step 1: Clone and Install

```bash
git clone https://github.com/your-username/multi-ai-orchestrator.git
cd multi-ai-orchestrator
pip install -r requirements.txt
```

## Step 2: GCP Configuration

### 2.1 Create Service Account

```bash
gcloud iam service-accounts create multi-ai-orchestrator \
    --project=phsysics \
    --display-name="Multi-AI Orchestrator"
```

### 2.2 Grant Permissions

```bash
# BigQuery Data Editor
gcloud projects add-iam-policy-binding phsysics \
    --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

# Cloud Storage Object Admin
gcloud projects add-iam-policy-binding phsysics \
    --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Vertex AI User
gcloud projects add-iam-policy-binding phsysics \
    --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### 2.3 Create Service Account Key

```bash
gcloud iam service-accounts keys create sa-key.json \
    --iam-account=multi-ai-orchestrator@phsysics.iam.gserviceaccount.com
```

**Important**: Keep `sa-key.json` secure and never commit to Git!

## Step 3: API Keys Setup

### 3.1 Create .env file

```bash
cp .env.example .env
```

### 3.2 Edit .env with your keys

```bash
# Get Claude API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Get Gemini API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=AIzaSyxxxxx

# Get Perplexity API key from: https://www.perplexity.ai/settings/api
PERPLEXITY_API_KEY=pplx-xxxxx

# GCP
GOOGLE_APPLICATION_CREDENTIALS=./sa-key.json
GCP_PROJECT_ID=phsysics
```

## Step 4: Verify BigQuery and GCS

### 4.1 Check BigQuery table

```bash
bq show phsysics:my_physics_agent_stackoverflow_data.questions_embeddings
```

Expected: Table with ~4,362 rows

### 4.2 Check GCS bucket

```bash
gsutil ls gs://multi-ai-memory-bank-phsysics/
```

Expected folders:
- `context/`
- `decisions/`
- `session_logs/`

If missing, create them:

```bash
gsutil mb -p phsysics gs://multi-ai-memory-bank-phsysics/
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/context/.keep
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/decisions/.keep
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/session_logs/.keep
```

## Step 5: Initialize Knowledge Base

### 5.1 Create knowledge_base dataset in BigQuery

```bash
bq mk --dataset \
    --location=US \
    --description="Multi-AI Orchestrator knowledge base" \
    phsysics:knowledge_base
```

### 5.2 Create embeddings table

```bash
bq mk --table \
    phsysics:knowledge_base.embeddings \
    content:STRING,embedding:FLOAT64,metadata:JSON,created_at:TIMESTAMP
```

## Step 6: Configure GitHub Secrets

Go to GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:
- `ANTHROPIC_API_KEY`: Your Claude API key
- `GEMINI_API_KEY`: Your Gemini API key
- `PERPLEXITY_API_KEY`: Your Perplexity API key
- `GCP_SA_KEY`: Entire content of `sa-key.json` file

## Step 7: Configure Claude Code Skills

### 7.1 Copy skills to Claude Code directory

```bash
# Create Claude Code skills directory if not exists
mkdir -p ~/.claude/skills

# Link skills from this project
ln -s $(pwd)/.claude/skills/vertex-search ~/.claude/skills/
ln -s $(pwd)/.claude/skills/github-sync ~/.claude/skills/
ln -s $(pwd)/.claude/skills/debate-request ~/.claude/skills/
ln -s $(pwd)/.claude/skills/decision-logger ~/.claude/skills/
```

### 7.2 Configure hooks in Claude settings

Edit `~/.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "/path/to/multi-ai-orchestrator/.claude/hooks/sync-to-vertex.py"
        }]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [{
          "type": "command",
          "command": "/path/to/multi-ai-orchestrator/.claude/hooks/trigger-debate.py"
        }]
      }
    ],
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": "/path/to/multi-ai-orchestrator/.claude/hooks/save-debate-result.py"
        }]
      }
    ]
  }
}
```

## Step 8: Test Installation

### 8.1 Test Vertex AI connection

```bash
python scripts/vertex_github_bridge.py --test
```

### 8.2 Test local debate

```bash
python scripts/auto-debate.py "Test question: What is 2+2?" --rounds 2
```

### 8.3 Test GitHub Actions (after pushing to GitHub)

```bash
gh issue create \
  --title "[Debate] Test issue" \
  --body "This is a test debate" \
  --label "ai-debate"
```

## Step 9: Initial Sync

Sync existing knowledge to Vertex AI:

```bash
python scripts/sync_manager.py --initial-sync
```

## Troubleshooting

### Permission denied errors
- Check service account permissions
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path
- Ensure sa-key.json is in project root

### API rate limits
- Claude API: 50 requests/minute (Tier 1)
- Gemini API: 60 requests/minute (free tier)
- Adjust `debate_config.yaml` timeouts if needed

### BigQuery errors
- Verify dataset and table exist
- Check IAM permissions
- Ensure billing is enabled on GCP project

### Skills not showing in Claude Code
- Verify symlinks are created correctly
- Check SKILL.md format
- Restart Claude Code

## Next Steps

1. Create your first debate via GitHub Issue
2. Test `/vertex-search` skill in Claude Code
3. Monitor `docs/brain/` for auto-generated decisions
4. Review GitHub Actions runs

## Support

For issues, check:
- GitHub Actions logs
- GCP Cloud Logging
- Local logs in `logs/` directory
