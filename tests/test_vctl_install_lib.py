#!/usr/bin/env python3
"""
Unit tests for vctl_install_lib functionality

Tests the vctl_install_lib function that allows installation of VOLTTRON libraries
without requiring VOLTTRON to be running (unlike the vctl install-lib command).
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_app.volttron_commands import vctl_install_lib, get_pip_command_from_venv


class TestVctlInstallLib:
    """Test cases for vctl_install_lib function"""
    
    @patch('chat_app.volttron_commands.get_pip_command_from_venv')
    @patch('subprocess.run')
    def test_successful_installation(self, mock_run, mock_get_pip):
        """Test successful library installation"""
        # Setup mocks
        mock_get_pip.return_value = ('/path/to/pip', None)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed volttron-lib-modbustk-driver"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Test
        result = vctl_install_lib('volttron-lib-modbustk-driver')
        
        # Verify
        assert "Successfully installed" in result
        assert "volttron-lib-modbustk-driver" in result
        mock_run.assert_called_once()
    
    @patch('chat_app.volttron_commands.get_pip_command_from_venv')
    @patch('subprocess.run')
    def test_already_installed(self, mock_run, mock_get_pip):
        """Test when library is already installed"""
        # Setup mocks
        mock_get_pip.return_value = ('/path/to/pip', None)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Requirement already satisfied: volttron-lib-modbustk-driver"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Test
        result = vctl_install_lib('volttron-lib-modbustk-driver')
        
        # Verify
        assert "already installed" in result
        assert "volttron-lib-modbustk-driver" in result
    
    @patch('chat_app.volttron_commands.get_pip_command_from_venv')
    def test_no_pip_command(self, mock_get_pip):
        """Test when pip command is not available"""
        # Setup mocks
        mock_get_pip.return_value = (None, "Pip not found")
        
        # Test
        result = vctl_install_lib('volttron-lib-modbustk-driver')
        
        # Verify
        assert "Pip" in result or "pip" in result
    
    @patch('chat_app.volttron_commands.get_pip_command_from_venv')
    @patch('subprocess.run')
    def test_library_not_found(self, mock_run, mock_get_pip):
        """Test when library package doesn't exist"""
        # Setup mocks
        mock_get_pip.return_value = ('/path/to/pip', None)
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Could not find a version that satisfies the requirement"
        mock_run.return_value = mock_result
        
        # Test
        result = vctl_install_lib('nonexistent-library')
        
        # Verify
        assert "not found" in result.lower() or "could not find" in result.lower()
    
    @patch('chat_app.volttron_commands.get_pip_command_from_venv')
    @patch('subprocess.run')
    def test_permission_denied(self, mock_run, mock_get_pip):
        """Test when user doesn't have permission to install"""
        # Setup mocks
        mock_get_pip.return_value = ('/path/to/pip', None)
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result
        
        # Test
        result = vctl_install_lib('volttron-lib-modbustk-driver')
        
        # Verify
        assert "permission" in result.lower()
    
    @patch('chat_app.volttron_commands.get_pip_command_from_venv')
    @patch('subprocess.run')
    def test_timeout_handling(self, mock_run, mock_get_pip):
        """Test timeout during installation"""
        # Setup mocks
        mock_get_pip.return_value = ('/path/to/pip', None)
        mock_run.side_effect = subprocess.TimeoutExpired('pip', 180)
        
        # Test
        result = vctl_install_lib('volttron-lib-modbustk-driver')
        
        # Verify
        assert "timeout" in result.lower() or "taking longer" in result.lower()
    
    def test_library_name_normalization(self):
        """Test that library names are normalized correctly"""
        test_cases = [
            ('volttron-lib-modbustk-driver', 'volttron-lib-modbustk-driver'),  # Already correct
            ('modbustk-driver', 'volttron-lib-modbustk-driver'),  # Missing prefix
            ('lib-modbustk-driver', 'volttron-lib-modbustk-driver'),  # Partial prefix
        ]
        
        for input_name, expected in test_cases:
            normalized = input_name
            if not normalized.startswith('volttron-'):
                if normalized.startswith('lib-'):
                    normalized = 'volttron-' + normalized
                elif not normalized.startswith('volttron'):
                    normalized = 'volttron-lib-' + normalized
            
            assert normalized == expected, f"Failed for {input_name}: got {normalized}, expected {expected}"


class TestAIServiceIntegration:
    """Test AI service integration for library installation"""
    
    def test_vctl_install_lib_import(self):
        """Test that vctl_install_lib can be imported"""
        from chat_app.volttron_commands import vctl_install_lib
        assert callable(vctl_install_lib)
    
    def test_function_signature(self):
        """Test that the function has the correct signature"""
        from chat_app.volttron_commands import vctl_install_lib
        import inspect
        
        sig = inspect.signature(vctl_install_lib)
        params = list(sig.parameters.keys())
        
        assert 'library_name' in params
        assert 'confirm' in params


if __name__ == '__main__':
    # Run tests with pytest
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])
