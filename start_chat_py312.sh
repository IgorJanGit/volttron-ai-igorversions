#!/bin/bash
# Start chat app with Python 3.12 for Pydantic AI support
cd "$(dirname "$0")"
echo "Starting VOLTTRON AI Chat with Python 3.12 (Pydantic AI enabled)..."
python3.12 -m chat_app
