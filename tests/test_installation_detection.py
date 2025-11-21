#!/usr/bin/env python3
"""
Unit Tests for GitHub Repository Installation Method Detection

This test suite covers:
- Detection of pip installation from README
- Detection of vctl installation from README
- Parsing of package names from installation commands
- Handling of repositories with multiple installation methods
- Error handling for inaccessible repositories

Author: VOLTTRON AI System
Date: November 2025
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_app.volttron_commands import detect_installation_method


class TestInstallationMethodDetection(unittest.TestCase):
    """Test suite for installation method detection functionality."""
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_detect_pip_installation_from_readme(self, mock_get):
        """Test detection of pip installation method from README."""
        mock_contents_response = MagicMock()
        mock_contents_response.status_code = 200
        mock_contents_response.json.return_value = [
            {'name': 'README.md', 'download_url': 'http://example.com/readme'},
            {'name': 'pyproject.toml'}
        ]
        
        mock_readme_response = MagicMock()
        mock_readme_response.status_code = 200
        mock_readme_response.text = """
        # Installation
        
        Install using pip:
        ```
        pip install volttron-test-agent
        ```
        """
        
        mock_get.side_effect = [mock_contents_response, mock_readme_response]
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertEqual(result['method'], 'pip')
        self.assertEqual(result['pypi_package'], 'volttron-test-agent')
        self.assertIn("README mentions 'pip install'", result['details'])
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_detect_vctl_installation_from_readme(self, mock_get):
        """Test detection of vctl installation method from README."""
        mock_contents_response = MagicMock()
        mock_contents_response.status_code = 200
        mock_contents_response.json.return_value = [
            {'name': 'README.md', 'download_url': 'http://example.com/readme'},
            {'name': 'setup.py'}
        ]
        
        mock_readme_response = MagicMock()
        mock_readme_response.status_code = 200
        mock_readme_response.text = """
        # Installation
        
        Install using vctl:
        ```
        vctl install volttron-custom-agent
        ```
        """
        
        mock_get.side_effect = [mock_contents_response, mock_readme_response]
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertTrue(result['vctl_compatible'])
        self.assertIn("README mentions 'vctl install'", result['details'])
        self.assertEqual(result['pypi_package'], 'volttron-custom-agent')
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_detect_both_installation_methods(self, mock_get):
        """Test detection when both pip and vctl methods are available."""
        mock_contents_response = MagicMock()
        mock_contents_response.status_code = 200
        mock_contents_response.json.return_value = [
            {'name': 'README.md', 'download_url': 'http://example.com/readme'},
            {'name': 'setup.py'}
        ]
        
        mock_readme_response = MagicMock()
        mock_readme_response.status_code = 200
        mock_readme_response.text = """
        # Installation
        
        ## Option 1: pip
        ```
        pip install volttron-dual-agent
        ```
        
        ## Option 2: vctl
        ```
        vctl install volttron-dual-agent
        ```
        """
        
        mock_get.side_effect = [mock_contents_response, mock_readme_response]
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertEqual(result['pypi_package'], 'volttron-dual-agent')
        self.assertTrue(result['vctl_compatible'])
        self.assertTrue(result['setup_py'])
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_detect_historian_package_pattern(self, mock_get):
        """Test detection of historian package naming pattern."""
        mock_contents_response = MagicMock()
        mock_contents_response.status_code = 200
        mock_contents_response.json.return_value = [
            {'name': 'README.md', 'download_url': 'http://example.com/readme'}
        ]
        
        mock_readme_response = MagicMock()
        mock_readme_response.status_code = 200
        mock_readme_response.text = """
        Install the historian:
        pip install custom-historian
        """
        
        mock_get.side_effect = [mock_contents_response, mock_readme_response]
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertEqual(result['pypi_package'], 'custom-historian')
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_detect_pyproject_toml(self, mock_get):
        """Test detection of pyproject.toml file."""
        mock_contents_response = MagicMock()
        mock_contents_response.status_code = 200
        mock_contents_response.json.return_value = [
            {'name': 'pyproject.toml'}
        ]
        
        mock_get.return_value = mock_contents_response
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertTrue(result['pyproject_toml'])
        self.assertIn('Found pyproject.toml', result['details'])
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_detect_setup_py(self, mock_get):
        """Test detection of setup.py file."""
        mock_contents_response = MagicMock()
        mock_contents_response.status_code = 200
        mock_contents_response.json.return_value = [
            {'name': 'setup.py'}
        ]
        
        mock_get.return_value = mock_contents_response
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertTrue(result['setup_py'])
        self.assertIn('Found setup.py', result['details'])
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_handle_repo_access_error(self, mock_get):
        """Test handling of repository access errors."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = detect_installation_method('test-owner', 'nonexistent-repo')
        
        self.assertEqual(result['method'], 'unknown')
        self.assertIn('Could not fetch repo contents', result['details'][0])
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_handle_readme_fetch_error(self, mock_get):
        """Test handling of README fetch errors."""
        mock_contents_response = MagicMock()
        mock_contents_response.status_code = 200
        mock_contents_response.json.return_value = [
            {'name': 'README.md', 'download_url': 'http://example.com/readme'}
        ]
        
        mock_readme_response = MagicMock()
        mock_readme_response.status_code = 404
        
        mock_get.side_effect = [mock_contents_response, mock_readme_response]
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertEqual(result['method'], 'unknown')
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_no_installation_info_available(self, mock_get):
        """Test when no installation information is available."""
        mock_contents_response = MagicMock()
        mock_contents_response.status_code = 200
        mock_contents_response.json.return_value = [
            {'name': 'some_file.txt'}
        ]
        
        mock_get.return_value = mock_contents_response
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertEqual(result['method'], 'unknown')
        self.assertFalse(result['setup_py'])
        self.assertFalse(result['pyproject_toml'])
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_exception_handling(self, mock_get):
        """Test exception handling during detection."""
        mock_get.side_effect = Exception("Network error")
        
        result = detect_installation_method('test-owner', 'test-repo')
        
        self.assertEqual(result['method'], 'unknown')
        self.assertIn('Error detecting method', result['details'][0])


class TestInstallationMethodIntegration(unittest.TestCase):
    """Integration tests for installation method detection with search."""
    
    @patch('chat_app.volttron_commands.detect_installation_method')
    @patch('chat_app.volttron_commands.requests.get')
    def test_search_includes_installation_method(self, mock_get, mock_detect):
        """Test that search results include installation method."""
        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = [
            {
                'name': 'volttron-test-agent',
                'html_url': 'https://github.com/test/volttron-test-agent',
                'clone_url': 'https://github.com/test/volttron-test-agent.git',
                'description': 'Test agent',
                'updated_at': '2025-01-01T00:00:00Z',
                'stargazers_count': 5
            }
        ]
        mock_get.return_value = mock_search_response
        
        mock_detect.return_value = {
            'method': 'pip',
            'pypi_package': 'volttron-test-agent',
            'vctl_compatible': False,
            'setup_py': True,
            'pyproject_toml': False,
            'details': ['Found setup.py', 'PyPI package name: volttron-test-agent']
        }
        
        from chat_app.volttron_commands import search_github_for_agent
        result = search_github_for_agent('test-agent')
        
        self.assertIn('Installation method: pip', result)
        self.assertIn('pip install volttron-test-agent', result)


if __name__ == '__main__':
    unittest.main()
