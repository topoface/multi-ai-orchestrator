---
name: decision-logger
description: Automatically log important decisions. Use "/decision-log" to log
user-invocable: true
---

# Decision Logger Skill

## Purpose
Automatically record AI debate results and architectural decisions to both GitHub and Vertex AI

## What Gets Logged

### Decision Information
- **What**: The decision made
- **Why**: Rationale and reasoning
- **When**: Timestamp
- **Who**: Participating AIs and consensus score
- **Alternatives**: What options were considered

### Storage Locations
1. **GitHub**: `docs/brain/DECISIONS.md` (human-readable)
2. **Vertex AI BigQuery**: `knowledge_base.embeddings` (searchable)
3. **Vertex AI GCS**: `gs://bucket/decisions/` (archival)

## Usage

```bash
# Log current debate result
/decision-log

# Log manual decision
/decision-log --manual "Decision title" --reason "Why this was chosen" --alternatives "What else was considered"

# Log with custom metadata
/decision-log --tags "architecture,performance" --priority high
```

## Automatic Logging

This skill is automatically triggered when:
- AI debate concludes with consensus ≥85%
- User manually approves debate result (consensus 70-85%)
- Important architectural changes are committed

## Log Format

```markdown
## Decision: [Title]

**Date**: YYYY-MM-DD HH:MM:SS UTC
**Consensus**: X%
**Priority**: [low|medium|high]
**Tags**: tag1, tag2, tag3

### What Was Decided
[The final decision]

### Why This Decision
[Rationale and reasoning]

### Alternatives Considered
1. Alternative A - Rejected because...
2. Alternative B - Rejected because...

### Participants
- Claude: [position]
- Gemini: [position]
- Perplexity: [judgment] (if applicable)

### Implementation Notes
[Key considerations for implementation]
```

## Searchability

All logged decisions are:
- Embedded and stored in BigQuery for semantic search
- Tagged with metadata for filtering
- Linked to source code commits (when applicable)
- Versioned in GCS for audit trail

## Configuration

Edit `config/vertex_config.yaml`:
- Auto-log threshold
- Required metadata fields
- Storage paths

## Implementation

Python script: `.claude/skills/decision-logger/logger.py`
- Formats decisions in consistent structure
- Generates embeddings for search
- Uploads to BigQuery and GCS
- Updates GitHub files
