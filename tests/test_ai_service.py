#!/usr/bin/env python3
"""
Comprehensive Unit Tests for VOLTTRON AI Chat Service

This test suite covers:
- Function tools registration and schema generation
- Direct command detection and handling
- Function tool calling mechanism
- Contextual reversal detection
- Conversation history management
- Error handling and edge cases
- Integration scenarios

Author: VOLTTRON AI System
Date: October 2025
"""

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AI service
from chat_app.ai_service import AIService


class TestAIServiceInitialization(unittest.TestCase):
    """Test AI service initialization and setup."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock environment to avoid API key requirements
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
        ai_service = AIService('gpt-4o-mini')
        
        # Test basic properties
        self.assertEqual(ai_service.model_name, 'gpt-4o-mini')
        self.assertIsInstance(ai_service.conversation_history, list)
        self.assertIsInstance(ai_service.function_tools, dict)
        self.assertFalse(ai_service.volttron_checked)
        self.assertIsNone(ai_service.last_action)
        
    def test_function_tools_registration(self):
        """Test that function tools are registered correctly."""
        ai_service = AIService('gpt-4o-mini')
        
        # Check that expected function tools are registered
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
        ai_service = AIService('gpt-4o-mini')
        schemas = ai_service.get_function_schemas()
        
        self.assertIsInstance(schemas, list)
        self.assertEqual(len(schemas), len(ai_service.function_tools))
        
        # Check schema structure
        for schema in schemas:
            self.assertIn('name', schema)
            self.assertIn('description', schema)
            self.assertIn('parameters', schema)
            self.assertIn('type', schema['parameters'])
            self.assertEqual(schema['parameters']['type'], 'object')


class TestFunctionToolCalling(unittest.TestCase):
    """Test function tool calling mechanism."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key-for-testing'
        })
        self.env_patcher.start()
        
        self.ai_service = AIService('gpt-4o-mini')
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
        self.env_patcher.stop()
    
    @patch('chat_app.volttron_commands.check_volttron_status')
    def test_function_tool_call_success(self, mock_volttron_status):
        """Test successful function tool call."""
        mock_volttron_status.return_value = "VOLTTRON is running"
        
        result = self.ai_service.call_function_tool('check_volttron_status', {})
        
        self.assertEqual(result, "VOLTTRON is running")
        mock_volttron_status.assert_called_once()
        
    @patch('chat_app.volttron_commands.vctl_uninstall_agent')
    def test_function_tool_call_with_arguments(self, mock_uninstall):
        """Test function tool call with arguments."""
        mock_uninstall.return_value = "Agent removed successfully"
        
        result = self.ai_service.call_function_tool(
            'vctl_uninstall_agent', 
            {'agent_uuid_or_tag': 'test-agent-id'}
        )
        
        self.assertEqual(result, "Agent removed successfully")
        mock_uninstall.assert_called_once_with(agent_uuid_or_tag='test-agent-id')
        
    def test_function_tool_call_unknown_function(self):
        """Test function tool call with unknown function."""
        result = self.ai_service.call_function_tool('unknown_function', {})
        
        self.assertIn("Unknown function", result)
        self.assertIn("unknown_function", result)
        
    @patch('chat_app.volttron_commands.start_volttron')
    def test_function_tool_call_exception_handling(self, mock_start):
        """Test function tool call exception handling."""
        mock_start.side_effect = Exception("Test error")
        
        result = self.ai_service.call_function_tool('start_volttron', {})
        
        self.assertIn("Error calling start_volttron", result)
        self.assertIn("Test error", result)
        
    def test_action_tracking_for_reversal(self):
        """Test that function calls are tracked for contextual reversal."""
        with patch('chat_app.volttron_commands.vctl_install_listener_agent') as mock_install:
            mock_install.return_value = "Listener installed"
            
            self.ai_service.call_function_tool('vctl_install_listener_agent', {})
            
            self.assertEqual(self.ai_service.last_action, 'install_agent')
            self.assertIn('function', self.ai_service.last_action_details)
            self.assertIn('arguments', self.ai_service.last_action_details)
            self.assertIn('result', self.ai_service.last_action_details)


class TestDirectCommandHandling(unittest.TestCase):
    """Test direct command detection and handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key-for-testing'
        })
        self.env_patcher.start()
        
        self.ai_service = AIService('gpt-4o-mini')
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
        self.env_patcher.stop()
    
    @patch('chat_app.volttron_commands.vctl_status')
    def test_status_command_detection(self, mock_status):
        """Test status command detection."""
        mock_status.return_value = "Agent status output"
        
        test_commands = ['status', 'vctl status', 'agent status', 'check status']
        
        for command in test_commands:
            result = self.ai_service._handle_direct_command(command)
            self.assertEqual(result, "Agent status output")
            
    @patch('chat_app.volttron_commands.start_volttron')
    def test_start_volttron_command_detection(self, mock_start):
        """Test start VOLTTRON command detection."""
        mock_start.return_value = "VOLTTRON started"
        
        test_commands = ['start volttron', 'start platform']
        
        for command in test_commands:
            result = self.ai_service._handle_direct_command(command)
            self.assertEqual(result, "VOLTTRON started")
            
    @patch('chat_app.volttron_commands.vctl_uninstall_agent')
    def test_uninstall_pattern_matching(self, mock_uninstall):
        """Test uninstall command pattern matching."""
        mock_uninstall.return_value = "Agent uninstalled"
        
        test_commands = [
            'uninstall agent123',
            'remove test-id',
            'delete listener',
            'uninstall agent platform.driver',
            'remove agent abc'
        ]
        
        for command in test_commands:
            result = self.ai_service._handle_direct_command(command)
            self.assertEqual(result, "Agent uninstalled")
            
    @patch('chat_app.volttron_commands.verify_agent_uninstalled')
    def test_verification_command_detection(self, mock_verify):
        """Test verification command detection."""
        mock_verify.return_value = "Verification complete"
        
        test_commands = [
            'verify uninstall test-id',
            'check removal of listener',
            'confirm uninstall platform.driver',
            'verify removal abc123'
        ]
        
        for command in test_commands:
            result = self.ai_service._handle_direct_command(command)
            self.assertEqual(result, "Verification complete")
            
    def test_no_command_detected(self):
        """Test when no direct command is detected."""
        result = self.ai_service._handle_direct_command('hello how are you?')
        self.assertIsNone(result)


class TestContextualReversal(unittest.TestCase):
    """Test contextual reversal detection."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key-for-testing'
        })
        self.env_patcher.start()
        
        self.ai_service = AIService('gpt-4o-mini')
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
        self.env_patcher.stop()
    
    def test_reversal_detection_install_agent(self):
        """Test reversal detection for agent installation."""
        # Set up previous action
        self.ai_service.last_action = "install_agent"
        self.ai_service.last_action_details = {"agent_type": "listener"}
        
        is_reversal, response = self.ai_service._detect_context_reversal("I changed my mind")
        
        self.assertTrue(is_reversal)
        self.assertIn("uninstall the listener agent", response)
        self.assertTrue(self.ai_service.awaiting_reversal_confirmation)
        
    def test_reversal_detection_start_volttron(self):
        """Test reversal detection for VOLTTRON start."""
        # Set up previous action
        self.ai_service.last_action = "start_volttron"
        
        is_reversal, response = self.ai_service._detect_context_reversal("nevermind")
        
        self.assertTrue(is_reversal)
        self.assertIn("stop VOLTTRON", response)
        
    def test_reversal_phrases_detection(self):
        """Test various reversal phrases."""
        self.ai_service.last_action = "install_agent"
        self.ai_service.last_action_details = {"agent_type": "test"}
        
        reversal_phrases = [
            "i changed my mind",
            "undo that",
            "reverse it",
            "cancel that",
            "forget it",
            "actually no",
            "i made a mistake"
        ]
        
        for phrase in reversal_phrases:
            is_reversal, response = self.ai_service._detect_context_reversal(phrase)
            self.assertTrue(is_reversal, f"Failed to detect reversal for: {phrase}")
            
    def test_no_reversal_without_previous_action(self):
        """Test that reversal is not detected without previous action."""
        self.ai_service.last_action = None
        
        is_reversal, response = self.ai_service._detect_context_reversal("I changed my mind")
        
        self.assertFalse(is_reversal)
        self.assertEqual(response, "")


class TestConversationHistory(unittest.TestCase):
    """Test conversation history management."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key-for-testing'
        })
        self.env_patcher.start()
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
        self.env_patcher.stop()
    
    def test_conversation_history_loading(self):
        """Test loading conversation history from file."""
        # Create a test conversation file
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
        
    def test_conversation_history_saving(self):
        """Test saving conversation history to file."""
        ai_service = AIService('gpt-4o-mini')
        
        # Add some conversation history
        ai_service.conversation_history = [
            {'role': 'user', 'content': 'test message'},
            {'role': 'assistant', 'content': 'test response'}
        ]
        
        ai_service._save_conversation_history()
        
        # Check that file was created and contains correct data
        self.assertTrue(os.path.exists('conversation_history.json'))
        
        with open('conversation_history.json', 'r') as f:
            saved_data = json.load(f)
            
        self.assertIn('history', saved_data)
        self.assertEqual(len(saved_data['history']), 2)
        
    def test_conversation_history_truncation(self):
        """Test that conversation history is properly truncated."""
        # Create a large conversation history
        large_history = {
            'history': [{'role': 'user', 'content': f'message {i}'} for i in range(50)]
        }
        
        with open('conversation_history.json', 'w') as f:
            json.dump(large_history, f)
            
        ai_service = AIService('gpt-4o-mini')
        
        # Should only load last 20 messages
        self.assertEqual(len(ai_service.conversation_history), 20)
        self.assertEqual(ai_service.conversation_history[0]['content'], 'message 30')
        self.assertEqual(ai_service.conversation_history[-1]['content'], 'message 49')


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key-for-testing'
        })
        self.env_patcher.start()
        
        self.ai_service = AIService('gpt-4o-mini')
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
        self.env_patcher.stop()
    
    def test_invalid_conversation_history_file(self):
        """Test handling of invalid conversation history file."""
        # Create invalid JSON file
        with open('conversation_history.json', 'w') as f:
            f.write('invalid json content')
            
        # Should not crash and should initialize empty history
        ai_service = AIService('gpt-4o-mini')
        self.assertEqual(len(ai_service.conversation_history), 0)
        
    def test_conversation_history_save_error(self):
        """Test handling of conversation history save errors."""
        # Make directory read-only to cause save error
        os.chmod(self.test_dir, 0o444)
        
        try:
            # Should not crash when save fails
            self.ai_service._save_conversation_history()
        except Exception as e:
            self.fail(f"Save error was not handled gracefully: {e}")
        finally:
            # Restore permissions
            os.chmod(self.test_dir, 0o755)
            
    def test_empty_message_handling(self):
        """Test handling of empty messages."""
        result = self.ai_service._handle_direct_command("")
        self.assertIsNone(result)
        
        result = self.ai_service._handle_direct_command("   ")
        self.assertIsNone(result)
        
    def test_case_insensitive_command_detection(self):
        """Test that command detection is case insensitive."""
        with patch('chat_app.volttron_commands.vctl_status') as mock_status:
            mock_status.return_value = "Status output"
            
            test_commands = ['STATUS', 'Status', 'VCTL STATUS', 'VcTl StAtUs']
            
            for command in test_commands:
                result = self.ai_service._handle_direct_command(command)
                self.assertEqual(result, "Status output")


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and workflows."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-api-key-for-testing'
        })
        self.env_patcher.start()
        
        self.ai_service = AIService('gpt-4o-mini')
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
        self.env_patcher.stop()
    
    @patch('chat_app.volttron_commands.vctl_install_listener_agent')
    @patch('chat_app.volttron_commands.vctl_uninstall_agent')
    def test_install_then_reversal_workflow(self, mock_uninstall, mock_install):
        """Test install agent then reversal workflow."""
        mock_install.return_value = "Agent installed"
        mock_uninstall.return_value = "Agent uninstalled"
        
        # Step 1: Install agent
        result1 = self.ai_service.call_function_tool('vctl_install_listener_agent', {})
        self.assertEqual(result1, "Agent installed")
        self.assertEqual(self.ai_service.last_action, "install_agent")
        
        # Step 2: User changes mind
        is_reversal, response = self.ai_service._detect_context_reversal("I changed my mind")
        self.assertTrue(is_reversal)
        self.assertTrue(self.ai_service.awaiting_reversal_confirmation)
        
        # Step 3: User confirms reversal (this would be handled in generate_response)
        # We can test the logic that would be executed
        self.ai_service.awaiting_reversal_confirmation = False
        result2 = self.ai_service.call_function_tool("vctl_uninstall_agent", {"agent_uuid_or_tag": "listener"})
        self.assertEqual(result2, "Agent uninstalled")
        
    def test_multiple_function_tool_calls_tracking(self):
        """Test that multiple function tool calls are tracked correctly."""
        with patch('chat_app.volttron_commands.start_volttron') as mock_start, \
             patch('chat_app.volttron_commands.vctl_install_listener_agent') as mock_install:
            
            mock_start.return_value = "VOLTTRON started"
            mock_install.return_value = "Listener installed"
            
            # Call multiple functions
            self.ai_service.call_function_tool('start_volttron', {})
            self.assertEqual(self.ai_service.last_action, "start_agent")  # start_volttron maps to start_agent
            
            self.ai_service.call_function_tool('vctl_install_listener_agent', {})
            self.assertEqual(self.ai_service.last_action, "install_agent")  # Most recent action
            
    def test_get_model_info(self):
        """Test model information retrieval."""
        # Test with simple model name
        ai_service = AIService('gpt-4o-mini')
        info = ai_service.get_model_info()
        
        self.assertEqual(info['model_name'], 'gpt-4o-mini')
        self.assertEqual(info['model_id'], 'gpt-4o-mini')
        
        # Test with provider prefix
        ai_service2 = AIService('openai:gpt-4o-mini')
        info2 = ai_service2.get_model_info()
        
        self.assertEqual(info2['model_name'], 'openai:gpt-4o-mini')
        self.assertEqual(info2['provider'], 'openai')
        self.assertEqual(info2['model_id'], 'gpt-4o-mini')


def run_tests():
    """Run all tests with detailed output."""
    # Create test suite
    test_classes = [
        TestAIServiceInitialization,
        TestFunctionToolCalling,
        TestDirectCommandHandling,
        TestContextualReversal,
        TestConversationHistory,
        TestErrorHandling,
        TestIntegrationScenarios
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
            
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 VOLTTRON AI Chat Service - Unit Tests")
    print("=" * 60)
    success = run_tests()
    exit(0 if success else 1)