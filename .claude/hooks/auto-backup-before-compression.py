#!/usr/bin/env python3
"""
Auto Backup Before Compression Hook (UserPromptSubmit)
Automatically backs up conversation locally when file size exceeds threshold
"""
import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# Backup threshold: 50MB (압축은 보통 100MB+ 에서 발생)
BACKUP_THRESHOLD_MB = 50
BACKUP_MARKER_FILE = Path.home() / '.claude' / 'last_backup_size.txt'
BACKUP_DIR = Path.home() / 'multi-ai-orchestrator' / 'backups' / 'conversations'

def get_current_session_file():
    """Find current session .jsonl file"""
    projects_dir = Path.home() / '.claude' / 'projects' / '-home-wishingfly'
    if not projects_dir.exists():
        return None

    # Find most recently modified .jsonl file
    jsonl_files = list(projects_dir.glob('*.jsonl'))
    if not jsonl_files:
        return None

    return max(jsonl_files, key=lambda f: f.stat().st_mtime)

def get_last_backup_size():
    """Get size of last backup"""
    try:
        if BACKUP_MARKER_FILE.exists():
            return int(BACKUP_MARKER_FILE.read_text().strip())
    except:
        pass
    return 0

def save_last_backup_size(size):
    """Save current backup size"""
    BACKUP_MARKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_MARKER_FILE.write_text(str(size))

def main():
    try:
        # Read hook input (not used but required)
        input_data = json.load(sys.stdin)
    except:
        pass

    # Find current session file
    session_file = get_current_session_file()
    if not session_file or not session_file.exists():
        sys.exit(0)

    # Check file size
    file_size_mb = session_file.stat().st_size / (1024 * 1024)
    last_backup_size_mb = get_last_backup_size() / (1024 * 1024)

    # Backup if:
    # 1. File exceeds threshold AND
    # 2. Grew significantly since last backup (10MB+)
    size_diff = file_size_mb - last_backup_size_mb

    if file_size_mb < BACKUP_THRESHOLD_MB or size_diff < 10:
        # No backup needed
        sys.exit(0)

    try:
        # Create backup directory
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_id = session_file.stem
        backup_file = BACKUP_DIR / f'backup_{session_id}_{timestamp}.jsonl'

        # Copy file locally
        shutil.copy2(session_file, backup_file)

        # Save backup marker
        save_last_backup_size(session_file.stat().st_size)

        print(f"✅ 대화 자동 백업 완료: {file_size_mb:.1f}MB → 로컬", file=sys.stderr)
        print(f"   위치: {backup_file}", file=sys.stderr)

    except Exception as e:
        # Don't fail - just warn
        print(f"⚠ 백업 경고: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
