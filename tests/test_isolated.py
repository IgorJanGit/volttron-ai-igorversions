#!/usr/bin/env python3
"""
Isolated Unit Tests for VOLTTRON AI Chat Service
Tests individual components in isolation without external dependencies
"""

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAIServiceIsolated(unittest.TestCase):
    """Isolated tests for AI service core functionality."""
    
    def setUp(self):
        """Set up isolated test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key-for-testing'
        })
        self.env_patcher.start()
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
        self.env_patcher.stop()
    
    def test_ai_service_initialization(self):
        """Test that AI service initializes correctly."""
        from chat_app.ai_service import AIService
        ai_service = AIService('gpt-4o-mini')
        self.assertEqual(ai_service.model_name, 'gpt-4o-mini')
        self.assertIsInstance(ai_service.conversation_history, list)
        self.assertIsInstance(ai_service.function_tools, dict)
        self.assertFalse(ai_service.volttron_checked)
        self.assertIsNone(ai_service.last_action)
        
    def test_function_tools_registration(self):
        """Test that function tools are registered correctly."""
        from chat_app.ai_service import AIService
        ai_service = AIService('gpt-4o-mini')
        expected_tools = [
            'start_volttron', 'stop_volttron', 'check_volttron_status',
            'vctl_status', 'vctl_install_listener_agent', 'vctl_uninstall_agent',
            'vctl_start_agent', 'vctl_stop_agent', 'verify_agent_uninstalled',
            'list_available_agents'
        ]
        
        for tool_name in expected_tools:
            self.assertIn(tool_name, ai_service.function_tools)
            self.assertIn('function', ai_service.function_tools[tool_name])
            self.assertIn('schema', ai_service.function_tools[tool_name])
            
    def test_function_schema_generation(self):
        """Test that function schemas are generated correctly."""
        from chat_app.ai_service import AIService
        ai_service = AIService('gpt-4o-mini')
        schemas = ai_service.get_function_schemas()
        
        self.assertIsInstance(schemas, list)
        self.assertEqual(len(schemas), len(ai_service.function_tools))
        for schema in schemas:
            self.assertIn('name', schema)
            self.assertIn('description', schema)
            self.assertIn('parameters', schema)
            self.assertIn('type', schema['parameters'])
            self.assertEqual(schema['parameters']['type'], 'object')
    
    def test_unknown_function_handling(self):
        """Test handling of unknown function calls."""
        from chat_app.ai_service import AIService
        ai_service = AIService('gpt-4o-mini')
        
        result = ai_service.call_function_tool('unknown_function', {})
        self.assertIn("Unknown function", result)
        self.assertIn("unknown_function", result)
    
    def test_contextual_reversal_detection(self):
        """Test contextual reversal detection logic."""
        from chat_app.ai_service import AIService
        ai_service = AIService('gpt-4o-mini')
        ai_service.last_action = "install_agent"
        ai_service.last_action_details = {"agent_type": "listener"}
        
        is_reversal, response = ai_service._detect_context_reversal("I changed my mind")
        self.assertTrue(is_reversal)
        self.assertIn("uninstall the listener agent", response)
        self.assertTrue(ai_service.awaiting_reversal_confirmation)
        reversal_phrases = [
            "i changed my mind", "undo that", "reverse it", "cancel that",
            "forget it", "actually no", "i made a mistake"
        ]
        
        for phrase in reversal_phrases:
            ai_service.last_action = "install_agent"
            ai_service.last_action_details = {"agent_type": "test"}
            ai_service.awaiting_reversal_confirmation = False
            
            is_reversal, response = ai_service._detect_context_reversal(phrase)
            self.assertTrue(is_reversal, f"Failed to detect reversal for: {phrase}")
        ai_service.last_action = None
        is_reversal, response = ai_service._detect_context_reversal("I changed my mind")
        self.assertFalse(is_reversal)
        self.assertEqual(response, "")
    
    def test_conversation_history_management(self):
        """Test conversation history loading and saving."""
        from chat_app.ai_service import AIService
        test_history = {
            'history': [
                {'role': 'user', 'content': 'hello'},
                {'role': 'assistant', 'content': 'hi there'}
            ]
        }
        
        with open('conversation_history.json', 'w') as f:
            json.dump(test_history, f)
            
        ai_service = AIService('gpt-4o-mini')
        self.assertEqual(len(ai_service.conversation_history), 2)
        self.assertEqual(ai_service.conversation_history[0]['role'], 'user')
        self.assertEqual(ai_service.conversation_history[1]['role'], 'assistant')
        ai_service.conversation_history = [
            {'role': 'user', 'content': 'test message'},
            {'role': 'assistant', 'content': 'test response'}
        ]
        
        ai_service._save_conversation_history()
        self.assertTrue(os.path.exists('conversation_history.json'))
        
        with open('conversation_history.json', 'r') as f:
            saved_data = json.load(f)
        
        self.assertIn('history', saved_data)
        self.assertEqual(len(saved_data['history']), 2)
    
    def test_conversation_history_truncation(self):
        """Test that conversation history is properly truncated."""
        from chat_app.ai_service import AIService
        large_history = {
            'history': [{'role': 'user', 'content': f'message {i}'} for i in range(50)]
        }
        
        with open('conversation_history.json', 'w') as f:
            json.dump(large_history, f)
            
        ai_service = AIService('gpt-4o-mini')
        self.assertEqual(len(ai_service.conversation_history), 20)
        self.assertEqual(ai_service.conversation_history[0]['content'], 'message 30')
        self.assertEqual(ai_service.conversation_history[-1]['content'], 'message 49')
    
    def test_invalid_conversation_history_handling(self):
        """Test handling of invalid conversation history file."""
        from chat_app.ai_service import AIService
        with open('conversation_history.json', 'w') as f:
            f.write('invalid json content')
        ai_service = AIService('gpt-4o-mini')
        self.assertEqual(len(ai_service.conversation_history), 0)
    
    def test_model_info_retrieval(self):
        self.skipTest("get_model_info method removed in AI-first refactor")
        return
        self.skipTest("get_model_info method removed in AI-first refactor")
        return
        """Test model information retrieval."""
        from chat_app.ai_service import AIService
        ai_service = AIService('gpt-4o-mini')
        info = ai_service.get_model_info()
        
        self.assertEqual(info['model_name'], 'gpt-4o-mini')
        self.assertEqual(info['model_id'], 'gpt-4o-mini')
        ai_service2 = AIService('openai:gpt-4o-mini')
        info2 = ai_service2.get_model_info()
        
        self.assertEqual(info2['model_name'], 'openai:gpt-4o-mini')
        self.assertEqual(info2['provider'], 'openai')
        self.assertEqual(info2['model_id'], 'gpt-4o-mini')
    
    def test_direct_command_pattern_matching(self):
        """Test direct command pattern matching logic."""
        from chat_app.ai_service import AIService
        
        ai_service = AIService('gpt-4o-mini')
        result = ai_service._handle_direct_command('hello how are you?')
        self.assertIsNone(result)
        
        result = ai_service._handle_direct_command('tell me about the weather')
        self.assertIsNone(result)
        
        result = ai_service._handle_direct_command('')
        self.assertIsNone(result)
        
        result = ai_service._handle_direct_command('   ')
        self.assertIsNone(result)
    
    @patch('chat_app.volttron_commands.vctl_uninstall_agent')
    def test_function_tool_action_tracking(self, mock_uninstall):
        """Test that function tool calls are tracked for reversal."""
        from chat_app.ai_service import AIService
        
        ai_service = AIService('gpt-4o-mini')
        mock_uninstall.return_value = "Agent uninstalled successfully"
        result = ai_service.call_function_tool('vctl_uninstall_agent', {'agent_uuid_or_tag': 'test-id'})
        self.assertEqual(ai_service.last_action, 'uninstall_agent')
        self.assertIn('function', ai_service.last_action_details)
        self.assertIn('arguments', ai_service.last_action_details)
        self.assertIn('result', ai_service.last_action_details)
        self.assertEqual(ai_service.last_action_details['function'], 'vctl_uninstall_agent')
    
    @patch('chat_app.volttron_commands.vctl_install_listener_agent')
    def test_install_action_tracking(self, mock_install):
        """Test that install actions are tracked correctly."""
        from chat_app.ai_service import AIService
        
        ai_service = AIService('gpt-4o-mini')
        mock_install.return_value = "Agent installed successfully"
        result = ai_service.call_function_tool('vctl_install_listener_agent', {})
        self.assertEqual(ai_service.last_action, 'install_agent')
        self.assertIn('function', ai_service.last_action_details)
        self.assertEqual(ai_service.last_action_details['function'], 'vctl_install_listener_agent')


def run_isolated_tests():
    """Run isolated unit tests."""
    print("🧪 VOLTTRON AI Chat Service - Isolated Unit Tests")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIServiceIsolated)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("ISOLATED TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.testsRun > 0:
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
            
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success = result.wasSuccessful()
    
    if success:
        print("\n🎉 All isolated tests passed!")
    else:
        print("\n⚠️ Some isolated tests failed")
        
    return success


if __name__ == '__main__':
    success = run_isolated_tests()
    sys.exit(0 if success else 1)