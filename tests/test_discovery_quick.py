#!/usr/bin/env python3
"""Quick test of intelligent command discovery."""

import requests
import json

CHAT_URL = "http://127.0.0.1:8000/chat"

def send_test_message(message, description):
    """Send message and print response."""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"USER: {message}")
    print(f"{'-'*80}")
    
    try:
        response = requests.post(
            CHAT_URL,
            json={"message": message},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        result = response.json()
        ai_response = result.get('response', 'No response')
        
        # Check for intelligent discovery indicators
        used_help = "run_vctl_help" in ai_response or "vctl --help" in ai_response.lower()
        used_discovery = "intelligent_vctl" in ai_response.lower()
        command_executed = "✅" in ai_response or any(word in ai_response.lower() for word in ["status", "peer", "tag", "auth", "stats"])
        
        print(f"AI: {ai_response[:500]}...")
        print(f"\n📊 Analysis:")
        print(f"  • Used vctl help: {'✅' if used_help else '❌'}")
        print(f"  • Used intelligent discovery: {'✅' if used_discovery else '❌'}")
        print(f"  • Command executed: {'✅' if command_executed else '❌'}")
        print(f"{'='*80}\n")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"{'='*80}\n")
        return False

# Run tests
print("\n🧪 QUICK INTELLIGENT DISCOVERY TESTS\n")

tests = [
    ("check agent health", "Health Check Discovery"),
    ("list agent tags", "Tag List Discovery"),  
    ("show peer list", "Peer List Discovery"),
    ("run vctl --help", "Direct Help Access"),
]

passed = 0
for msg, desc in tests:
    if send_test_message(msg, desc):
        passed += 1

print(f"\n{'='*80}")
print(f"RESULTS: {passed}/{len(tests)} tests completed")
print(f"{'='*80}\n")
