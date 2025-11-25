#!/usr/bin/env python3
"""
Simple Python Test Runner for VOLTTRON AI Chat Service
Alternative to bash script for cross-platform compatibility
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def colored_print(text, color='white'):
    """Print colored text to terminal."""
    colors = {
        'red': '\033[0;31m',
        'green': '\033[0;32m',
        'yellow': '\033[1;33m',
        'blue': '\033[0;34m',
        'white': '\033[0m'
    }
    
    color_code = colors.get(color, colors['white'])
    reset_code = colors['white']
    print(f"{color_code}{text}{reset_code}")


def check_pytest_available():
    """Check if pytest is available, install if not."""
    try:
        import pytest
        return True
    except ImportError:
        colored_print("📦 pytest not found. Installing test dependencies...", 'yellow')
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'test_requirements.txt'], check=True)
        return True


def install_test_dependencies():
    """Install test dependencies."""
    colored_print("📦 Installing test dependencies...", 'yellow')
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'test_requirements.txt'], check=True)
        colored_print("✅ Dependencies installed", 'green')
        return True
    except subprocess.CalledProcessError as e:
        colored_print(f"❌ Failed to install dependencies: {e}", 'red')
        return False


def run_tests(verbose=False, coverage=False, html_report=False, test_file=None):
    """Run the tests with specified options."""
    os.environ['TESTING'] = 'true'
    if 'OPENAI_API_KEY' not in os.environ:
        os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'
    
    # Build command
    cmd = [sys.executable, '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
        
    if coverage:
        cmd.extend(['--cov=chat_app', '--cov-report=term'])
        if html_report:
            cmd.append('--cov-report=html:htmlcov')
    
    if test_file:
        if not test_file.startswith('tests/'):
            test_file = f'tests/{test_file}'
        cmd.append(test_file)
    else:
        cmd.append('tests/')
    cmd.extend(['--tb=short', '--strict-markers'])
    
    colored_print("🔍 Running tests...", 'blue')
    colored_print(f"Command: {' '.join(cmd)}", 'blue')
    print()
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print()
            colored_print("✅ All tests passed!", 'green')
            
            if html_report:
                colored_print("📊 HTML coverage report generated: htmlcov/index.html", 'blue')
                
            return True
        else:
            print()
            colored_print("❌ Some tests failed!", 'red')
            return False
            
    except KeyboardInterrupt:
        colored_print("\n⚠️ Tests interrupted by user", 'yellow')
        return False
    except Exception as e:
        colored_print(f"❌ Error running tests: {e}", 'red')
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="VOLTTRON AI Chat Service Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py                    # Run all tests
  python test_runner.py -v -c              # Verbose with coverage
  python test_runner.py -i -c --html       # Install deps, coverage with HTML
  python test_runner.py -f test_isolated.py  # Run specific test file
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Run tests with verbose output')
    parser.add_argument('-c', '--coverage', action='store_true',
                        help='Generate coverage report')
    parser.add_argument('--html', action='store_true',
                        help='Generate HTML coverage report')
    parser.add_argument('-i', '--install', action='store_true',
                        help='Install test dependencies first')
    parser.add_argument('-f', '--file', type=str,
                        help='Run specific test file')
    
    args = parser.parse_args()
    
    colored_print("🧪 VOLTTRON AI Chat Service Test Runner", 'blue')
    print("=" * 50)
    
    # Install dependencies if requested
    if args.install:
        if not install_test_dependencies():
            sys.exit(1)
        print()
    if not check_pytest_available():
        sys.exit(1)
    
    # Run tests
    success = run_tests(
        verbose=args.verbose,
        coverage=args.coverage,
        html_report=args.html,
        test_file=args.file
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()