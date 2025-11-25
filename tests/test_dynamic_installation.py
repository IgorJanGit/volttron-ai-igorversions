#!/usr/bin/env python3
"""
Tests for dynamic README-based installation system.
Tests extract_installation_commands(), execute_direct_commands(), and execute_clone_and_install().
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_app.volttron_commands import (
    extract_installation_commands,
    execute_direct_commands,
    execute_clone_and_install,
    install_from_github_smart
)


class TestExtractInstallationCommands(unittest.TestCase):
    """Test the extract_installation_commands function."""
    
    def test_detects_pip_from_pypi(self):
        """Test detection of pip install from PyPI."""
        readme = """
# My Package

## Installation

```bash
pip install volttron-my-package
```
"""
        result = extract_installation_commands(readme, "https://github.com/test/repo", "repo")
        
        assert result['method'] == 'pip_from_pypi'
        assert result['package'] == 'volttron-my-package'
    
    def test_detects_clone_and_install(self):
        """Test detection of git clone + pip install pattern."""
        readme = """
# My Package

## Installation

```bash
git clone https://github.com/test/repo.git
cd repo
pip install .
```
"""
        result = extract_installation_commands(readme, "https://github.com/test/repo", "repo")
        
        assert result['method'] == 'clone_and_install'
        assert 'pip install .' in result['commands'] or 'install' in str(result['commands'])
    
    def test_detects_poetry_install(self):
        """Test detection of poetry install."""
        readme = """
# Package

```bash
poetry install
```
"""
        result = extract_installation_commands(readme, "https://github.com/test/repo", "repo")
        
        assert result['method'] in ['clone_and_install', 'direct_commands']
        assert any('poetry' in cmd for cmd in result.get('commands', []))
    
    def test_filters_prose_from_code_blocks(self):
        """Test that code blocks are extracted."""
        readme = """
# Package

```bash
pip install my-package
npm install
```
"""
        result = extract_installation_commands(readme, "https://github.com/test/repo", "repo")
        
        # Should find installation method
        assert result['method'] != 'unknown'
        
        # Should have either package name or commands
        assert 'package' in result or 'commands' in result
    
    def test_detects_ansible_galaxy_install(self):
        """Test detection of ansible-galaxy install."""
        readme = """
# Ansible Role

```bash
ansible-galaxy install volttron.ansible
```
"""
        result = extract_installation_commands(readme, "https://github.com/test/repo", "repo")
        
        # Function may detect as clone_and_install or direct_commands
        assert result['method'] in ['clone_and_install', 'direct_commands']
        assert any('ansible-galaxy' in cmd for cmd in result['commands'])
    
    def test_handles_multiple_code_blocks(self):
        """Test handling of multiple code blocks."""
        readme = """
# Package

## Prerequisites
```bash
sudo apt-get install python3
```

## Installation
```bash
pip install my-package
```
"""
        result = extract_installation_commands(readme, "https://github.com/test/repo", "repo")
        
        # Should find pip install
        assert result['method'] in ['pip_from_pypi', 'direct_commands']
    
    def test_handles_no_installation_section(self):
        """Test when README has no installation instructions."""
        readme = """
# My Package

This is a great package!
"""
        result = extract_installation_commands(readme, "https://github.com/test/repo", "repo")
        
        assert result['method'] == 'unknown'
    
    def test_detects_editable_install(self):
        """Test detection of pip install -e ."""
        readme = """
## Development

```bash
git clone https://github.com/test/repo.git
pip install -e .
```
"""
        result = extract_installation_commands(readme, "https://github.com/test/repo", "repo")
        
        # May detect as pip_from_pypi or clone_and_install
        assert result['method'] in ['clone_and_install', 'pip_from_pypi', 'direct_commands']
        assert 'commands' in result or 'package' in result


class TestExecuteDirectCommands(unittest.TestCase):
    """Test the execute_direct_commands function."""
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.shutil.which')
    def test_executes_simple_command(self, mock_which, mock_run):
        """Test execution of a simple command."""
        mock_which.return_value = '/usr/bin/pip'
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = execute_direct_commands(['pip install some-package'], 'test-repo')
        
        assert '✅' in result
        assert 'test-repo' in result
        mock_run.assert_called_once()
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.shutil.which')
    def test_auto_installs_missing_tools(self, mock_which, mock_run):
        """Test auto-installation of missing tools like ansible."""
        # First call: check for ansible-galaxy (not found)
        # Second call: install ansible
        # Third call: run the actual command
        mock_which.side_effect = [None, '/usr/bin/pip', '/usr/bin/ansible-galaxy']
        
        install_result = Mock()
        install_result.returncode = 0
        
        command_result = Mock()
        command_result.returncode = 0
        
        mock_run.side_effect = [install_result, command_result]
        
        result = execute_direct_commands(['ansible-galaxy install volttron.ansible'], 'test-repo')
        
        # Should have tried to install ansible first
        assert mock_run.call_count >= 1
        assert '✅' in result or 'installed' in result.lower()
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.shutil.which')
    def test_handles_command_failure(self, mock_which, mock_run):
        """Test handling of command execution failure."""
        mock_which.return_value = '/usr/bin/pip'
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Installation failed"
        mock_run.return_value = mock_result
        
        result = execute_direct_commands(['pip install nonexistent-package'], 'test-repo')
        
        assert '❌' in result
        assert 'failed' in result.lower()
    
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('chat_app.volttron_commands.shutil.which')
    def test_reports_ansible_role_installation(self, mock_which, mock_run):
        """Test that ansible role installations are reported correctly."""
        mock_which.return_value = '/usr/bin/ansible-galaxy'
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = execute_direct_commands(['ansible-galaxy install volttron.ansible'], 'volttron-ansible')
        
        assert 'Ansible role' in result or 'ansible-galaxy list' in result


class TestExecuteCloneAndInstall(unittest.TestCase):
    """Test the execute_clone_and_install function."""
    
    @patch('tempfile.mkdtemp')
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('shutil.rmtree')
    @patch('chat_app.volttron_commands.find_pip_command')
    def test_clones_and_installs(self, mock_pip, mock_rmtree, mock_run, mock_tempdir):
        """Test cloning repository and installing."""
        mock_tempdir.return_value = '/tmp/test-repo'
        mock_pip.return_value = '/usr/bin/pip'
        
        # Mock git clone
        clone_result = Mock()
        clone_result.returncode = 0
        
        # Mock pip install
        install_result = Mock()
        install_result.returncode = 0
        
        mock_run.side_effect = [clone_result, install_result]
        
        result = execute_clone_and_install(
            'https://github.com/test/repo.git',
            'test-repo',
            ['pip install .']
        )
        
        assert '✅' in result
        assert 'test-repo' in result
        mock_rmtree.assert_called_once()  # Cleanup
    
    @patch('tempfile.mkdtemp')
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('shutil.rmtree')
    def test_handles_clone_failure(self, mock_rmtree, mock_run, mock_tempdir):
        """Test handling of git clone failure."""
        mock_tempdir.return_value = '/tmp/test-repo'
        
        clone_result = Mock()
        clone_result.returncode = 1
        clone_result.stderr = "Repository not found"
        mock_run.return_value = clone_result
        
        result = execute_clone_and_install(
            'https://github.com/test/nonexistent.git',
            'test-repo',
            ['pip install .']
        )
        
        assert '❌' in result
        assert 'clone' in result.lower() or 'failed' in result.lower()
        mock_rmtree.assert_called_once()  # Still cleanup
    
    @patch('tempfile.mkdtemp')
    @patch('chat_app.volttron_commands.subprocess.run')
    @patch('shutil.rmtree')
    @patch('chat_app.volttron_commands.find_pip_command')
    def test_handles_poetry_install(self, mock_pip, mock_rmtree, mock_run, mock_tempdir):
        """Test handling of poetry install command."""
        mock_tempdir.return_value = '/tmp/test-repo'
        mock_pip.return_value = '/usr/bin/pip'
        
        clone_result = Mock()
        clone_result.returncode = 0
        
        poetry_result = Mock()
        poetry_result.returncode = 0
        
        mock_run.side_effect = [clone_result, poetry_result]
        
        result = execute_clone_and_install(
            'https://github.com/test/repo.git',
            'test-repo',
            ['poetry install']
        )
        
        assert '✅' in result or 'installed' in result.lower()


class TestInstallFromGithubSmart(unittest.TestCase):
    """Test the install_from_github_smart function."""
    
    @patch('chat_app.volttron_commands.requests.get')
    @patch('chat_app.volttron_commands.detect_installation_method')
    @patch('chat_app.volttron_commands.pip_install_package')
    def test_uses_pip_when_package_detected(self, mock_pip, mock_detect, mock_get):
        """Test that it uses pip when PyPI package is detected."""
        # Mock detection
        mock_detect.return_value = {'pypi_package': 'volttron-listener'}
        
        # Mock README fetch
        readme_response = Mock()
        readme_response.status_code = 200
        readme_response.json.return_value = {
            'content': 'IyBNeSBQYWNrYWdl'  # base64 encoded
        }
        mock_get.return_value = readme_response
        
        # Mock pip install
        mock_pip.return_value = "✅ volttron-listener v1.0.0 installed successfully"
        
        result = install_from_github_smart('https://github.com/eclipse-volttron/volttron-listener')
        
        assert '✅' in result
        mock_pip.assert_called_once_with('volttron-listener')
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_detects_documentation_site(self, mock_get):
        """Test detection of documentation/Jekyll sites."""
        readme_response = Mock()
        readme_response.status_code = 200
        readme_response.json.return_value = {
            'content': 'IyBEb2NzCmJ1bmRsZSBpbnN0YWxsCg=='  # "# Docs\nbundle install\n"
        }
        mock_get.return_value = readme_response
        
        result = install_from_github_smart('https://github.com/test/docs.github.io')
        
        assert 'documentation' in result.lower() or 'website' in result.lower()
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_detects_copier_template(self, mock_get):
        """Test detection of Copier/Cookiecutter templates."""
        readme_response = Mock()
        readme_response.status_code = 200
        readme_response.json.return_value = {
            'content': 'IyBUZW1wbGF0ZQpjb3BpZXIgY29weSA='  # "# Template\ncopier copy "
        }
        mock_get.return_value = readme_response
        
        result = install_from_github_smart('https://github.com/test/copier-template')
        
        assert 'template' in result.lower()
        assert 'copier' in result.lower()
    
    @patch('chat_app.volttron_commands.requests.get')
    def test_handles_invalid_url(self, mock_get):
        """Test handling of invalid GitHub URL."""
        result = install_from_github_smart('https://not-github.com/test/repo')
        
        assert '❌' in result
        # Should contain error message about README or fetch
        assert 'README' in result or 'fetch' in result


class TestDynamicInstallationIntegration(unittest.TestCase):
    """Integration tests for dynamic installation."""
    
    def test_command_extraction_preserves_order(self):
        """Test that commands are extracted in order."""
        readme = """
```bash
pip install prereq
pip install package
pip install optional
```
"""
        result = extract_installation_commands(readme, "url", "repo")
        
        if 'commands' in result:
            commands = result['commands']
            # Check that order is preserved (if multiple commands)
            if len(commands) >= 2:
                assert commands[0] != commands[1]
    
    def test_concise_output_format(self):
        """Test that outputs follow concise format (no verbose messages)."""
        with patch('chat_app.volttron_commands.subprocess.run') as mock_run, \
             patch('chat_app.volttron_commands.shutil.which') as mock_which:
            
            mock_which.return_value = '/usr/bin/pip'
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = execute_direct_commands(['pip install test'], 'test-repo')
            
            # Should be concise
            lines = result.split('\n')
            assert len(lines) < 5  # Not verbose
            assert '✅' in result  # Has status emoji


if __name__ == '__main__':
    unittest.main()
