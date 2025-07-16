#!/usr/bin/env python3
"""
Simple wrapper script for FIT file analysis.
Place this in your project root for easy access.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the analyzer
from fit_analyzer import main

if __name__ == "__main__":
    main()