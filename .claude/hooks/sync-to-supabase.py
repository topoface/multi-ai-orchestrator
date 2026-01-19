#!/usr/bin/env python3
"""
파일 변경 시 자동으로 Supabase에 동기화
PostToolUse Hook: Edit/Write 후 실행
"""
import json
import sys
import os
from pathlib import Path

# Supabase client (optional)
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    sys.exit(0)  # Silently exit if Supabase not available

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    sys.exit(0)  # Silently exit if not configured

try:
    input_data = json.load(sys.stdin)
    file_path = input_data.get('tool_input', {}).get('file_path', '')

    # Only sync docs/brain/ files
    if not file_path or 'docs/brain/' not in file_path:
        sys.exit(0)

    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Save to knowledge_base table
    data = {
        'content': content,
        'metadata': {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'synced_at': input_data.get('timestamp', None)
        }
    }

    response = supabase.table('knowledge_base').insert(data).execute()
    print(f"✓ Supabase sync: {file_path}", file=sys.stderr)

except Exception as e:
    # Don't fail the hook, just log the error
    print(f"⚠ Supabase sync failed: {e}", file=sys.stderr)

sys.exit(0)
