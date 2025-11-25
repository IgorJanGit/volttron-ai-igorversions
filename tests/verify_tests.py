#!/usr/bin/env python3
"""
Quick Test Verification for VOLTTRON AI Chat Service
Runs a subset of critical tests to verify core functionality
"""

import sys
import os
import tempfile
import shutil
import json
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_ai_service_basic_functionality():
    """Test basic AI service functionality."""
    print("🧪 Testing AI Service Basic Functionality...")
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            from chat_app.ai_service import AIService
            ai_service = AIService('gpt-4o-mini')
            assert ai_service.model_name == 'gpt-4o-mini'
            assert isinstance(ai_service.conversation_history, list)
            assert isinstance(ai_service.function_tools, dict)
            assert not ai_service.volttron_checked
            assert ai_service.last_action is None
            expected_tools = [
                'start_volttron', 'stop_volttron', 'check_volttron_status',
                'vctl_status', 'vctl_install_listener_agent', 'vctl_uninstall_agent',
                'vctl_start_agent', 'vctl_stop_agent', 'verify_agent_uninstalled',
                'list_available_agents'
            ]
            
            for tool_name in expected_tools:
                assert tool_name in ai_service.function_tools
                assert 'function' in ai_service.function_tools[tool_name]
                assert 'schema' in ai_service.function_tools[tool_name]
            schemas = ai_service.get_function_schemas()
            assert isinstance(schemas, list)
            assert len(schemas) == len(ai_service.function_tools)
            
            print("  ✅ AI Service initialization successful")
            print(f"  ✅ {len(ai_service.function_tools)} function tools registered")
            print("  ✅ Function schemas generated correctly")
            
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def test_direct_command_detection():
    """Test direct command detection."""
    print("🧪 Testing Direct Command Detection...")
    
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            from chat_app.ai_service import AIService
            
            ai_service = AIService('gpt-4o-mini')
            with patch('chat_app.volttron_commands.check_volttron_status') as mock_check, \
                 patch('chat_app.volttron_commands.vctl_status') as mock_status:
                
                mock_check.return_value = "✓ VOLTTRON is running"  # Make it think VOLTTRON is running
                mock_status.return_value = "Agent status output"
                result = ai_service.call_function_tool('vctl_status', {})
                assert result == "Agent status output", f"Direct function call failed: got '{result}'"
                
                print("  ✅ Direct function tool calls working")
            with patch('chat_app.volttron_commands.vctl_uninstall_agent') as mock_uninstall:
                mock_uninstall.return_value = "Agent uninstalled"
                
                result = ai_service.call_function_tool('vctl_uninstall_agent', {'agent_uuid_or_tag': 'test-id'})
                assert result == "Agent uninstalled", f"Expected 'Agent uninstalled', got '{result}'"
                
                print("  ✅ Uninstall function calls working")
            result = ai_service._handle_direct_command('hello how are you?')
            assert result is None, f"Expected None for non-command, got '{result}'"
            
            print("  ✅ Non-command detection working")
            
    except Exception as e:
        print(f"  ❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def test_function_tool_calling():
    """Test function tool calling mechanism."""
    print("🧪 Testing Function Tool Calling...")
    
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            from chat_app.ai_service import AIService
            
            ai_service = AIService('gpt-4o-mini')
            with patch('chat_app.volttron_commands.check_volttron_status') as mock_status:
                mock_status.return_value = "VOLTTRON is running"
                
                try:
                    result = ai_service.call_function_tool('check_volttron_status', {})
                    assert result == "VOLTTRON is running", f"Expected 'VOLTTRON is running', got '{result}'"
                    mock_status.assert_called_once()
                except Exception as e:
                    print(f"    ❌ Error in function call test: {e}")
                    raise
            with patch('chat_app.volttron_commands.vctl_uninstall_agent') as mock_uninstall:
                mock_uninstall.return_value = "Agent removed successfully"
                
                try:
                    result = ai_service.call_function_tool(
                        'vctl_uninstall_agent', 
                        {'agent_uuid_or_tag': 'test-agent-id'}
                    )
                    assert result == "Agent removed successfully", f"Expected 'Agent removed successfully', got '{result}'"
                    mock_uninstall.assert_called_once_with(agent_uuid_or_tag='test-agent-id')
                except Exception as e:
                    print(f"    ❌ Error in function call with arguments test: {e}")
                    raise
            result = ai_service.call_function_tool('unknown_function', {})
            assert "Unknown function" in result, f"Expected error message containing 'Unknown function', got '{result}'"
            
            print("  ✅ Function tool calls working")
            print("  ✅ Function arguments passed correctly")
            print("  ✅ Unknown function handling working")
            
    except Exception as e:
        print(f"  ❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def test_contextual_reversal():
    """Test contextual reversal detection."""
    print("🧪 Testing Contextual Reversal Detection...")
    
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            from chat_app.ai_service import AIService
            
            ai_service = AIService('gpt-4o-mini')
            ai_service.last_action = "install_agent"
            ai_service.last_action_details = {"agent_type": "listener"}
            
            is_reversal, response = ai_service._detect_context_reversal("I changed my mind")
            assert is_reversal
            assert "uninstall the listener agent" in response
            assert ai_service.awaiting_reversal_confirmation
            reversal_phrases = [
                "i changed my mind", "undo that", "reverse it", "cancel that"
            ]
            
            for phrase in reversal_phrases:
                ai_service.last_action = "install_agent"
                ai_service.last_action_details = {"agent_type": "test"}
                
                is_reversal, response = ai_service._detect_context_reversal(phrase)
                assert is_reversal, f"Failed to detect reversal for: {phrase}"
            ai_service.last_action = None
            is_reversal, response = ai_service._detect_context_reversal("I changed my mind")
            assert not is_reversal
            
            print("  ✅ Reversal detection working")
            print("  ✅ Multiple reversal phrases recognized")
            print("  ✅ No false positives without previous action")
            
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def test_conversation_history():
    """Test conversation history management."""
    print("🧪 Testing Conversation History Management...")
    
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        test_history = {
            'history': [
                {'role': 'user', 'content': 'hello'},
                {'role': 'assistant', 'content': 'hi there'}
            ]
        }
        
        with open('conversation_history.json', 'w') as f:
            json.dump(test_history, f)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            from chat_app.ai_service import AIService
            
            ai_service = AIService('gpt-4o-mini')
            assert len(ai_service.conversation_history) == 2
            assert ai_service.conversation_history[0]['role'] == 'user'
            assert ai_service.conversation_history[1]['role'] == 'assistant'
            ai_service.conversation_history = [
                {'role': 'user', 'content': 'test message'},
                {'role': 'assistant', 'content': 'test response'}
            ]
            
            ai_service._save_conversation_history()
            assert os.path.exists('conversation_history.json')
            
            with open('conversation_history.json', 'r') as f:
                saved_data = json.load(f)
            
            assert 'history' in saved_data
            assert len(saved_data['history']) == 2
            
            print("  ✅ Conversation history loading working")
            print("  ✅ Conversation history saving working")
            
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)


def main():
    """Run verification tests."""
    print("🔍 VOLTTRON AI Chat Service - Quick Verification")
    print("=" * 60)
    
    tests = [
        test_ai_service_basic_functionality,
        test_direct_command_detection,
        test_function_tool_calling,
        test_contextual_reversal,
        test_conversation_history
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print()
        except Exception as e:
            failed += 1
            print(f"  ❌ Test failed: {e}")
            print()
    
    print("=" * 60)
    print(f"VERIFICATION SUMMARY: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All critical functionality verified!")
        return True
    else:
        print("⚠️ Some tests failed - check implementation")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)