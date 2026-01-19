---
name: github-sync
description: Bidirectional sync between GitHub and Vertex AI. Use "/github-sync" to sync
user-invocable: true
---

# GitHub ↔ Vertex AI Sync Skill

## Purpose
Synchronize knowledge between GitHub docs/brain/ and Vertex AI RAG (BigQuery + GCS)

## Sync Directions

### 1. GitHub → Vertex AI
When files in `docs/brain/` change:
- Generate embeddings using Vertex AI Embeddings API
- Store in BigQuery for similarity search
- Backup to GCS

### 2. Vertex AI → GitHub
When AI debates conclude:
- Update `docs/brain/DECISIONS.md` with results
- Commit changes automatically
- Create PR if configured

## Usage

```bash
# Bidirectional sync (default)
/github-sync

# GitHub to Vertex only
/github-sync --to-vertex

# Vertex to GitHub only
/github-sync --from-vertex

# Initial full sync
/github-sync --initial-sync
```

## What Gets Synced

### To Vertex AI:
- `docs/brain/CONTEXT.md`
- `docs/brain/DECISIONS.md`
- `docs/brain/DEBATES.md`
- All `.md` files in `docs/brain/`

### From Vertex AI:
- Debate results → `docs/brain/DECISIONS.md`
- Session logs → `docs/brain/DEBATES.md`
- Knowledge updates → `docs/brain/CONTEXT.md`

## Conflict Resolution
- Vertex AI is source of truth for decisions
- GitHub is source of truth for manual edits
- Timestamp-based merge for conflicts

## Implementation
Python script: `.claude/skills/github-sync/sync_manager.py`
- Git diff detection for changed files
- Vertex AI Embeddings API for vectorization
- BigQuery upload with deduplication
- GCS backup with versioning
