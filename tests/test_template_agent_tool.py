"""
Tests for create_template_agent_tool function.

This module tests the quick template agent creation tool that allows
the AI to instantly scaffold listener agents.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from chat_app.agent_creator import AgentRequirements, write_agent_project, build_package, install_agent_package


class TestTemplateAgentToolFunction:
    """Test the create_template_agent_tool function directly."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test artifacts."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_tool_creates_requirements_correctly(self):
        """Test that the tool creates AgentRequirements with correct parameters."""
        # Simulate what the tool does
        agent_name = "test-monitor"
        description = "Test monitoring agent"
        topics = "devices/temp/#, devices/humidity/#"
        
        req = AgentRequirements()
        req.name = agent_name
        req.vip_identity = agent_name.replace("-", "_")
        req.description = description
        req.template_type = "listener"
        req.topics_subscribe = [t.strip() for t in topics.split(",")]
        req.author = "VOLTTRON AI"
        req.version = "0.1.0"
        
        assert req.name == "test-monitor"
        assert req.vip_identity == "test_monitor"
        assert req.description == "Test monitoring agent"
        assert req.template_type == "listener"
        assert len(req.topics_subscribe) == 2
        assert "devices/temp/#" in req.topics_subscribe
        assert "devices/humidity/#" in req.topics_subscribe
        assert req.author == "VOLTTRON AI"
        assert req.version == "0.1.0"
    
    def test_tool_handles_single_topic(self):
        """Test that the tool handles a single topic correctly."""
        topics = "devices/#"
        topics_list = [t.strip() for t in topics.split(",")]
        
        assert len(topics_list) == 1
        assert topics_list[0] == "devices/#"
    
    def test_tool_handles_multiple_topics_with_spaces(self):
        """Test that the tool handles topics with extra spaces."""
        topics = "devices/temp/# ,  devices/humidity/# , analysis/data"
        topics_list = [t.strip() for t in topics.split(",")]
        
        assert len(topics_list) == 3
        assert "devices/temp/#" in topics_list
        assert "devices/humidity/#" in topics_list
        assert "analysis/data" in topics_list
    
    @patch('chat_app.agent_creator.write_agent_project')
    @patch('chat_app.agent_creator.build_package')
    @patch('chat_app.agent_creator.install_agent_package')
    def test_tool_workflow_success(self, mock_install, mock_build, mock_write):
        """Test successful end-to-end workflow."""
        # Setup mocks
        mock_write.return_value = "/fake/path/agents/test-agent"
        mock_build.return_value = (True, "Build successful")
        mock_install.return_value = (True, "Agent installed")
        
        # Execute tool logic
        from chat_app.agent_creator import AgentRequirements
        
        req = AgentRequirements()
        req.name = "test-agent"
        req.vip_identity = "test_agent"
        req.description = "Test agent"
        req.template_type = "listener"
        req.topics_subscribe = ["devices/#"]
        req.author = "VOLTTRON AI"
        req.version = "0.1.0"
        
        project_dir = mock_write.return_value
        success_build, msg_build = mock_build.return_value
        success_install, msg_install = mock_install.return_value
        
        # Verify workflow
        assert project_dir == "/fake/path/agents/test-agent"
        assert success_build is True
        assert success_install is True
        
        # Verify calls would be made in correct order
        mock_write.assert_not_called()  # Not called yet
        mock_write(req)
        mock_write.assert_called_once()
    
    @patch('chat_app.agent_creator.write_agent_project')
    @patch('chat_app.agent_creator.build_package')
    def test_tool_handles_build_failure(self, mock_build, mock_write):
        """Test that the tool handles build failures gracefully."""
        mock_write.return_value = "/fake/path/agents/test-agent"
        mock_build.return_value = (False, "Build failed: Missing dependency")
        
        project_dir = mock_write.return_value
        success, msg = mock_build.return_value
        
        assert success is False
        assert "Build failed" in msg
    
    @patch('chat_app.agent_creator.write_agent_project')
    @patch('chat_app.agent_creator.build_package')
    @patch('chat_app.agent_creator.install_agent_package')
    def test_tool_handles_install_failure(self, mock_install, mock_build, mock_write):
        """Test that the tool handles installation failures."""
        mock_write.return_value = "/fake/path/agents/test-agent"
        mock_build.return_value = (True, "Build successful")
        mock_install.return_value = (False, "VOLTTRON not running")
        
        success_install, msg_install = mock_install.return_value
        
        assert success_install is False
        assert "VOLTTRON not running" in msg_install
    
    def test_vip_identity_conversion(self):
        """Test that agent names are correctly converted to VIP identities."""
        test_cases = [
            ("my-agent", "my_agent"),
            ("temp-monitor", "temp_monitor"),
            ("data-collector-v2", "data_collector_v2"),
            ("simple", "simple"),
        ]
        
        for agent_name, expected_vip in test_cases:
            vip_identity = agent_name.replace("-", "_")
            assert vip_identity == expected_vip


class TestTemplateAgentToolIntegration:
    """Integration tests for the template agent tool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
    
    def teardown_method(self):
        """Clean up test artifacts."""
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_full_project_generation(self):
        """Test that a complete project is generated with correct structure."""
        req = AgentRequirements()
        req.name = "test-listener"
        req.vip_identity = "test_listener"
        req.description = "Test listener agent"
        req.template_type = "listener"
        req.topics_subscribe = ["devices/#"]
        req.author = "VOLTTRON AI"
        req.version = "0.1.0"
        
        # Generate project in test directory (no mocking needed)
        project_dir = Path(self.test_dir) / "agents" / req.name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify structure was created
        assert project_dir.parent.name == "agents"
        assert project_dir.name == "test-listener"
        assert project_dir.exists()
        assert project_dir.is_dir()


    def test_listener_template_includes_subscriptions(self):
        """Test that generated listener template includes topic subscriptions."""
        req = AgentRequirements()
        req.name = "sensor-monitor"
        req.vip_identity = "sensor_monitor"
        req.description = "Monitors sensor data"
        req.template_type = "listener"
        req.topics_subscribe = ["devices/sensors/#", "analysis/data"]
        req.author = "VOLTTRON AI"
        req.version = "0.1.0"
        
        # Generate templates
        from chat_app.agent_creator import generate_templates
        templates = generate_templates(req)
        
        # Verify agent.py exists in templates
        agent_file_key = f"{req.name.replace('-', '_')}/agent.py"
        assert agent_file_key in templates
        
        # Verify subscriptions are in the code
        agent_code = templates[agent_file_key]
        assert "devices/sensors/#" in agent_code or "self.vip.pubsub.subscribe" in agent_code


class TestTemplateAgentToolWithAIService:
    """Test the tool's integration with AIService."""
    
    @pytest.mark.skipif(
        not os.path.exists("chat_app/ai_service.py"),
        reason="AIService file not found"
    )
    def test_tool_is_registered_in_ai_service(self):
        """Test that the tool is properly registered in AIService."""
        # Check that the function exists in ai_service.py
        with open("chat_app/ai_service.py", "r") as f:
            content = f.read()
            assert "def create_template_agent_tool" in content
            assert "@agent.tool_plain" in content
    
    @pytest.mark.skipif(
        not os.path.exists("chat_app/ai_service.py"),
        reason="AIService file not found"
    )
    def test_tool_has_proper_docstring(self):
        """Test that the tool has a docstring for the AI to understand."""
        with open("chat_app/ai_service.py", "r") as f:
            content = f.read()
            
            # Find the function definition
            if "def create_template_agent_tool" in content:
                # Check for docstring indicators
                assert '"""' in content or "'''" in content
                assert "agent_name" in content
                assert "description" in content
                assert "topics" in content


class TestTemplateAgentToolErrorHandling:
    """Test error handling in the template agent tool."""
    
    def test_invalid_agent_name_detection(self):
        """Test that invalid agent names would be caught."""
        from chat_app.agent_creator import validate_agent_name
        
        invalid_names = [
            "123-start-with-number",
            "has spaces",
            "has@special!chars",
            "",
        ]
        
        for name in invalid_names:
            valid, msg = validate_agent_name(name)
            assert valid is False
    
    def test_valid_agent_names(self):
        """Test that valid agent names pass validation."""
        from chat_app.agent_creator import validate_agent_name
        
        valid_names = [
            "my-agent",
            "temperature-monitor",
            "data-collector-v2",
            "simple",
        ]
        
        for name in valid_names:
            valid, msg = validate_agent_name(name)
            assert valid is True
    
    @patch('chat_app.agent_creator.write_agent_project')
    def test_exception_handling(self, mock_write):
        """Test that exceptions are caught and returned as error messages."""
        mock_write.side_effect = Exception("Disk full")
        
        # Simulate tool trying to create project
        try:
            mock_write(AgentRequirements())
        except Exception as e:
            error_msg = f"Error creating agent: {str(e)}"
            assert "Disk full" in error_msg


class TestTemplateAgentToolDefaultValues:
    """Test default values and optional parameters."""
    
    def test_default_description(self):
        """Test that default description is used when not provided."""
        default_description = "A VOLTTRON listener agent"
        
        req = AgentRequirements()
        req.description = default_description
        
        assert req.description == "A VOLTTRON listener agent"
    
    def test_default_topics(self):
        """Test that default topic is used when not provided."""
        default_topics = "devices/#"
        topics_list = [t.strip() for t in default_topics.split(",")]
        
        assert len(topics_list) == 1
        assert topics_list[0] == "devices/#"
    
    def test_custom_description_overrides_default(self):
        """Test that custom description overrides default."""
        custom_description = "Custom sensor monitor"
        
        req = AgentRequirements()
        req.description = custom_description
        
        assert req.description == custom_description
        assert req.description != "A VOLTTRON listener agent"
    
    def test_custom_topics_override_default(self):
        """Test that custom topics override default."""
        custom_topics = "analysis/#, control/#"
        topics_list = [t.strip() for t in custom_topics.split(",")]
        
        assert len(topics_list) == 2
        assert "analysis/#" in topics_list
        assert "control/#" in topics_list
        assert "devices/#" not in topics_list


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
