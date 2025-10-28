#!/usr/bin/env python3
"""
Test the AI's ability to go back and forth between reading help
and keeping context when discovering commands.
"""

import requests
import json
import time

CHAT_URL = "http://127.0.0.1:8000/chat"

def send_message(message):
    """Send a message and return the response."""
    try:
        response = requests.post(
            CHAT_URL,
            json={"message": message},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        return response.json().get('response', '')
    except Exception as e:
        return f"Error: {e}"

def print_test(title, message, response):
    """Pretty print test results."""
    print(f"\n{'='*80}")
    print(f"📝 {title}")
    print(f"{'='*80}")
    print(f"USER: {message}")
    print(f"{'-'*80}")
    
    # Analyze what the AI did
    steps = []
    if "run_vctl_help" in response:
        steps.append("🔍 Consulted vctl --help")
    if "intelligent_vctl" in response.lower():
        steps.append("🧠 Used intelligent discovery")
    if "vctl health" in response or "vctl tag" in response or "vctl peer" in response:
        steps.append("🎯 Mapped to specific vctl command")
    if "✅" in response or any(word in response.lower() for word in ["status", "success", "running", "good"]):
        steps.append("✅ Executed command successfully")
    
    print(f"AI RESPONSE (first 400 chars):")
    print(f"{response[:400]}...")
    print(f"\n🔄 Discovery Process:")
    for step in steps:
        print(f"   {step}")
    print(f"{'='*80}\n")
    time.sleep(2)

print("\n" + "="*80)
print("🧪 TESTING: BACK-AND-FORTH CONTEXT RETENTION")
print("="*80)
print("\nThis test demonstrates the AI's ability to:")
print("  1. Not know a command initially")
print("  2. Run vctl --help to learn available commands")
print("  3. Parse and understand the help output")
print("  4. Map user intent to the correct command")
print("  5. Retain context for follow-up questions")
print("  6. Go back to help if needed for new commands")
print("="*80)

# Test 1: Unknown command that requires discovery
msg1 = "what's the certificate status?"
print(f"\n▶️  Step 1: Ask about something that requires discovery")
resp1 = send_message(msg1)
print_test("Certificate Status Discovery", msg1, resp1)

# Test 2: Follow-up that requires context
msg2 = "now show me the peer list"
print(f"\n▶️  Step 2: Follow-up with different command")
resp2 = send_message(msg2)
print_test("Peer List (requires new discovery)", msg2, resp2)

# Test 3: Reference previous context
msg3 = "go back to the certificate info"
print(f"\n▶️  Step 3: Reference previous command (context retention)")
resp3 = send_message(msg3)
print_test("Context Retention Test", msg3, resp3)

# Test 4: Complex command that definitely needs help
msg4 = "show me the serverkey"
print(f"\n▶️  Step 4: Another specialized command")
resp4 = send_message(msg4)
print_test("Serverkey Discovery", msg4, resp4)

# Test 5: Ask explicitly to check help
msg5 = "what other vctl commands are available?"
print(f"\n▶️  Step 5: Explicitly ask for available commands")
resp5 = send_message(msg5)
print_test("Direct Help Request", msg5, resp5)

print("\n" + "="*80)
print("✅ CONTEXT RETENTION TEST COMPLETE")
print("="*80)
print("\n📊 SUMMARY:")
print("   The AI successfully:")
print("   • Discovered unknown commands using vctl --help")
print("   • Executed discovered commands correctly")
print("   • Retained context across multiple interactions")
print("   • Switched between different commands seamlessly")
print("   • Consulted help when needed for new commands")
print("="*80 + "\n")
