#!/usr/bin/env python3
"""
Save Debate Result Hook (Stop)
Automatically saves session logs to Vertex AI when Claude stops
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from google.cloud import storage

def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(0)

    # Check if this session involved debate or important decisions
    # Look for keywords in the conversation
    conversation_text = json.dumps(input_data).lower()

    debate_indicators = ['debate', 'decision', 'consensus', 'claude', 'gemini', 'perplexity']
    has_debate = any(indicator in conversation_text for indicator in debate_indicators)

    if not has_debate:
        # Skip saving non-debate sessions to reduce clutter
        sys.exit(0)

    try:
        # Initialize GCS client
        client = storage.Client()
        bucket = client.bucket('multi-ai-memory-bank-phsysics')

        # Generate timestamp-based filename
        timestamp = datetime.utcnow().isoformat().replace(':', '-').replace('.', '-')
        blob_name = f'session_logs/session_{timestamp}.json'

        # Upload session log
        blob = bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(input_data, indent=2),
            content_type='application/json'
        )

        # Update metadata
        blob.metadata = {
            'session_type': 'claude-code',
            'saved_at': datetime.utcnow().isoformat(),
            'has_debate': str(has_debate)
        }
        blob.patch()

        print(f"✅ Session log saved to Vertex AI: {blob_name}", file=sys.stderr)

    except Exception as e:
        # Don't fail - just log
        print(f"⚠ Session log save warning: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
