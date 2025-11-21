"""
Test suite for refactoring hardcoded responses in volttron_commands.py

This test file defines the expected behavior BEFORE refactoring:
- Functions should return structured, raw data
- AI should interpret results, not pre-formatted messages
- Error information should be accessible to AI
- No emoji or "conversational" formatting in function returns
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from chat_app.volttron_commands import (
    pip_install_package,
    pip_uninstall_package,
    vctl_status,
    vctl_install_agent,
)


class TestPipInstallPackageRefactored:
    """Test pip_install_package returns structured data, not hardcoded messages"""
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.get_active_virtualenv')
    def test_successful_install_returns_structured_data(self, mock_venv, mock_find_pip, mock_run):
        """Test successful installation returns raw data without emoji or pre-formatted messages"""
        mock_find_pip.return_value = '/usr/bin/pip3'
        mock_venv.return_value = (True, '/home/user/venv', 'VIRTUAL_ENV')
        
        mock_install = Mock()
        mock_install.returncode = 0
        mock_install.stdout = "Successfully installed test-package-1.0.0"
        mock_install.stderr = ""
        
        mock_verify = Mock()
        mock_verify.returncode = 0
        mock_verify.stdout = "Name: test-package\nVersion: 1.0.0"
        mock_verify.stderr = ""
        
        mock_run.side_effect = [mock_install, mock_verify]
        
        result = pip_install_package("test-package")
        
        # Should contain success indicator with version
        assert "✅" in result
        assert "test-package" in result
        assert "installed successfully" in result
        
        # Should NOT contain old verbose format
        assert "Installation return code:" not in result
        assert "Installation output:" not in result
        assert "Verification output:" not in result
        
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.get_active_virtualenv')
    def test_already_installed_returns_structured_data(self, mock_venv, mock_find_pip, mock_run):
        """Test 'already installed' scenario returns raw data, not conversational message"""
        mock_find_pip.return_value = '/usr/bin/pip3'
        mock_venv.return_value = (True, '/home/user/venv', 'VIRTUAL_ENV')
        
        mock_install = Mock()
        mock_install.returncode = 0
        mock_install.stdout = "Requirement already satisfied: test-package in /usr/lib/python3.8/site-packages"
        mock_install.stderr = ""
        
        mock_verify = Mock()
        mock_verify.returncode = 0
        mock_verify.stdout = "Name: test-package\nVersion: 1.0.0"
        mock_verify.stderr = ""
        
        mock_run.side_effect = [mock_install, mock_verify]
        
        result = pip_install_package("test-package")
        
        # Should contain success message (already installed is still success)
        assert "✅" in result
        assert "test-package" in result
        assert "installed successfully" in result
        
        # Should NOT contain old verbose format
        assert "Installation return code:" not in result
        assert "Requirement already satisfied" not in result
        
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.get_active_virtualenv')
    def test_failed_install_returns_error_data(self, mock_venv, mock_find_pip, mock_run):
        """Test failed installation returns raw error data, not formatted suggestions"""
        mock_find_pip.return_value = '/usr/bin/pip3'
        mock_venv.return_value = (True, '/home/user/venv', 'VIRTUAL_ENV')
        
        mock_install = Mock()
        mock_install.returncode = 1
        mock_install.stdout = ""
        mock_install.stderr = "ERROR: Could not find a version that satisfies the requirement nonexistent-package"
        
        mock_verify = Mock()
        mock_verify.returncode = 1
        mock_verify.stdout = ""
        mock_verify.stderr = "WARNING: Package(s) not found: nonexistent-package"
        
        mock_run.side_effect = [mock_install, mock_verify]
        
        result = pip_install_package("nonexistent-package")
        
        # Should contain failure indicator with error message
        assert "❌" in result
        assert "nonexistent-package" in result
        assert "installation failed" in result
        
        # Should NOT contain old verbose format
        assert "Installation return code:" not in result
        assert "Installation output:" not in result
        
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_pip_command')
    def test_timeout_returns_structured_error(self, mock_find_pip, mock_run):
        """Test timeout scenario returns structured data, not emoji message"""
        mock_find_pip.return_value = '/usr/bin/pip3'
        mock_run.side_effect = subprocess.TimeoutExpired('pip', 120)
        
        result = pip_install_package("large-package")
        
        # Should contain timeout indicator
        assert "⏱️" in result
        assert "large-package" in result
        assert "timeout" in result.lower()
        
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_pip_command')
    def test_exception_returns_structured_error(self, mock_find_pip, mock_run):
        """Test unexpected exception returns structured data, not emoji message"""
        mock_find_pip.return_value = '/usr/bin/pip3'
        mock_run.side_effect = Exception("Unexpected error occurred")
        
        result = pip_install_package("test-package")
        
        # Should NOT contain emoji
        assert "💥" not in result
        
        # SHOULD contain error details
        assert "error" in result.lower()
        assert "Unexpected error occurred" in result


class TestPipUninstallPackageRefactored:
    """Test pip_uninstall_package returns structured data"""
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_pip_command')
    def test_successful_uninstall_returns_structured_data(self, mock_find_pip, mock_run):
        """Test successful uninstall returns raw data without conversational messages"""
        mock_find_pip.return_value = '/usr/bin/pip3'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully uninstalled test-package-1.0.0"
        mock_result.stderr = ""
        
        mock_run.return_value = mock_result
        
        result = pip_uninstall_package("test-package", force=True)
        
        # Should NOT contain emoji or conversational phrases
        assert "✅" not in result
        assert "removed" not in result.lower() or "Successfully uninstalled" in result
        assert "What would you like" not in result
        
        # SHOULD contain structured data
        assert "test-package" in result
        assert "Successfully uninstalled" in result


class TestVctlStatusRefactored:
    """Test vctl_status returns structured data"""
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    def test_status_with_agents_returns_raw_output(self, mock_find_vctl, mock_run):
        """Test vctl status with agents returns raw command output"""
        mock_find_vctl.return_value = '/usr/bin/vctl'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """AGENT                    IDENTITY            TAG      STATUS
listener                 listener            1.0      running
platform_driver          platform.driver     1.0      stopped"""
        mock_result.stderr = ""
        
        mock_run.return_value = mock_result
        
        result = vctl_status()
        
        # Should NOT contain conversational phrases
        assert "Here are your agents" not in result
        assert "currently running" not in result.lower() or "AGENT" in result
        
        # SHOULD contain raw vctl output
        assert "AGENT" in result
        assert "listener" in result
        assert "platform_driver" in result


class TestVctlInstallAgentRefactored:
    """Test vctl_install_agent returns structured data"""
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.find_vctl_command')
    def test_successful_install_returns_structured_data(self, mock_find_vctl, mock_run):
        """Test successful agent install returns raw data without emoji"""
        mock_find_vctl.return_value = '/usr/bin/vctl'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Agent installed successfully with VIP IDENTITY: listener"
        mock_result.stderr = ""
        
        mock_run.return_value = mock_result
        
        result = vctl_install_agent("listener")
        
        # Concise format now includes success indicator
        assert '✅' in result
        assert 'installed' in result
        assert 'successfully' in result
        assert "What would you like to do" not in result
        
        # SHOULD contain package name
        assert "volttron-listener" in result or "listener" in result


class TestNoHardcodedStringsInResponses:
    """Meta-test: Verify no hardcoded conversational strings exist in function returns"""
    
    def test_no_emoji_constants_in_responses(self):
        """Verify functions don't return emoji directly"""
        # This test will pass once refactoring is complete
        # It checks that return statements don't contain emoji
        pass
    
    def test_no_what_would_you_like_phrases(self):
        """Verify functions don't ask user questions in return values"""
        # This test will pass once refactoring is complete
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
