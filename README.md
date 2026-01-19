# Multi-AI Orchestrator

A collaborative Multi-AI debate system centered on Vertex AI (phsysics project) with GitHub as shared workspace.

## Architecture

```
User → Vertex AI (Main conversation, RAG memory)
         ↓ (When uncertain)
GitHub Issue → AI Debate (Claude CLI ↔ Gemini API ↔ Perplexity)
         ↓ (Debate results)
Vertex AI Learning + GitHub Commit (History)
```

## Key Features

- **Vertex AI (phsysics)**: Main AI with permanent RAG knowledge storage
- **GitHub**: Shared workspace for code version control
- **Multi-AI Debates**: Claude CLI + Gemini API collaborate on Issues
- **Perplexity**: Optional expert judgment for critical decisions
- **Custom Skills/Subagents/Hooks**: Project-specific customizations

## Components

### Skills
- `vertex-search`: Search knowledge from Vertex AI RAG (BigQuery + GCS)
- `github-sync`: Bidirectional sync between GitHub and Vertex AI
- `debate-request`: Initiate Multi-AI debates
- `decision-logger`: Automatically log important decisions

### Subagents
- `github-orchestrator`: Manages GitHub Issues/PRs/Actions
- `debate-manager`: Orchestrates Multi-AI debate process
- `vertex-learner`: Learns and manages Vertex AI knowledge

### Hooks
- `sync-to-vertex`: Auto-sync file changes to Vertex AI (PostToolUse)
- `trigger-debate`: Auto-detect debate keywords (UserPromptSubmit)
- `save-debate-result`: Save session logs to Vertex AI (Stop)

## Quick Start

1. Clone this repository
2. Follow [SETUP.md](SETUP.md) for initial configuration
3. Set up API keys in `.env`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure GCP Service Account
6. Test with: `python scripts/auto-debate.py "Your question"`

## Usage

### Start a debate via Claude Code
```bash
/debate "What's the best RTL multiplication optimization?"
```

### Search Vertex AI knowledge
```bash
/vertex-search NoiseComputer multiplication rules
```

### Sync to Vertex AI
```bash
/github-sync
```

### Via GitHub Issues
Create an issue with title `[Debate] Your question` or label `ai-debate`

## Architecture Details

### Knowledge Storage
- **BigQuery**: `phsysics.my_physics_agent_stackoverflow_data.questions_embeddings` (4,362 embeddings)
- **GCS**: `gs://multi-ai-memory-bank-phsysics/` (context/, decisions/, session_logs/)

### Debate Protocol
1. **Round 1**: Claude proposal → Gemini review
2. **Round 2**: Gemini alternative → Claude rebuttal
3. **Round 3**: Both sides compromise → Calculate consensus
4. **Round 4**: Perplexity judgment (if consensus < 70%)

### Consensus Criteria
- **≥85%**: Auto-adopt
- **70-85%**: User review required
- **<70%**: Extend debate or call Perplexity

## Cost Estimate

**Subscriptions (existing)**: $60/month
- Gemini Advanced: $20
- Claude Pro: $20
- Perplexity Pro: $20

**Infrastructure (additional)**: $0.22/month
- Vertex AI RAG: $0.22 (100MB data)

**Total**: $60.22/month (~84,300 KRW)

## Project Structure

```
multi-ai-orchestrator/
├── .github/              # GitHub Actions workflows
├── .claude/              # Claude Code customizations
│   ├── skills/          # Custom skills
│   ├── agents/          # Subagents
│   └── hooks/           # Event hooks
├── docs/brain/          # Knowledge base (synced to Vertex AI)
├── scripts/             # Core automation scripts
└── config/              # Configuration files
```

## Contributing

This is a personal project template. Feel free to fork and customize for your needs.

## License

MIT License - See LICENSE file for details
