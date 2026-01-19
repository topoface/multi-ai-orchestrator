# Project Context

This file contains the overall context and background knowledge for the Multi-AI Orchestrator project.

## Project Overview

Multi-AI Orchestrator is a collaborative system that enables multiple AI models (Claude, Gemini, Perplexity) to debate and reach consensus on technical decisions. The system is centered around Vertex AI (phsysics project) for permanent knowledge storage.

## Architecture

### Core Components

1. **Vertex AI (phsysics)**
   - Main knowledge repository
   - BigQuery: 4,362+ embeddings for semantic search
   - GCS: Document storage and backups
   - Embedding model: textembedding-gecko@003 (768 dimensions)

2. **GitHub**
   - Shared workspace for code and decisions
   - Version control for all knowledge
   - GitHub Actions for automation
   - Issue-based debate triggering

3. **AI Participants**
   - **Claude (Sonnet 4.5)**: Primary debater, analytical
   - **Gemini (2.0 Flash)**: Alternative perspectives, review
   - **Perplexity**: Expert judgment for difficult decisions

### Data Flow

```
User Question
    ↓
Vertex AI RAG Search (if needed)
    ↓
Multi-AI Debate (Claude ↔ Gemini ↔ Perplexity)
    ↓
Consensus Calculation
    ↓
Decision Logging (GitHub + Vertex AI)
    ↓
Knowledge Base Update
```

## Key Concepts

### Consensus Scoring
- **85%+**: Auto-adopt decision
- **70-85%**: User review required
- **<70%**: Extended debate or expert judgment

Formula: `0.6 × embedding_similarity + 0.4 × keyword_overlap`

### Knowledge Storage
- All decisions stored in both GitHub (human-readable) and Vertex AI (searchable)
- Embeddings enable semantic search across historical decisions
- GCS provides archival and versioning

### Automation
- GitHub Actions trigger debates from Issues
- Hooks auto-sync changes to Vertex AI
- Daily knowledge updates from Vertex AI to GitHub

## Technology Stack

- **Python 3.11+**
- **Vertex AI**: Embeddings, BigQuery, Cloud Storage
- **Claude API**: Anthropic SDK
- **Gemini API**: google-generativeai
- **Perplexity API**: REST API
- **GitHub Actions**: Workflow automation
- **Claude Code**: Skills, Subagents, Hooks

## Project Goals

1. Enable multiple AI perspectives on technical decisions
2. Maintain permanent, searchable knowledge base
3. Automate debate triggering and result logging
4. Provide audit trail for all decisions
5. Reduce single-AI bias through consensus

## Cost Structure

### Monthly Costs
- **Subscriptions**: $60 (Gemini Advanced + Claude Pro + Perplexity Pro)
- **Infrastructure**: $0.22 (Vertex AI RAG storage)
- **Total**: $60.22/month (~84,300 KRW)

### API Usage
- Vertex AI Embeddings: $0.025 per 1,000 characters
- Claude API: Included in subscription
- Gemini API: Included in subscription
- Perplexity API: Included in subscription

## Security Considerations

- Service account keys stored as GitHub Secrets
- Never commit API keys or credentials
- GCS buckets use IAM for access control
- BigQuery data encrypted at rest

## Future Enhancements

- Resume debates from previous state
- Multi-round debate optimization
- Enhanced consensus algorithms
- Real-time debate monitoring UI
- Integration with more AI models

---

**Last Updated**: 2025-01-17
**Version**: 1.0.0
