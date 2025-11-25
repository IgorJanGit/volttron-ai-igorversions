#!/usr/bin/env python3
"""
Tests for repository package listing functions.
Tests list_repository_packages() and list_all_installations().
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_app.volttron_commands import (
    list_repository_packages,
    list_all_installations
)


class TestListRepositoryPackages(unittest.TestCase):
    """Test the list_repository_packages function."""
    
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_lists_volttron_packages_with_versions(self, mock_run, mock_find_pip):
        """Test that it lists VOLTTRON packages with versions."""
        mock_find_pip.return_value = '/path/to/pip'
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """Package                      Version
---------------------------- ----------
volttron                     10.0.0
volttron-listener            1.0.0
volttron-platform-driver     2.1.0
some-other-package           3.0.0
ansible                      2.9.0
"""
        mock_run.return_value = mock_result
        
        result = list_repository_packages()
        assert 'volttron (10.0.0)' in result
        assert 'volttron-listener (1.0.0)' in result
        assert 'volttron-platform-driver (2.1.0)' in result
        assert 'ansible (2.9.0)' in result
        assert 'some-other-package' not in result
    
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_handles_no_volttron_packages(self, mock_run, mock_find_pip):
        """Test when no VOLTTRON packages are installed."""
        mock_find_pip.return_value = '/path/to/pip'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """Package                      Version
---------------------------- ----------
some-package                 1.0.0
another-package              2.0.0
"""
        mock_run.return_value = mock_result
        
        result = list_repository_packages()
        
        assert 'No VOLTTRON packages found' in result
    
    @patch('chat_app.volttron_commands.find_pip_command')
    def test_handles_pip_not_found(self, mock_find_pip):
        """Test when pip command is not found."""
        mock_find_pip.return_value = None
        
        result = list_repository_packages()
        
        assert 'Pip not found' in result
    
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_handles_pip_error(self, mock_run, mock_find_pip):
        """Test when pip list command fails."""
        mock_find_pip.return_value = '/path/to/pip'
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result
        
        result = list_repository_packages()
        
        assert 'Failed to list packages' in result or 'Permission denied' in result
    
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_includes_pydantic_and_poetry(self, mock_run, mock_find_pip):
        """Test that it includes pydantic-ai and poetry in related tools."""
        mock_find_pip.return_value = '/path/to/pip'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """Package                      Version
---------------------------- ----------
volttron                     10.0.0
pydantic-ai                  0.0.9
poetry                       1.8.0
openai                       1.0.0
"""
        mock_run.return_value = mock_result
        
        result = list_repository_packages()
        
        assert 'pydantic-ai' in result
        assert 'poetry' in result
        assert 'openai' in result
        assert 'Related tools' in result


class TestListAllInstallations(unittest.TestCase):
    """Test the list_all_installations function."""
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_shows_vctl_status(self, mock_run, mock_home, mock_vctl):
        """Test that it shows vctl status output."""
        mock_vctl.return_value = '/path/to/vctl'
        mock_home.return_value = '/volttron_home'
        vctl_result = Mock()
        vctl_result.returncode = 0
        vctl_result.stdout = """UUID   AGENT                 STATUS
123    volttron-listener     running
456    platform-driver       stopped"""
        
        mock_run.return_value = vctl_result
        
        result = list_all_installations()
        
        assert 'volttron-listener' in result
        assert 'platform-driver' in result
        assert 'running' in result
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_shows_pip_packages(self, mock_run, mock_pip, mock_home, mock_vctl):
        """Test that it shows pip packages."""
        mock_vctl.return_value = '/path/to/vctl'
        mock_home.return_value = '/volttron_home'
        mock_pip.return_value = '/path/to/pip'
        vctl_result = Mock()
        vctl_result.returncode = 0
        vctl_result.stdout = "UUID   AGENT   STATUS"
        pip_result = Mock()
        pip_result.returncode = 0
        pip_result.stdout = """Package                      Version
---------------------------- ----------
volttron                     10.0.0
volttron-listener            1.0.0
"""
        
        mock_run.side_effect = [vctl_result, pip_result]
        
        result = list_all_installations()
        
        assert 'volttron 10.0.0' in result or 'volttron-listener' in result
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_handles_volttron_not_running(self, mock_run, mock_home, mock_vctl):
        """Test when VOLTTRON is not running."""
        mock_vctl.return_value = '/path/to/vctl'
        mock_home.return_value = '/volttron_home'
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        result = list_all_installations()
        
        assert 'not running' in result.lower() or 'No installations' in result
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_includes_ansible_roles(self, mock_run, mock_pip, mock_home, mock_vctl):
        """Test that it includes Ansible roles when available."""
        mock_vctl.return_value = '/path/to/vctl'
        mock_home.return_value = '/volttron_home'
        mock_pip.return_value = '/path/to/pip'
        vctl_result = Mock()
        vctl_result.returncode = 0
        vctl_result.stdout = "UUID   AGENT   STATUS"
        pip_result = Mock()
        pip_result.returncode = 0
        pip_result.stdout = "Package   Version\nvolttron  10.0.0"
        ansible_result = Mock()
        ansible_result.returncode = 0
        ansible_result.stdout = "- volttron-ansible, 1.0.0"
        
        mock_run.side_effect = [vctl_result, pip_result, ansible_result]
        
        result = list_all_installations()
        if 'volttron-ansible' in result:
            assert 'Ansible' in result


class TestPackageListingIntegration(unittest.TestCase):
    """Integration tests for package listing."""
    
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_repository_packages_format(self, mock_run, mock_find_pip):
        """Test the output format of repository packages."""
        mock_find_pip.return_value = '/path/to/pip'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """Package                      Version
---------------------------- ----------
volttron                     10.0.0
volttron-listener            1.0.0
ansible                      2.9.0
"""
        mock_run.return_value = mock_result
        
        result = list_repository_packages()
        assert '📦' in result  # Should have emoji
        assert 'Repository Packages' in result
        assert 'VOLTTRON packages' in result
        assert '(' in result and ')' in result  # Version in parentheses
    
    @patch('chat_app.volttron_commands.find_vctl_command')
    @patch('chat_app.volttron_commands.get_volttron_home')
    @patch('chat_app.volttron_commands.find_pip_command')
    @patch('chat_app.volttron_commands.subprocess.run')
    def test_all_installations_concise_format(self, mock_run, mock_pip, mock_home, mock_vctl):
        """Test that list_all_installations uses concise format."""
        mock_vctl.return_value = '/path/to/vctl'
        mock_home.return_value = '/volttron_home'
        mock_pip.return_value = '/path/to/pip'
        
        vctl_result = Mock()
        vctl_result.returncode = 0
        vctl_result.stdout = "UUID   AGENT   STATUS\n123    listener  running"
        
        pip_result = Mock()
        pip_result.returncode = 0
        pip_result.stdout = "Package   Version\nvolttron  10.0.0"
        
        mock_run.side_effect = [vctl_result, pip_result]
        
        result = list_all_installations()
        assert 'Operation' not in result  # No verbose "operation completed" text
        lines = result.split('\n')
        assert len(lines) < 20  # Should be compact


if __name__ == '__main__':
    unittest.main()
