---
name: supabase-search
description: Search knowledge base in Supabase using PostgreSQL full-text search. Use "/supabase-search <query>" to search.
user-invocable: true
---

# Supabase Knowledge Search Skill

## Purpose

Search the knowledge base stored in Supabase PostgreSQL database using full-text search and vector similarity (when pgvector is enabled).

## Features

- Full-text search across knowledge_base table
- Metadata filtering (file_path, file_name, etc.)
- Results ranked by relevance
- Source attribution with GitHub links

## Usage

```bash
/supabase-search "RTL multiplication optimization"
/supabase-search "NoiseComputer architecture"
/supabase-search --limit 10 "debate results"
```

## Search Methods

1. **Full-text search**: PostgreSQL `tsvector` and `tsquery`
2. **Metadata filtering**: JSON field searches
3. **Vector similarity**: pgvector cosine similarity (if configured)

## Implementation

Python script: `supabase_search.py`

- Connects to Supabase PostgreSQL
- Executes search queries
- Formats results with context
- Includes source attribution

## Configuration

Requires environment variables:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for database access

## Output Format

```
Search Results for "RTL optimization"
=====================================

1. NoiseComputer RTL Implementation (Score: 0.95)
   Source: docs/brain/DECISIONS.md
   Content: RTL 곱셈 회피를 위해 256x256 lookup table 사용...

2. Previous Debate on Multiplication (Score: 0.87)
   Source: debate_results/2026-01-19T20:30:00Z
   Content: Claude and Gemini discussed alternatives to multiplication...
```

## Integration with Multi-AI System

- Automatically searches before debates (context gathering)
- Used by Claude/Gemini to reference previous decisions
- Provides evidence for arguments
- Links to source files in GitHub

## Future Enhancements

- Vector similarity search with embeddings
- Semantic search using Supabase AI
- Multi-language support
- Relevance ranking improvements
