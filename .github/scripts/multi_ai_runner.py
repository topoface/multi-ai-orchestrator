#!/usr/bin/env python3
"""
Multi-AI Runner
Entry point for GitHub Actions to run multi-AI debates
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / ".claude" / "skills" / "debate-request"))

from debate_engine import DebateEngine, format_result, save_result


def main():
    parser = argparse.ArgumentParser(description='Run Multi-AI Debate')
    parser.add_argument('--topic', required=True, help='Debate topic')
    parser.add_argument('--issue-number', type=int, help='GitHub issue number')
    parser.add_argument('--max-rounds', type=int, default=4, help='Maximum debate rounds')
    parser.add_argument('--expert', action='store_true', help='Enable expert mode (Perplexity)')

    args = parser.parse_args()

    print(f"🔥 Starting Multi-AI Debate")
    print(f"Topic: {args.topic}")
    print(f"Max rounds: {args.max_rounds}")
    print(f"Expert mode: {args.expert}")
    if args.issue_number:
        print(f"GitHub Issue: #{args.issue_number}")
    print()

    try:
        # Run debate
        engine = DebateEngine(args.topic, args.expert, args.max_rounds)
        result = engine.conduct_debate()

        # Add issue reference if provided
        if args.issue_number:
            result['github_issue'] = args.issue_number

        # Format and display
        output = format_result(result)
        print(output)

        # Save results
        save_result(result)

        print("\n✅ Debate completed successfully")

        # Exit with 0 if consensus reached, 1 if review needed
        if result['consensus_score'] >= 0.85:
            sys.exit(0)
        else:
            print("⚠️ Consensus not reached - manual review required")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Debate failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
