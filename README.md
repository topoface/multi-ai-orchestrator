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

### Discussion Protocol (Collaborative, Not Adversarial)

**Philosophy**: AI experts trained on similar data naturally converge. No forced opposition.

1. **Round 1-10**: Pure technical discussion
   - Claude: "What's your understanding of {topic}?"
   - Gemini: "Your thoughts on the discussion?"
   - Natural exchange without forced structure

2. **Mid-Discussion Check (Round 5)**:
   - If consensus < 70% → Auto-call Perplexity for expert perspective
   - AIs continue discussing with Perplexity's insights

3. **Dynamic Expert Mediation**:
   - Either AI can request Perplexity via `[REQUEST_EXPERT]` signal
   - If both request → Immediate expert judgment

### Consensus Criteria

- **≥85%**: Auto-adopt (high natural agreement)
- **70-85%**: User review (moderate agreement)
- **<70%**: Genuine disagreement → Perplexity mediation

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
# Hook 자동 실행 테스트 - Wed Jan 21 11:26:05 KST 2026
