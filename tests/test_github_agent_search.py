"""Tests for GitHub agent search and installation functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chat_app.volttron_commands import search_github_for_agent, install_agent_from_github


class TestSearchGitHubForAgent:
    """Test the search_github_for_agent function."""
    
    def test_successful_single_match(self):
        """Test finding a single matching repository."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'volttron-listener',
                'html_url': 'https://github.com/eclipse-volttron/volttron-listener',
                'clone_url': 'https://github.com/eclipse-volttron/volttron-listener.git',
                'description': 'VOLTTRON listener agent',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 5
            }
        ]
        
        mock_detect = {
            'method': 'pip',
            'pypi_package': 'volttron-listener',
            'vctl_compatible': True,
            'setup_py': True,
            'pyproject_toml': False,
            'details': ['Found setup.py', 'README mentions pip install']
        }
        
        with patch('requests.get', return_value=mock_response), \
             patch('chat_app.volttron_commands.detect_installation_method', return_value=mock_detect):
            result = search_github_for_agent('listener')
        
        assert 'Status: Match found' in result
        assert 'volttron-listener' in result
        assert 'https://github.com/eclipse-volttron/volttron-listener' in result
        assert 'Do you want to install this agent?' in result
        assert 'yes/no' in result
        # Verify pagination info is included
        assert 'Pages scanned:' in result
        assert 'Repositories scanned:' in result
        # Verify installation method is included
        assert 'Installation method:' in result
        # Verify no hardcoded emoji or marketing language
        assert '🎉' not in result
        assert '✨' not in result
    
    def test_successful_multiple_matches(self):
        """Test finding multiple matching repositories."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'volttron-bacnet-proxy',
                'html_url': 'https://github.com/eclipse-volttron/volttron-bacnet-proxy',
                'clone_url': 'https://github.com/eclipse-volttron/volttron-bacnet-proxy.git',
                'description': 'BACnet proxy agent',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 3
            },
            {
                'name': 'volttron-lib-bacnet-driver',
                'html_url': 'https://github.com/eclipse-volttron/volttron-lib-bacnet-driver',
                'clone_url': 'https://github.com/eclipse-volttron/volttron-lib-bacnet-driver.git',
                'description': 'BACnet driver library',
                'updated_at': '2025-10-15T12:00:00Z',
                'stargazers_count': 2
            }
        ]
        
        with patch('requests.get', return_value=mock_response):
            result = search_github_for_agent('bacnet')
        
        assert 'Status: Multiple matches found' in result
        assert 'Matches found: 2' in result
        assert 'volttron-bacnet-proxy' in result
        assert 'volttron-lib-bacnet-driver' in result
        assert 'Question: Which one do you want?' in result
        assert 'enter number 1-2' in result
        # Verify pagination info is included
        assert 'Pages scanned:' in result
        assert 'Repositories scanned:' in result
        # Verify no hardcoded emoji
        assert '🎉' not in result
        assert '✨' not in result
    
    def test_no_matches_found(self):
        """Test when no matching repositories are found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'some-other-repo',
                'html_url': 'https://github.com/eclipse-volttron/some-other-repo',
                'clone_url': 'https://github.com/eclipse-volttron/some-other-repo.git',
                'description': 'Other repository',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            }
        ]
        
        with patch('requests.get', return_value=mock_response):
            result = search_github_for_agent('nonexistent')
        
        assert 'Status: No matches found' in result
        assert 'Matches found: 0' in result
        assert 'nonexistent' in result
        assert 'Suggestion:' in result
        # Verify structured data response
        assert 'Repositories scanned:' in result
    
    def test_api_request_failed(self):
        """Test handling of GitHub API request failure."""
        mock_response = Mock()
        mock_response.status_code = 403
        
        with patch('requests.get', return_value=mock_response):
            result = search_github_for_agent('listener')
        
        assert 'Status: API request failed' in result
        assert 'Status code: 403' in result
        assert 'Agent searched: listener' in result
        # Verify no hardcoded suggestions
        assert 'try again' not in result.lower() or 'Error:' in result
    
    def test_network_timeout(self):
        """Test handling of network timeout."""
        with patch('requests.get', side_effect=Exception('Timeout')):
            result = search_github_for_agent('listener')
        
        assert 'Status: Error' in result or 'Status: Timeout' in result
        assert 'listener' in result
        # Verify structured error response
        assert 'Error' in result
    
    def test_returns_structured_data_not_emoji(self):
        """Test that response is structured data without hardcoded emoji."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'test-agent',
                'html_url': 'https://github.com/eclipse-volttron/test-agent',
                'clone_url': 'https://github.com/eclipse-volttron/test-agent.git',
                'description': 'Test agent',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            }
        ]
        
        with patch('requests.get', return_value=mock_response):
            result = search_github_for_agent('test')
        
        # Check for structured data format
        assert 'GitHub agent search completed.' in result
        assert 'Status:' in result
        assert 'Agent searched:' in result
        assert 'Pages scanned:' in result
        assert 'Repositories scanned:' in result
        
        # Verify NO hardcoded emoji or marketing language
        emoji_list = ['🎉', '✨', '🚀', '💡', '🔥', '⚡', '✅', '❌']
        for emoji in emoji_list:
            if emoji in result:
                # Only ✅ and ❌ are acceptable as status indicators in structured data
                if emoji not in ['✅', '❌']:
                    assert False, f"Found hardcoded emoji: {emoji}"
    
    def test_pagination_multiple_pages(self):
        """Test that pagination works across multiple pages of results."""
        # Mock responses for multiple pages
        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = [
            {
                'name': f'agent-{i}',
                'html_url': f'https://github.com/eclipse-volttron/agent-{i}',
                'clone_url': f'https://github.com/eclipse-volttron/agent-{i}.git',
                'description': f'Agent {i}',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            } for i in range(100)
        ]
        
        page2_response = Mock()
        page2_response.status_code = 200
        page2_response.json.return_value = [
            {
                'name': f'test-agent-{i}',
                'html_url': f'https://github.com/eclipse-volttron/test-agent-{i}',
                'clone_url': f'https://github.com/eclipse-volttron/test-agent-{i}.git',
                'description': f'Test Agent {i}',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            } for i in range(50)
        ]
        
        # Create a side effect that returns different responses for different calls
        mock_get = Mock()
        mock_get.side_effect = [page1_response, page2_response]
        
        with patch('requests.get', mock_get):
            result = search_github_for_agent('agent')
        
        # Verify it scanned multiple pages
        assert 'Pages scanned: 2' in result
        assert 'Repositories scanned: 150' in result
        # Verify it found matches from both pages
        assert 'Status: Multiple matches found' in result
        assert 'Matches found: 150' in result
    
    def test_pagination_stops_on_empty_page(self):
        """Test that pagination stops when encountering an empty page."""
        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = [
            {
                'name': 'test-agent-1',
                'html_url': 'https://github.com/eclipse-volttron/test-agent-1',
                'clone_url': 'https://github.com/eclipse-volttron/test-agent-1.git',
                'description': 'Test Agent 1',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            }
        ]
        
        page2_response = Mock()
        page2_response.status_code = 200
        page2_response.json.return_value = []  # Empty page
        
        mock_get = Mock()
        mock_get.side_effect = [page1_response, page2_response]
        
        with patch('requests.get', mock_get):
            result = search_github_for_agent('test')
        
        # Should stop after page 1 since page 2 is empty
        assert 'Pages scanned: 1' in result
        assert 'Repositories scanned: 1' in result
    
    def test_pagination_handles_partial_last_page(self):
        """Test pagination correctly handles last page with fewer than 100 repos."""
        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = [
            {
                'name': f'repo-{i}',
                'html_url': f'https://github.com/eclipse-volttron/repo-{i}',
                'clone_url': f'https://github.com/eclipse-volttron/repo-{i}.git',
                'description': f'Repo {i}',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            } for i in range(100)
        ]
        
        page2_response = Mock()
        page2_response.status_code = 200
        page2_response.json.return_value = [
            {
                'name': f'repo-{i}',
                'html_url': f'https://github.com/eclipse-volttron/repo-{i}',
                'clone_url': f'https://github.com/eclipse-volttron/repo-{i}.git',
                'description': f'Repo {i}',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            } for i in range(25)  # Less than 100, so this is the last page
        ]
        
        mock_get = Mock()
        mock_get.side_effect = [page1_response, page2_response]
        
        with patch('requests.get', mock_get):
            result = search_github_for_agent('repo')
        
        # Should stop after page 2 since it returned < 100 repos
        assert 'Pages scanned: 2' in result
        assert 'Repositories scanned: 125' in result
        assert 'Matches found: 125' in result
    
    def test_pagination_respects_max_page_limit(self):
        """Test that pagination stops at the safety limit."""
        # Create a response that always returns 100 repos (simulating many pages)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': f'agent-{i}',
                'html_url': f'https://github.com/eclipse-volttron/agent-{i}',
                'clone_url': f'https://github.com/eclipse-volttron/agent-{i}.git',
                'description': f'Agent {i}',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            } for i in range(100)
        ]
        
        with patch('requests.get', return_value=mock_response):
            result = search_github_for_agent('agent')
        
        # Should stop at page 10 (max_pages limit)
        assert 'Pages scanned: 10' in result
        assert 'Repositories scanned: 1000' in result
    
    def test_pagination_failure_on_later_page(self):
        """Test handling of API failure on a page after the first."""
        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = [
            {
                'name': 'test-agent',
                'html_url': 'https://github.com/eclipse-volttron/test-agent',
                'clone_url': 'https://github.com/eclipse-volttron/test-agent.git',
                'description': 'Test Agent',
                'updated_at': '2025-11-01T12:00:00Z',
                'stargazers_count': 1
            } for i in range(100)
        ]
        
        page2_response = Mock()
        page2_response.status_code = 500  # Server error on page 2
        
        mock_get = Mock()
        mock_get.side_effect = [page1_response, page2_response]
        
        with patch('requests.get', mock_get):
            result = search_github_for_agent('test')
        
        # Should return results from page 1 even though page 2 failed
        assert 'Pages scanned: 1' in result
        assert 'Repositories scanned: 100' in result
        assert 'Matches found: 100' in result


class TestInstallAgentFromGitHub:
    """Test the install_agent_from_github function."""
    
    def test_successful_installation(self):
        """Test successful agent installation from GitHub."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Agent installed successfully"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('chat_app.volttron_commands.find_vctl_command', return_value='/usr/bin/vctl'):
                with patch('chat_app.volttron_commands.get_volttron_home', return_value='/home/user/.volttron'):
                    result = install_agent_from_github('https://github.com/eclipse-volttron/volttron-listener.git')
        
        assert '✅' in result
        assert 'volttron-listener installed from GitHub successfully' in result
        # Verify no hardcoded emoji (other than success indicator)
        assert '🎉' not in result
        assert '✨' not in result
    
    def test_installation_failure(self):
        """Test handling of installation failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Installation failed: package not found"
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('chat_app.volttron_commands.find_vctl_command', return_value='/usr/bin/vctl'):
                with patch('chat_app.volttron_commands.get_volttron_home', return_value='/home/user/.volttron'):
                    result = install_agent_from_github('https://github.com/eclipse-volttron/bad-agent.git')
        
        assert '❌' in result
        assert 'bad-agent installation failed' in result
        assert 'package not found' in result.lower()
    
    def test_vctl_not_found(self):
        """Test handling when vctl command is not found."""
        with patch('chat_app.volttron_commands.find_vctl_command', return_value=None):
            result = install_agent_from_github('https://github.com/eclipse-volttron/test-agent.git')
        
        assert 'Status: vctl command not found' in result
        assert 'Recommendation:' in result
    
    def test_installation_timeout(self):
        """Test handling of installation timeout."""
        with patch('subprocess.run', side_effect=Exception('Timeout')):
            with patch('chat_app.volttron_commands.find_vctl_command', return_value='/usr/bin/vctl'):
                with patch('chat_app.volttron_commands.get_volttron_home', return_value='/home/user/.volttron'):
                    result = install_agent_from_github('https://github.com/eclipse-volttron/test.git')
        
        assert '❌' in result
        assert 'test.git installation error' in result or 'test installation error' in result
    
    def test_extracts_repo_name_correctly(self):
        """Test that repository name is extracted correctly from URL."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Done"
        mock_result.stderr = ""
        
        # Test with .git extension
        with patch('subprocess.run', return_value=mock_result):
            with patch('chat_app.volttron_commands.find_vctl_command', return_value='/usr/bin/vctl'):
                with patch('chat_app.volttron_commands.get_volttron_home', return_value='/home/user/.volttron'):
                    result = install_agent_from_github('https://github.com/eclipse-volttron/my-agent.git')
        
        assert '✅' in result
        assert 'my-agent installed from GitHub successfully' in result
        
        # Test without .git extension
        with patch('subprocess.run', return_value=mock_result):
            with patch('chat_app.volttron_commands.find_vctl_command', return_value='/usr/bin/vctl'):
                with patch('chat_app.volttron_commands.get_volttron_home', return_value='/home/user/.volttron'):
                    result = install_agent_from_github('https://github.com/eclipse-volttron/another-agent')
        
        assert '✅' in result
        assert 'another-agent installed from GitHub successfully' in result
    
    def test_returns_structured_data(self):
        """Test that response is structured data without hardcoded responses."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Installation complete"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('chat_app.volttron_commands.find_vctl_command', return_value='/usr/bin/vctl'):
                with patch('chat_app.volttron_commands.get_volttron_home', return_value='/home/user/.volttron'):
                    result = install_agent_from_github('https://github.com/eclipse-volttron/test.git')
        
        # Check for concise success message
        assert '✅' in result
        assert 'test installed from GitHub successfully' in result
        
        # Verify NO hardcoded marketing language
        assert '🎉' not in result
        assert 'Congratulations' not in result
        assert 'Great job' not in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
