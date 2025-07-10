#!/usr/bin/env python3
"""
Startup script for Erg Screen Reader Web Interface
"""

import os
import sys

def check_environment():
    """Check if required environment variables are set."""
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it with:")
        print("  export OPENAI_API_KEY='your-api-key'")
        print("\nOr create a .env file with:")
        print("  OPENAI_API_KEY=your-api-key")
        return False
    
    print("✅ Environment variables are properly configured.")
    return True

def main():
    """Main startup function."""
    print("🚣 Erg Screen Reader Web Interface")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check if Flask is installed
    try:
        import flask
        print("✅ Flask is installed.")
    except ImportError:
        print("❌ Error: Flask is not installed.")
        print("Please install dependencies with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Check if our modules are available
    try:
        from src.erg_screen_reader import ErgScreenReader
        print("✅ Erg Screen Reader module is available.")
    except ImportError as e:
        print(f"❌ Error: Could not import Erg Screen Reader module: {e}")
        sys.exit(1)
    
    print("\n🚀 Starting web server...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 40)
    
    # Import and run the Flask app
    from src.app import app
    app.run(debug=True, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()