#!/usr/bin/env python3
"""
Vertex GitHub Bridge
Bridge script for syncing between Vertex AI and GitHub
"""
import sys
from pathlib import Path

# Add skills to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "github-sync"))

from sync_manager import main

if __name__ == "__main__":
    main()
