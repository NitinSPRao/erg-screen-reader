#!/usr/bin/env python3
"""
Setup script for Erg Screen Reader development environment.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print status."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Set up the development environment."""
    print("🚣 Erg Screen Reader - Development Setup")
    print("=" * 45)
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if uv is installed
    if not run_command("uv --version", "Checking uv installation"):
        print("\n❌ uv is not installed. Please install it first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   or visit: https://docs.astral.sh/uv/getting-started/installation/")
        return False
    
    # Create virtual environment and install dependencies
    commands = [
        ("uv venv", "Creating virtual environment"),
        ("uv pip install -e .", "Installing package in development mode"),
        ("uv pip install -e '.[dev]'", "Installing development dependencies"),
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    print("   source .venv/bin/activate  # On Unix/macOS")
    print("   .venv\\Scripts\\activate     # On Windows")
    print("\n2. Set up your environment variables:")
    print("   cp .env.example .env")
    print("   # Edit .env with your API keys")
    print("\n3. Start the development server:")
    print("   python scripts/dev.py")
    print("   # or")
    print("   uv run erg-web")
    print("\n4. Run the CLI:")
    print("   uv run erg-reader image.png")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)