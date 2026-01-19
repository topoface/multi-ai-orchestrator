---
name: debate-request
description: Start Multi-AI debate. Use "/debate <topic>" to initiate
user-invocable: true
---

# Multi-AI Debate Request Skill

## Purpose
Initiate intensive debate between Claude CLI + Gemini API + Perplexity for critical technical decisions

## Debate Protocol

### Round Structure
1. **Round 1**: Claude proposes → Gemini reviews
2. **Round 2**: Gemini alternative → Claude rebuts
3. **Round 3**: Both sides compromise → Calculate consensus
4. **Round 4**: Perplexity judgment (if consensus < 70%)

### Consensus Criteria
- **≥85%**: Auto-adopt decision
- **70-85%**: User review required
- **<70%**: Extend debate or trigger Perplexity

## Usage

```bash
# Basic debate
/debate "RTL multiplication optimization methods?"

# Expert mode (includes Perplexity from start)
/debate --expert "NoiseComputer architecture design"

# Quick debate (max 2 rounds)
/debate --quick "Variable naming convention"

# Save results to specific file
/debate --output decisions/my_decision.md "Topic here"
```

## Debate Flow

```
User Question
    ↓
Claude analyzes & proposes
    ↓
Gemini reviews & counters
    ↓
Calculate consensus score
    ↓
┌─────────────┬──────────────┬─────────────┐
│  ≥85%       │  70-85%      │  <70%       │
│  Auto-adopt │  User review │  Perplexity │
└─────────────┴──────────────┴─────────────┘
```

## Consensus Scoring

**Formula**: `0.6 × embedding_similarity + 0.4 × keyword_overlap`

- Embedding similarity: Cosine distance between final positions
- Keyword overlap: Shared technical terms / total unique terms

## Output

Results saved to:
1. **GitHub**: `docs/brain/DECISIONS.md`
2. **Vertex AI BigQuery**: `knowledge_base.embeddings`
3. **Vertex AI GCS**: `gs://bucket/decisions/debate_TIMESTAMP.json`

## Configuration

Edit `config/debate_config.yaml`:
- `max_rounds`: Maximum debate rounds (default: 4)
- `consensus_threshold`: Auto-adopt threshold (default: 0.85)
- `expert_threshold`: Trigger Perplexity threshold (default: 0.70)

## Implementation

Python script: `.claude/skills/debate-request/debate_engine.py`
- Claude API via Anthropic SDK
- Gemini API via google-generativeai
- Perplexity API via requests
- Consensus calculation with embeddings + keywords
