"""
Pytest configuration and fixtures for VOLTTRON AI tests.

This module loads environment variables from .env file to ensure
API keys are available for tests that require actual AI model calls.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment variables from {env_file}")
else:
    print(f"Warning: .env file not found at {env_file}")
