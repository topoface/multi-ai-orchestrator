#!/usr/bin/env python3
"""
Vertex Uploader
Upload content to Vertex AI knowledge base
"""
import sys
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "agents" / "vertex-learner"))

from vertex_learner import main

if __name__ == "__main__":
    main()
