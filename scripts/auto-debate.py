#!/usr/bin/env python3
"""
Auto Debate Script
Standalone script to run multi-AI debates locally
"""
import sys
from pathlib import Path

# Add skills to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "debate-request"))

from debate_engine import main

if __name__ == "__main__":
    main()
