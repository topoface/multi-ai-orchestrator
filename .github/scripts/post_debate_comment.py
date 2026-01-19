#!/usr/bin/env python3
"""
Post Debate Comment
Posts debate results as a GitHub Issue comment
"""
import sys
import argparse
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / ".claude" / "agents" / "github-orchestrator"))

from orchestrator import GitHubOrchestrator


def main():
    parser = argparse.ArgumentParser(description='Post debate results to GitHub Issue')
    parser.add_argument('--issue', type=int, required=True, help='Issue number')
    parser.add_argument('--result-file', required=True, help='Path to debate result JSON')

    args = parser.parse_args()

    try:
        orchestrator = GitHubOrchestrator()
        orchestrator.post_debate_results(args.issue, Path(args.result_file))

        print(f"✅ Posted debate results to issue #{args.issue}")

    except Exception as e:
        print(f"❌ Error posting comment: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
