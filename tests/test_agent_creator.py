"""
Tests for Agent Creator functionality.

This module tests the agent scaffolding wizard, template generation,
project creation, and validation functions.
"""

import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Import the functions we're testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from chat_app.agent_creator import (
    AgentRequirements,
    collect_requirements,
    generate_templates,
    write_agent_project,
    build_package,
    install_agent_package,
    validate_agent_name,
    validate_vip_identity,
    _generate_pyproject_toml,
    _generate_readme,
    _generate_default_config,
    _generate_init_file,
    _generate_test_file
)


class TestAgentRequirements:
    """Test AgentRequirements data class."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        req = AgentRequirements(
            agent_name="test-agent",
            vip_identity="test.agent",
            description="Test agent"
        )
        assert req.agent_name == "test-agent"
        assert req.vip_identity == "test.agent"
        assert req.description == "Test agent"
        assert req.template_type == "minimal"
        assert req.topics_subscribe == []
        assert req.topics_publish == []
        assert req.schedule_type is None
        assert req.dependencies == ["volttron>=11.0.0rc0"]
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        req = AgentRequirements(
            agent_name="test-agent",
            vip_identity="test.agent",
            description="Test agent",
            topics_subscribe=["devices/campus/building1/#"],
            topics_publish=["analysis/results"]
        )
        data = req.to_dict()
        
        assert isinstance(data, dict)
        assert data["agent_name"] == "test-agent"
        assert data["vip_identity"] == "test.agent"
        assert data["topics_subscribe"] == ["devices/campus/building1/#"]
        assert data["topics_publish"] == ["analysis/results"]
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "agent_name": "monitor-agent",
            "vip_identity": "monitor.agent",
            "description": "Monitoring agent",
            "template_type": "listener",
            "topics_subscribe": ["devices/#"],
            "topics_publish": ["alerts/#"],
            "schedule_type": "interval",
            "schedule_value": "60",
            "dependencies": ["volttron>=11.0.0rc0", "pandas"],
            "author": "Test Author",
            "version": "1.0.0",
            "package_format": "wheel"
        }
        
        req = AgentRequirements.from_dict(data)
        assert req.agent_name == "monitor-agent"
        assert req.vip_identity == "monitor.agent"
        assert req.template_type == "listener"
        assert req.topics_subscribe == ["devices/#"]
        assert "pandas" in req.dependencies


class TestValidation:
    """Test validation functions."""
    
    def test_validate_agent_name_valid(self):
        """Test validation of valid agent names."""
        valid_names = [
            "simple-agent",
            "my-test-agent",
            "temperature-monitor",
            "agent123",
            "data-collector-v2"
        ]
        
        for name in valid_names:
            success, message = validate_agent_name(name)
            assert success is True, f"Failed for valid name: {name}"
            assert message == ""
    
    def test_validate_agent_name_invalid(self):
        """Test validation rejects invalid agent names."""
        invalid_names = [
            ("Agent With Spaces", "cannot contain spaces"),
            ("123-agent", "cannot start with a digit"),
            ("agent@special", "can only contain"),
            ("", "cannot be empty"),
            ("a" * 100, "cannot exceed")
        ]
        
        for name, expected_error in invalid_names:
            success, message = validate_agent_name(name)
            assert success is False, f"Should reject: {name}"
            assert expected_error in message.lower()
    
    @patch('chat_app.agent_creator.find_vctl_command')
    @patch('chat_app.agent_creator.subprocess.run')
    def test_validate_vip_identity_unique(self, mock_run, mock_find_vctl):
        """Test VIP identity validation when identity is unique."""
        mock_find_vctl.return_value = "/path/to/vctl"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "UUID  AGENT           IDENTITY\n123   listener.agent   listener\n"
        mock_run.return_value = mock_result
        
        success, message = validate_vip_identity("new.agent")
        assert success is True
        assert message == ""
    
    @patch('chat_app.agent_creator.find_vctl_command')
    @patch('chat_app.agent_creator.subprocess.run')
    def test_validate_vip_identity_collision(self, mock_run, mock_find_vctl):
        """Test VIP identity validation detects collisions."""
        mock_find_vctl.return_value = "/path/to/vctl"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "UUID  AGENT           IDENTITY\n123   listener.agent   listener.agent\n"
        mock_run.return_value = mock_result
        
        success, message = validate_vip_identity("listener.agent")
        assert success is False
        assert "already in use" in message.lower()
    
    @patch('chat_app.agent_creator.find_vctl_command')
    def test_validate_vip_identity_no_volttron(self, mock_find_vctl):
        """Test VIP identity validation when VOLTTRON not running."""
        mock_find_vctl.return_value = None
        
        # Should succeed with warning when VOLTTRON not found
        success, message = validate_vip_identity("test.agent")
        assert success is True
        assert "not checked" in message.lower() or message == ""


class TestWizardFlow:
    """Test wizard flow through all steps."""
    
    def test_step_1_agent_name(self):
        """Test step 1: collecting agent name."""
        state = {}
        req, next_step, prompt = collect_requirements(state, 1, "temperature-monitor")
        
        assert req.agent_name == "temperature-monitor"
        assert next_step == 2
        assert "VIP identity" in prompt
    
    def test_step_2_vip_identity(self):
        """Test step 2: collecting VIP identity."""
        state = {"agent_name": "test-agent"}
        req, next_step, prompt = collect_requirements(state, 2, "test.agent")
        
        assert req.vip_identity == "test.agent"
        assert next_step == 3
        assert "description" in prompt.lower()
    
    def test_step_3_description(self):
        """Test step 3: collecting description."""
        state = {
            "agent_name": "test-agent",
            "vip_identity": "test.agent"
        }
        req, next_step, prompt = collect_requirements(state, 3, "Monitors temperature sensors")
        
        assert req.description == "Monitors temperature sensors"
        assert next_step == 4
        assert "template" in prompt.lower()
    
    def test_step_4_template_type(self):
        """Test step 4: selecting template type."""
        state = {
            "agent_name": "test-agent",
            "vip_identity": "test.agent",
            "description": "Test"
        }
        req, next_step, prompt = collect_requirements(state, 4, "listener")
        
        assert req.template_type == "listener"
        assert next_step == 5
        assert "subscribe" in prompt.lower()
    
    def test_step_5_subscribe_topics(self):
        """Test step 5: collecting subscribe topics."""
        state = {
            "agent_name": "test-agent",
            "vip_identity": "test.agent",
            "description": "Test",
            "template_type": "listener"
        }
        req, next_step, prompt = collect_requirements(state, 5, "devices/campus/#, sensors/#")
        
        assert "devices/campus/#" in req.topics_subscribe
        assert "sensors/#" in req.topics_subscribe
        assert next_step == 6
    
    def test_step_6_publish_topics(self):
        """Test step 6: collecting publish topics."""
        state = {
            "agent_name": "test-agent",
            "vip_identity": "test.agent",
            "description": "Test",
            "template_type": "listener",
            "topics_subscribe": ["devices/#"]
        }
        req, next_step, prompt = collect_requirements(state, 6, "analysis/results")
        
        assert "analysis/results" in req.topics_publish
        assert next_step == 7
    
    def test_step_7_schedule_interval(self):
        """Test step 7: collecting interval schedule."""
        state = {
            "agent_name": "test-agent",
            "vip_identity": "test.agent",
            "description": "Test",
            "template_type": "driver",
            "topics_subscribe": [],
            "topics_publish": ["devices/data"]
        }
        req, next_step, prompt = collect_requirements(state, 7, "interval:60")
        
        assert req.schedule_type == "interval"
        assert req.schedule_value == "60"
        assert next_step == 8
    
    def test_step_8_dependencies(self):
        """Test step 8: collecting dependencies."""
        state = {
            "agent_name": "test-agent",
            "vip_identity": "test.agent",
            "description": "Test",
            "template_type": "listener",
            "topics_subscribe": ["devices/#"],
            "topics_publish": ["analysis/results"],
            "schedule_type": None,
            "schedule_value": None
        }
        req, next_step, prompt = collect_requirements(state, 8, "pandas, numpy")
        
        assert "pandas" in req.dependencies
        assert "numpy" in req.dependencies
        assert "volttron>=11.0.0rc0" in req.dependencies
        assert next_step == 9
    
    def test_step_9_packaging(self):
        """Test step 9: selecting package format."""
        state = {
            "agent_name": "test-agent",
            "vip_identity": "test.agent",
            "description": "Test",
            "template_type": "minimal",
            "topics_subscribe": [],
            "topics_publish": [],
            "schedule_type": None,
            "schedule_value": None,
            "dependencies": ["volttron>=11.0.0rc0"]
        }
        req, next_step, prompt = collect_requirements(state, 9, "wheel")
        
        assert req.package_format == "wheel"
        assert next_step == 10
        assert "complete" in prompt.lower() or "ready" in prompt.lower()


class TestTemplateGeneration:
    """Test template file generation."""
    
    def test_generate_minimal_template(self):
        """Test generating minimal template."""
        req = AgentRequirements(
            agent_name="test-agent",
            vip_identity="test.agent",
            description="Test agent",
            template_type="minimal",
            topics_subscribe=["test/topic"],
            topics_publish=["output/topic"]
        )
        
        templates = generate_templates(req)
        
        assert "agent.py" in templates
        agent_code = templates["agent.py"]
        
        # Check placeholder substitution
        assert "TestAgent" in agent_code
        assert "test.agent" in agent_code
        assert "Test agent" in agent_code
        assert "test/topic" in agent_code
        assert "output/topic" in agent_code
    
    def test_generate_listener_template(self):
        """Test generating listener template."""
        req = AgentRequirements(
            agent_name="data-listener",
            vip_identity="listener.agent",
            description="Listens to data",
            template_type="listener"
        )
        
        templates = generate_templates(req)
        agent_code = templates["agent.py"]
        
        assert "DataListener" in agent_code
        assert "listener.agent" in agent_code
        assert "_handle_message" in agent_code
        assert "_process_message" in agent_code
    
    def test_generate_driver_template(self):
        """Test generating driver template."""
        req = AgentRequirements(
            agent_name="device-driver",
            vip_identity="driver.agent",
            description="Drives devices",
            template_type="driver",
            schedule_type="interval",
            schedule_value="60"
        )
        
        templates = generate_templates(req)
        agent_code = templates["agent.py"]
        
        assert "DeviceDriver" in agent_code
        assert "driver.agent" in agent_code
        assert "_poll_device" in agent_code
        assert "interval" in agent_code
        assert "60" in agent_code
    
    def test_generate_historian_template(self):
        """Test generating historian template."""
        req = AgentRequirements(
            agent_name="data-historian",
            vip_identity="historian.agent",
            description="Stores data",
            template_type="historian"
        )
        
        templates = generate_templates(req)
        agent_code = templates["agent.py"]
        
        assert "DataHistorian" in agent_code
        assert "historian.agent" in agent_code
        assert "_capture_data" in agent_code
        assert "sqlite" in agent_code.lower()


class TestProjectGeneration:
    """Test project structure generation."""
    
    def test_generate_pyproject_toml(self):
        """Test pyproject.toml generation."""
        req = AgentRequirements(
            agent_name="test-agent",
            vip_identity="test.agent",
            description="Test agent",
            dependencies=["volttron>=11.0.0rc0", "pandas"]
        )
        
        content = _generate_pyproject_toml(req)
        
        assert "[build-system]" in content
        assert "[project]" in content
        assert "test-agent" in content
        assert "Test agent" in content
        assert "volttron>=11.0.0rc0" in content
        assert "pandas" in content
    
    def test_generate_readme(self):
        """Test README generation."""
        req = AgentRequirements(
            agent_name="test-agent",
            vip_identity="test.agent",
            description="Test agent",
            template_type="listener"
        )
        
        content = _generate_readme(req)
        
        assert "test-agent" in content
        assert "Test agent" in content
        assert "Installation" in content
        assert "Configuration" in content
        assert "vctl install" in content
    
    def test_generate_default_config(self):
        """Test default config generation."""
        req = AgentRequirements(
            agent_name="test-agent",
            vip_identity="test.agent",
            description="Test agent",
            topics_subscribe=["devices/#"],
            topics_publish=["analysis/results"],
            schedule_type="interval",
            schedule_value="60"
        )
        
        content = _generate_default_config(req)
        config = json.loads(content)
        
        assert config["vip_identity"] == "test.agent"
        assert "devices/#" in config["topics_subscribe"]
        assert "analysis/results" in config["topics_publish"]
        assert config["schedule"]["type"] == "interval"
        assert config["schedule"]["value"] == 60
    
    def test_generate_init_file(self):
        """Test __init__.py generation."""
        content = _generate_init_file()
        assert "__version__" in content
        assert "0.1.0" in content
    
    def test_generate_test_file(self):
        """Test test file generation."""
        req = AgentRequirements(
            agent_name="test-agent",
            vip_identity="test.agent",
            description="Test agent"
        )
        
        content = _generate_test_file(req)
        
        assert "pytest" in content
        assert "test_agent_startup" in content
        assert "test_agent" in content.lower()
    
    def test_write_agent_project(self):
        """Test writing complete project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            req = AgentRequirements(
                agent_name="test-agent",
                vip_identity="test.agent",
                description="Test agent",
                template_type="minimal"
            )
            
            success, message, project_dir = write_agent_project(req, tmpdir)
            
            assert success is True
            assert os.path.exists(project_dir)
            
            # Check directory structure
            assert os.path.exists(os.path.join(project_dir, "test_agent"))
            assert os.path.exists(os.path.join(project_dir, "test_agent", "__init__.py"))
            assert os.path.exists(os.path.join(project_dir, "test_agent", "agent.py"))
            assert os.path.exists(os.path.join(project_dir, "config"))
            assert os.path.exists(os.path.join(project_dir, "config", "default_config.json"))
            assert os.path.exists(os.path.join(project_dir, "tests"))
            assert os.path.exists(os.path.join(project_dir, "tests", "test_agent.py"))
            assert os.path.exists(os.path.join(project_dir, "pyproject.toml"))
            assert os.path.exists(os.path.join(project_dir, "README.md"))


class TestPackaging:
    """Test package building."""
    
    @patch('chat_app.agent_creator.subprocess.run')
    def test_build_package_wheel_success(self, mock_run):
        """Test successful wheel build."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully built test_agent-0.1.0-py3-none-any.whl"
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success, message = build_package(tmpdir, "wheel")
            
            assert success is True
            assert "successfully" in message.lower()
            mock_run.assert_called_once()
            assert "-m" in mock_run.call_args[0][0]
            assert "build" in mock_run.call_args[0][0]
    
    @patch('chat_app.agent_creator.subprocess.run')
    def test_build_package_wheel_failure(self, mock_run):
        """Test failed wheel build."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Build error: missing dependency"
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success, message = build_package(tmpdir, "wheel")
            
            assert success is False
            assert "failed" in message.lower()
    
    @patch('chat_app.agent_creator.subprocess.run')
    def test_build_package_editable(self, mock_run):
        """Test editable install."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed test-agent"
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success, message = build_package(tmpdir, "editable")
            
            assert success is True
            assert "install" in mock_run.call_args[0][0]
            assert "-e" in mock_run.call_args[0][0]


class TestInstallation:
    """Test agent installation."""
    
    @patch('chat_app.agent_creator.find_vctl_command')
    @patch('chat_app.agent_creator.subprocess.run')
    def test_install_agent_vctl_success(self, mock_run, mock_find_vctl):
        """Test successful vctl installation."""
        mock_find_vctl.return_value = "/path/to/vctl"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Agent installed successfully"
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success, message = install_agent_package(
                tmpdir, 
                "test.agent",
                os.path.join(tmpdir, "config", "default_config.json"),
                start=True,
                method="vctl"
            )
            
            assert success is True
            assert "successfully" in message.lower()
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "install" in call_args
            assert "--vip-identity" in call_args
            assert "--start" in call_args
    
    @patch('chat_app.agent_creator.find_vctl_command')
    @patch('chat_app.agent_creator.subprocess.run')
    def test_install_agent_vctl_failure(self, mock_run, mock_find_vctl):
        """Test failed vctl installation."""
        mock_find_vctl.return_value = "/path/to/vctl"
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Installation failed: permission denied"
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success, message = install_agent_package(
                tmpdir,
                "test.agent",
                None,
                start=False,
                method="vctl"
            )
            
            assert success is False
            assert "failed" in message.lower()
    
    @patch('chat_app.agent_creator.subprocess.run')
    def test_install_agent_pip(self, mock_run):
        """Test pip installation."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed test-agent"
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success, message = install_agent_package(
                tmpdir,
                "test.agent",
                None,
                start=False,
                method="pip"
            )
            
            assert success is True
            call_args = mock_run.call_args[0][0]
            assert "pip" in call_args
            assert "install" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
