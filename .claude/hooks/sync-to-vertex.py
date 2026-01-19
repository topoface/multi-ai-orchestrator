#!/usr/bin/env python3
"""
Sync to Vertex Hook (PostToolUse)
Automatically syncs file changes to Vertex AI after Edit/Write operations
"""
import json
import sys
import os
from pathlib import Path
from google.cloud import storage

def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(0)  # Exit gracefully to not block Claude

    # Extract file path
    tool_input = input_data.get('tool_input', {})
    file_path = tool_input.get('file_path', '')

    # Only sync docs/brain/ files
    if not file_path or not 'docs/brain/' in file_path:
        sys.exit(0)

    # Check if file exists
    if not os.path.exists(file_path):
        sys.exit(0)

    try:
        # Initialize GCS client
        client = storage.Client()
        bucket = client.bucket('multi-ai-memory-bank-phsysics')

        # Extract filename
        filename = Path(file_path).name

        # Upload to GCS context folder
        blob = bucket.blob(f'context/{filename}')

        with open(file_path, 'rb') as f:
            blob.upload_from_file(f)

        # Update metadata
        blob.metadata = {
            'source': 'claude-code-hook',
            'synced_at': input_data.get('timestamp', ''),
            'original_path': file_path
        }
        blob.patch()

        print(f"✅ Vertex AI sync: {filename}", file=sys.stderr)

    except Exception as e:
        # Don't fail - just log
        print(f"⚠ Vertex AI sync warning: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
