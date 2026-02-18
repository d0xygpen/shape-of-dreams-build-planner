"""
Shape of Dreams - Build Analyzer
Desktop application entry point.

Run with: python app.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from gui.app import run

if __name__ == "__main__":
    run()
