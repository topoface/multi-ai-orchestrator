#!/usr/bin/env python3
"""
Supabase Knowledge Search
Search knowledge base using PostgreSQL full-text search
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed", file=sys.stderr)
    print("Install with: pip install supabase", file=sys.stderr)
    sys.exit(1)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
    sys.exit(1)


class SupabaseSearch:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    def search_knowledge_base(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge_base table using full-text search
        """
        try:
            # Search in content field
            response = self.client.table('knowledge_base') \
                .select('id, content, metadata, created_at') \
                .ilike('content', f'%{query}%') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            return response.data
        except Exception as e:
            print(f"Search error: {e}", file=sys.stderr)
            return []

    def search_debates(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search debate_results table
        """
        try:
            response = self.client.table('debate_results') \
                .select('id, topic, claude_position, gemini_position, consensus_score, created_at') \
                .or_(f'topic.ilike.%{query}%,claude_position.ilike.%{query}%,gemini_position.ilike.%{query}%') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            return response.data
        except Exception as e:
            print(f"Search error: {e}", file=sys.stderr)
            return []

    def search_decisions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search decisions table
        """
        try:
            response = self.client.table('decisions') \
                .select('id, title, content, rationale, created_at') \
                .or_(f'title.ilike.%{query}%,content.ilike.%{query}%') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            return response.data
        except Exception as e:
            print(f"Search error: {e}", file=sys.stderr)
            return []


def format_results(results: List[Dict[str, Any]], result_type: str) -> str:
    """Format search results for display"""
    if not results:
        return f"No {result_type} found."

    output = [f"\n{result_type.upper()} RESULTS"]
    output.append("=" * 80)

    for idx, result in enumerate(results, 1):
        output.append(f"\n{idx}. ", end="")

        if result_type == "knowledge_base":
            file_name = result.get('metadata', {}).get('file_name', 'Unknown')
            content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
            output.append(f"{file_name}")
            output.append(f"   Created: {result['created_at']}")
            output.append(f"   Content: {content_preview}")

        elif result_type == "debates":
            output.append(f"{result['topic']} (Consensus: {result['consensus_score']:.0%})")
            output.append(f"   Date: {result['created_at']}")
            output.append(f"   Claude: {result['claude_position'][:150]}...")
            output.append(f"   Gemini: {result['gemini_position'][:150]}...")

        elif result_type == "decisions":
            output.append(f"{result['title']}")
            output.append(f"   Date: {result['created_at']}")
            output.append(f"   Content: {result['content'][:200]}...")

        output.append("")

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: supabase_search.py <query> [--limit N] [--type knowledge|debates|decisions|all]")
        sys.exit(1)

    # Parse arguments
    query = ""
    limit = 5
    search_type = "all"

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--limit":
            limit = int(sys.argv[i + 1])
            i += 2
        elif arg == "--type":
            search_type = sys.argv[i + 1]
            i += 2
        else:
            query += arg + " "
            i += 1

    query = query.strip()

    if not query:
        print("Error: Query is required", file=sys.stderr)
        sys.exit(1)

    # Initialize search
    searcher = SupabaseSearch()

    print(f"\nSearching for: '{query}'", file=sys.stderr)
    print("=" * 80)

    # Perform searches based on type
    if search_type in ["all", "knowledge"]:
        results = searcher.search_knowledge_base(query, limit)
        print(format_results(results, "knowledge_base"))

    if search_type in ["all", "debates"]:
        results = searcher.search_debates(query, limit)
        print(format_results(results, "debates"))

    if search_type in ["all", "decisions"]:
        results = searcher.search_decisions(query, limit)
        print(format_results(results, "decisions"))


if __name__ == "__main__":
    main()
