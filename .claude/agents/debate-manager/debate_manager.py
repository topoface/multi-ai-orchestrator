#!/usr/bin/env python3
"""
Debate Manager
High-level orchestration of Multi-AI debates
"""
import sys
import json
from pathlib import Path

# Import the debate engine from skills
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "debate-request"))
from debate_engine import DebateEngine, format_result, save_result


def start_debate(topic: str, max_rounds: int = 4, expert_mode: bool = False):
    """Start a new debate"""
    print(f"🔥 Starting debate: {topic}\n", file=sys.stderr)

    engine = DebateEngine(topic, expert_mode, max_rounds)
    result = engine.conduct_debate()

    # Format and display
    output = format_result(result)
    print(output)

    # Save results
    save_result(result)

    return result


def resume_debate(debate_id: str, from_round: int):
    """Resume an existing debate (placeholder for future implementation)"""
    print(f"Resuming debate {debate_id} from round {from_round}...", file=sys.stderr)
    # TODO: Load previous state and continue
    print("Note: Resume functionality not yet implemented", file=sys.stderr)


def check_status(debate_id: str):
    """Check status of a debate (placeholder for future implementation)"""
    print(f"Checking status of debate {debate_id}...", file=sys.stderr)
    # TODO: Load and display status
    print("Note: Status check not yet implemented", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("Usage: debate_manager.py <command> [options]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  start --topic <topic> [--max-rounds N] [--expert]", file=sys.stderr)
        print("  resume --debate-id <id> --from-round N", file=sys.stderr)
        print("  status --debate-id <id>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'start':
            # Parse arguments
            topic = ""
            max_rounds = 4
            expert_mode = False

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--topic' and i + 1 < len(sys.argv):
                    topic = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--max-rounds' and i + 1 < len(sys.argv):
                    max_rounds = int(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == '--expert':
                    expert_mode = True
                    i += 1
                else:
                    # Collect remaining as topic
                    topic += " " + sys.argv[i]
                    i += 1

            if not topic:
                print("Error: --topic required", file=sys.stderr)
                sys.exit(1)

            result = start_debate(topic.strip(), max_rounds, expert_mode)

        elif command == 'resume':
            debate_id = ""
            from_round = 1

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--debate-id' and i + 1 < len(sys.argv):
                    debate_id = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--from-round' and i + 1 < len(sys.argv):
                    from_round = int(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1

            if not debate_id:
                print("Error: --debate-id required", file=sys.stderr)
                sys.exit(1)

            resume_debate(debate_id, from_round)

        elif command == 'status':
            debate_id = ""

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--debate-id' and i + 1 < len(sys.argv):
                    debate_id = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1

            if not debate_id:
                print("Error: --debate-id required", file=sys.stderr)
                sys.exit(1)

            check_status(debate_id)

        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
