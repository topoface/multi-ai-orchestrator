#!/usr/bin/env python3
"""
Trigger Debate Hook (UserPromptSubmit)
Automatically detects debate keywords and suggests starting a debate
"""
import json
import sys
import subprocess
from pathlib import Path

# Keywords that suggest a debate might be useful
DEBATE_KEYWORDS = [
    "어떻게 생각해",
    "의견",
    "추천",
    "어떤게 나아",
    "결정",
    "선택",
    "고민",
    "what do you think",
    "opinion",
    "recommend",
    "which is better",
    "decide",
    "choice",
    "should i",
    "or"
]

def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(0)

    # Extract user prompt
    user_prompt = input_data.get('prompt', '').lower()

    if not user_prompt:
        sys.exit(0)

    # Check for debate keywords
    has_debate_keyword = any(keyword in user_prompt for keyword in DEBATE_KEYWORDS)

    if not has_debate_keyword:
        sys.exit(0)

    # Found debate keyword - log it (don't automatically start debate)
    # The user can choose to use /debate skill manually
    print("💡 Debate keyword detected! Consider using /debate skill for multi-AI discussion.", file=sys.stderr)

    # Optional: Log to a file for analytics
    try:
        project_root = Path(__file__).parent.parent.parent
        log_file = project_root / "multi-ai-orchestrator" / ".debate_suggestions.log"

        with open(log_file, 'a') as f:
            f.write(f"{input_data.get('timestamp', '')}: {user_prompt[:100]}\n")
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
