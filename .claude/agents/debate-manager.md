---
name: debate-manager
description: Multi-AI debate process manager. Invoked for "manage debate", "orchestrate AI discussion"
tools: Bash, Read, Write
model: sonnet
---

# Debate Manager Subagent

## Role
Orchestrates the complete Multi-AI debate process from initiation to conclusion

## Responsibilities

### 1. Round-by-Round Management
- Control debate flow across multiple rounds
- Enforce turn-taking: Claude → Gemini → repeat
- Monitor round timeout (default: 5 minutes per round)
- Track conversation history

### 2. Consensus Calculation
- Calculate agreement score after each round
- Use embedding similarity + keyword matching
- Determine if consensus threshold reached
- Trigger Perplexity if needed (consensus < 70%)

### 3. Result Synthesis
- Compile complete debate transcript
- Extract final positions from each AI
- Format results for storage
- Trigger logging to Vertex AI and GitHub

## Debate Settings

From `config/debate_config.yaml`:
- **Max rounds**: 4
- **Round timeout**: 300 seconds (5 minutes)
- **Consensus threshold**: 85% (auto-adopt)
- **Expert threshold**: 70% (trigger Perplexity)

## Debate State Machine

```
INIT
  ↓
ROUND_1_CLAUDE_PROPOSE
  ↓
ROUND_1_GEMINI_REVIEW
  ↓
CHECK_CONSENSUS → [≥85%] → CONCLUDE
  ↓ [<85%]
ROUND_2_GEMINI_ALTERNATIVE
  ↓
ROUND_2_CLAUDE_REBUTTAL
  ↓
CHECK_CONSENSUS → [≥85%] → CONCLUDE
  ↓ [<85%]
ROUND_3_COMPROMISE
  ↓
CHECK_CONSENSUS → [<70%] → PERPLEXITY_JUDGMENT
  ↓
CONCLUDE
```

## Key Functions

### initiate_debate(topic, participants)
Starts a new debate session

### execute_round(round_num, previous_context)
Executes a single debate round

### calculate_consensus(position_a, position_b)
Calculates agreement score between two positions

### should_continue_debate(consensus, round_num)
Determines if debate should continue

### conclude_debate(history, final_positions)
Finalizes and stores debate results

## Consensus Scoring Algorithm

```python
def calculate_consensus(text_a, text_b):
    # 1. Extract keywords (remove stopwords)
    keywords_a = extract_keywords(text_a)
    keywords_b = extract_keywords(text_b)

    # 2. Keyword overlap (Jaccard similarity)
    overlap = len(keywords_a & keywords_b)
    union = len(keywords_a | keywords_b)
    keyword_score = overlap / union

    # 3. Semantic similarity (embeddings)
    embedding_a = get_embedding(text_a)
    embedding_b = get_embedding(text_b)
    semantic_score = cosine_similarity(embedding_a, embedding_b)

    # 4. Weighted average
    consensus = (0.4 * keyword_score) + (0.6 * semantic_score)

    return consensus
```

## Error Handling

- **Timeout**: If round exceeds timeout, force completion
- **API Failure**: Retry 3 times with exponential backoff
- **Deadlock**: If no progress after 2 rounds, trigger Perplexity
- **Invalid Response**: Request clarification from AI

## Integration Points

### With Skills:
- Calls `debate-request` skill to execute AI interactions
- Calls `decision-logger` skill to store results
- Calls `github-sync` skill to update repository

### With Vertex AI:
- Stores debate history in BigQuery
- Backs up to GCS
- Updates RAG knowledge base

### With GitHub:
- Updates Issue with progress
- Creates PR if decision requires code changes
- Closes Issue when concluded

## Implementation Script

Location: `.claude/agents/debate-manager/debate_manager.py`

Key features:
- State machine for debate flow
- Consensus calculation
- Timeout management
- Result compilation
- Integration with all storage systems

## Example Usage

```bash
# Start debate
python debate_manager.py start \
  --topic "RTL multiplication optimization" \
  --participants claude,gemini \
  --max-rounds 4

# Resume debate from round
python debate_manager.py resume \
  --debate-id abc123 \
  --from-round 3

# Check status
python debate_manager.py status --debate-id abc123
```

## Monitoring

Logs to stderr:
- Round start/end
- Consensus scores
- AI response times
- Errors and retries

Output format:
```
🔥 Debate started: RTL multiplication
=== Round 1 ===
  Claude proposing... ✓ (3.2s)
  Gemini reviewing... ✓ (2.8s)
  Consensus: 45%
=== Round 2 ===
  Gemini alternative... ✓ (3.5s)
  Claude rebuttal... ✓ (2.9s)
  Consensus: 72%
=== Round 3 ===
  Compromise... ✓ (4.1s)
  Consensus: 88% ✓
🎉 Debate concluded with consensus!
```
