#!/usr/bin/env python3
"""
Development startup script for Erg Screen Reader.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Start the development server with hot reload."""
    project_root = Path(__file__).parent.parent
    
    print("🚣 Erg Screen Reader - Development Mode")
    print("=" * 45)
    print("🔄 Hot reload enabled")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 45)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "erg_screen_reader.web:app",
            "--host", "0.0.0.0",
            "--port", "8080",
            "--reload",
            "--reload-dir", str(project_root / "erg_screen_reader"),
            "--reload-dir", str(project_root / "templates"),
            "--reload-dir", str(project_root / "static")
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()