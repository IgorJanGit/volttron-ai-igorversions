#!/usr/bin/env python3
"""
Visual Chat Program Test Launcher
=================================

This script launches the VOLTTRON AI chat program for visual interaction.
You can see the AI talking and interact with it in real-time through a web interface.
"""

import sys
import os
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def print_header():
    """Print welcome header"""
    print("=" * 70)
    print("🚀 VOLTTRON AI VISUAL CHAT PROGRAM LAUNCHER")
    print("=" * 70)
    print("This will start the chat program so you can visually see it talking!")
    print()

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    chat_app_path = Path("chat_app")
    if not chat_app_path.exists():
        print("❌ Error: chat_app directory not found!")
        return False
    main_file = chat_app_path / "__main__.py"
    app_file = chat_app_path / "app.py"
    
    if not main_file.exists():
        print("❌ Error: __main__.py not found in chat_app!")
        return False
        
    if not app_file.exists():
        print("❌ Error: app.py not found in chat_app!")
        return False
    
    print("✅ All requirements met!")
    return True

def launch_chat_program():
    """Launch the actual chat program"""
    print("\n🌐 Starting VOLTTRON AI Chat Program...")
    print("📝 You can interact with it visually through the web interface")
    print()
    
    try:
        # Launch the chat application
        print("🚀 Launching: python -m chat_app")
        print("🌍 Web interface will be available at: http://localhost:5000")
        print()
        print("💬 Try these commands in the chat:")
        print("   • 'show me vctl status'")
        print("   • 'install a fake driver'")
        print("   • 'help me with vctl commands'")
        print("   • 'what agents are running?'")
        print()
        print("🛑 Press Ctrl+C to stop the chat program")
        print("=" * 70)
        
        # Start the chat application
        process = subprocess.Popen([
            sys.executable, "-m", "chat_app"
        ], cwd=os.getcwd())
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Try to open browser automatically
        try:
            print("🔗 Opening browser automatically...")
            webbrowser.open("http://localhost:5000")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print("   Please manually open: http://localhost:5000")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Chat program stopped by user")
        try:
            process.terminate()
        except:
            pass
    except Exception as e:
        print(f"\n❌ Error launching chat program: {e}")
        print("   Make sure you have all dependencies installed:")
        print("   pip install -r requirements.txt")

def run_validation_test():
    """Run the validation test first"""
    print("🧪 Running validation test...")
    
    try:
        result = subprocess.run([
            sys.executable, "-c", """
import sys
sys.path.append('.')
from tests.test_ai_service import TestPydanticAIIntegration
import unittest

# Run just the visual chat test
suite = unittest.TestSuite()
suite.addTest(TestPydanticAIIntegration('test_visual_chat_program_launch'))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

exit(0 if result.wasSuccessful() else 1)
"""
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Validation test passed!")
            return True
        else:
            print("❌ Validation test failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running validation test: {e}")
        return False

def main():
    """Main execution function"""
    print_header()
    if not check_requirements():
        sys.exit(1)
    
    # Run validation test
    if not run_validation_test():
        print("\n⚠️  Validation test failed, but continuing anyway...")
    
    print("\n" + "=" * 70)
    print("🎯 READY TO LAUNCH VISUAL CHAT PROGRAM!")
    print("=" * 70)
    
    # Ask user if they want to proceed
    try:
        response = input("\n🚀 Launch the visual chat program? (y/n): ").strip().lower()
        if response in ['y', 'yes', '']:
            launch_chat_program()
        else:
            print("👋 Launch cancelled by user")
    except KeyboardInterrupt:
        print("\n👋 Launch cancelled by user")

if __name__ == "__main__":
    main()