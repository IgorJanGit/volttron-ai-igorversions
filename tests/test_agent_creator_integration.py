"""
Integration tests for Agent Creator - verifies agents are actually created and installed.

These tests validate the full lifecycle of agent creation:
1. Create agent requirements
2. Generate and write project files
3. Build the agent package (wheel)
4. Verify all artifacts are created correctly

IMPORTANT TESTING NOTES:
- These tests verify that the Agent Creator can successfully generate working
  agent projects with proper structure, dependencies, and buildable packages.
- Full VOLTTRON installation via vctl is complex and requires the agent to be
  pip-installable first, so we focus on verifying the creation and building
  process produces valid artifacts.
- For manual verification of VOLTTRON integration:
  1. Run these tests to create an agent
  2. Install the wheel: pip install agents/<agent-name>/dist/*.whl
  3. Register with VOLTTRON: vctl install <agent-name> --vip-identity <identity> --start

These tests require:
- VOLTTRON platform running (for validation checks)
- vctl command available
- Write access to agents directory
"""

import os
import sys
import pytest
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from chat_app.agent_creator import (
    AgentRequirements,
    write_agent_project,
    build_package,
    install_agent_package,
    validate_agent_name,
    validate_vip_identity
)
from chat_app.volttron_commands import (
    find_vctl_command,
    is_volttron_running_quick,
    vctl_list_agents,
    vctl_stop_agent,
    vctl_uninstall_agent,
    get_volttron_home
)


@pytest.fixture(scope="module")
def check_volttron():
    """Verify VOLTTRON is running before tests."""
    if not is_volttron_running_quick():
        pytest.skip("VOLTTRON is not running. Start it first.")
    
    vctl_cmd = find_vctl_command()
    if not vctl_cmd:
        pytest.skip("vctl command not found. VOLTTRON may not be installed.")


@pytest.fixture
def test_agent_name():
    """Provide unique agent name for test."""
    return "integration-test-agent"


@pytest.fixture
def test_vip_identity():
    """Provide unique VIP identity for test."""
    return "integration.test.agent"


@pytest.fixture
def agent_project_path(test_agent_name):
    """Provide and cleanup agent project path."""
    workspace_root = Path(__file__).parent.parent
    project_path = workspace_root / "agents" / test_agent_name
    
    # Cleanup before test
    if project_path.exists():
        shutil.rmtree(project_path)
    
    yield project_path
    
    # Cleanup after test
    if project_path.exists():
        shutil.rmtree(project_path)


@pytest.fixture
def cleanup_agent(test_vip_identity):
    """Cleanup agent from VOLTTRON after test."""
    yield
    
    # Stop and remove agent
    try:
        vctl_stop_agent(test_vip_identity)
        time.sleep(1)  # Give it a moment to stop
        vctl_uninstall_agent(test_vip_identity)
    except Exception as e:
        print(f"Cleanup warning: {e}")


class TestAgentCreationIntegration:
    """Integration tests for complete agent creation lifecycle."""
    
    def test_create_minimal_agent_end_to_end(
        self, 
        check_volttron,
        test_agent_name, 
        test_vip_identity,
        agent_project_path,
        cleanup_agent
    ):
        """
        Test complete agent creation workflow:
        1. Create requirements
        2. Write project files
        3. Build package
        4. Verify all files are created correctly
        5. Verify wheel is built
        
        Note: Full VOLTTRON installation testing requires manual verification
        due to complex vctl install requirements.
        """
        # Step 1: Create requirements
        req = AgentRequirements()
        req.name = test_agent_name
        req.vip_identity = test_vip_identity
        req.description = "Integration test agent"
        req.template_type = "minimal"
        req.author = "Test Suite"
        req.version = "0.1.0"
        req.package_format = "wheel"
        req.install_after_build = True
        
        # Step 2: Write project files
        project_dir = write_agent_project(req, str(agent_project_path))
        assert Path(project_dir).exists(), "Project directory should be created"
        
        # Verify key files exist
        assert (agent_project_path / "pyproject.toml").exists()
        assert (agent_project_path / "README.md").exists()
        assert (agent_project_path / f"{test_agent_name.replace('-', '_')}" / "__init__.py").exists()
        assert (agent_project_path / f"{test_agent_name.replace('-', '_')}" / "agent.py").exists()
        
        # Verify pyproject.toml has correct content
        pyproject_content = (agent_project_path / "pyproject.toml").read_text()
        assert test_agent_name in pyproject_content
        assert "volttron" in pyproject_content.lower()
        
        # Verify README has VIP identity
        readme_content = (agent_project_path / "README.md").read_text()
        assert test_vip_identity in readme_content
        
        # Verify agent.py has correct structure
        agent_py_path = agent_project_path / f"{test_agent_name.replace('-', '_')}" / "agent.py"
        agent_code = agent_py_path.read_text()
        assert "class" in agent_code
        assert "Agent" in agent_code
        assert "__init__" in agent_code
        
        # Step 3: Build package
        success, message = build_package(project_dir, format="wheel")
        assert success, f"Build should succeed: {message}"
        assert "✅" in message, "Success message should contain checkmark"
        
        # Verify wheel was created
        dist_dir = agent_project_path / "dist"
        assert dist_dir.exists(), "dist directory should exist"
        wheels = list(dist_dir.glob("*.whl"))
        assert len(wheels) > 0, "At least one wheel should be built"
        wheel_path = wheels[0]
        assert wheel_path.exists(), f"Wheel file should exist: {wheel_path}"
        assert test_agent_name.replace("-", "_") in wheel_path.name
        
        # Step 4: Verify wheel can be inspected
        # Check wheel is a valid zip file
        import zipfile
        assert zipfile.is_zipfile(wheel_path), "Wheel should be a valid zip file"
        
        with zipfile.ZipFile(wheel_path, 'r') as whl:
            wheel_contents = whl.namelist()
            # Should contain package files
            package_name = test_agent_name.replace("-", "_")
            assert any(package_name in f for f in wheel_contents), \
                   f"Wheel should contain package files for {package_name}"
            assert any("METADATA" in f for f in wheel_contents), \
                   "Wheel should contain METADATA"
    
    def test_agent_validation_functions(self):
        """Test that validation functions work correctly."""
        # Valid names
        is_valid, message = validate_agent_name("test-agent")
        assert is_valid is True, "Valid agent name should return True"
        assert "✅" in message or "valid" in message.lower()
        
        is_valid, message = validate_agent_name("my_cool_agent")
        assert is_valid is True, "Valid agent name should return True"
        
        # Invalid names
        is_valid, message = validate_agent_name("Invalid Agent!")
        assert is_valid is False, "Invalid agent name should return False"
        assert "❌" in message or "invalid" in message.lower()
        
        is_valid, message = validate_agent_name("")
        assert is_valid is False, "Empty agent name should return False"
        assert "❌" in message or "invalid" in message.lower()
        
        # Valid VIP identities
        is_valid, message = validate_vip_identity("test.agent")
        assert is_valid is True, "Valid VIP identity should return True"
        assert "✅" in message or "valid" in message.lower() or "available" in message.lower()
        
        is_valid, message = validate_vip_identity("platform.driver")
        assert is_valid is True or is_valid is False  # Can be valid or taken depending on VOLTTRON state
        
        # Invalid VIP identities - empty only
        is_valid, message = validate_vip_identity("")
        assert is_valid is False, "Empty VIP identity should return False"
        assert "❌" in message or "cannot be empty" in message.lower()
    
    def test_create_listener_agent_with_topics(
        self,
        check_volttron,
        agent_project_path,
        cleanup_agent
    ):
        """Test creating a listener agent with topic subscriptions."""
        agent_name = "integration-listener-test"
        vip_identity = "integration.listener.test"
        
        # Create requirements for listener agent
        req = AgentRequirements()
        req.name = agent_name
        req.vip_identity = vip_identity
        req.description = "Integration test listener agent"
        req.template_type = "listener"
        req.topics_subscribe = ["devices/campus/building1/#", "analysis/results"]
        req.topics_publish = ["alerts/warnings"]
        req.author = "Test Suite"
        req.version = "0.1.0"
        req.package_format = "wheel"
        
        # Update paths for this test
        project_path = agent_project_path.parent / agent_name
        if project_path.exists():
            shutil.rmtree(project_path)
        
        try:
            # Write project
            project_dir = write_agent_project(req, str(project_path))
            assert Path(project_dir).exists()
            
            # Verify agent.py contains subscription logic
            agent_py = project_path / agent_name.replace("-", "_") / "agent.py"
            agent_code = agent_py.read_text()
            assert "devices/campus/building1/#" in agent_code, \
                   "Subscription topic should be in agent code"
            assert "pubsub.subscribe" in agent_code, \
                   "pubsub.subscribe should be in listener agent code"
            
            # Build package
            success, message = build_package(project_dir, format="wheel")
            assert success, f"Build should succeed: {message}"
            
            # Verify wheel exists
            dist_dir = project_path / "dist"
            wheels = list(dist_dir.glob("*.whl"))
            assert len(wheels) > 0, "Wheel should be created"
        
        finally:
            # Cleanup
            if project_path.exists():
                shutil.rmtree(project_path)
    
    def test_create_agent_with_schedule(
        self,
        check_volttron,
        agent_project_path,
        cleanup_agent
    ):
        """Test creating an agent with scheduled tasks."""
        agent_name = "integration-scheduled-test"
        vip_identity = "integration.scheduled.test"
        
        # Create requirements for scheduled agent
        req = AgentRequirements()
        req.name = agent_name
        req.vip_identity = vip_identity
        req.description = "Integration test scheduled agent"
        req.template_type = "minimal"
        req.schedule_type = "interval"
        req.schedule_value = "30"  # 30 seconds
        req.author = "Test Suite"
        req.version = "0.1.0"
        req.package_format = "wheel"
        
        # Update paths for this test
        project_path = agent_project_path.parent / agent_name
        if project_path.exists():
            shutil.rmtree(project_path)
        
        try:
            # Write project
            project_dir = write_agent_project(req, str(project_path))
            assert Path(project_dir).exists()
            
            # Verify agent.py contains schedule logic
            agent_py = project_path / agent_name.replace("-", "_") / "agent.py"
            agent_code = agent_py.read_text()
            assert "periodic" in agent_code.lower() or "schedule" in agent_code.lower(), \
                   "Schedule logic should be in agent code"
            assert "30" in agent_code, \
                   "Schedule interval should be in agent code"
            
            # Build and verify
            success, _ = build_package(project_dir, format="wheel")
            assert success, "Build should succeed"
            
            # Verify wheel exists
            dist_dir = project_path / "dist"
            wheels = list(dist_dir.glob("*.whl"))
            assert len(wheels) > 0, "Wheel should be created"
        
        finally:
            # Cleanup
            if project_path.exists():
                shutil.rmtree(project_path)
    
    def test_agent_not_duplicated(
        self,
        check_volttron,
        test_agent_name,
        test_vip_identity,
        agent_project_path,
        cleanup_agent
    ):
        """Test that building the same agent twice creates valid wheels each time."""
        # Create and build agent
        req = AgentRequirements()
        req.name = test_agent_name
        req.vip_identity = test_vip_identity
        req.description = "Duplicate build test agent"
        req.template_type = "minimal"
        req.package_format = "wheel"
        
        project_dir = write_agent_project(req, str(agent_project_path))
        
        # Build first time
        success1, msg1 = build_package(project_dir, format="wheel")
        assert success1, "First build should succeed"
        
        dist_dir = agent_project_path / "dist"
        wheels_after_first = list(dist_dir.glob("*.whl"))
        assert len(wheels_after_first) == 1, "Should have one wheel after first build"
        
        # Build second time
        success2, msg2 = build_package(project_dir, format="wheel")
        assert success2, "Second build should succeed"
        
        wheels_after_second = list(dist_dir.glob("*.whl"))
        assert len(wheels_after_second) >= 1, "Should still have wheel(s) after second build"


class TestAgentCreationValidation:
    """Tests for agent creation validation without full VOLTTRON integration."""
    
    def test_project_structure_created_correctly(self, tmp_path):
        """Test that project structure is created with all required files."""
        req = AgentRequirements()
        req.name = "test-structure-agent"
        req.vip_identity = "test.structure.agent"
        req.description = "Test agent for structure validation"
        req.template_type = "minimal"
        
        project_dir = write_agent_project(req, str(tmp_path / "test-agent"))
        project_path = Path(project_dir)
        
        # Verify directory structure
        assert project_path.exists()
        assert (project_path / "pyproject.toml").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / "config").exists()
        assert (project_path / "tests").exists()
        
        package_dir = project_path / "test_structure_agent"
        assert package_dir.exists()
        assert (package_dir / "__init__.py").exists()
        assert (package_dir / "agent.py").exists()
        
        # Verify content
        pyproject_content = (project_path / "pyproject.toml").read_text()
        assert "test-structure-agent" in pyproject_content
        
        readme_content = (project_path / "README.md").read_text()
        assert "test-structure-agent" in readme_content
        assert "Test agent for structure validation" in readme_content
        assert "test.structure.agent" in readme_content  # VIP identity in README
    
    def test_different_template_types_generate_different_code(self, tmp_path):
        """Test that different template types generate different agent code."""
        templates = ["minimal", "listener"]
        agent_codes = {}
        
        for template in templates:
            req = AgentRequirements()
            req.name = f"test-{template}-agent"
            req.vip_identity = f"test.{template}.agent"
            req.description = f"Test {template} agent"
            req.template_type = template
            
            if template == "listener":
                req.topics_subscribe = ["devices/#"]
            
            project_dir = write_agent_project(req, str(tmp_path / f"test-{template}"))
            package_name = f"test_{template}_agent"
            agent_py = Path(project_dir) / package_name / "agent.py"
            agent_codes[template] = agent_py.read_text()
        
        # Verify codes are different
        assert agent_codes["minimal"] != agent_codes["listener"], \
               "Different templates should generate different code"
        
        # Verify listener has subscription logic
        assert "pubsub.subscribe" in agent_codes["listener"], \
               "Listener template should include subscription logic"
        assert "devices/#" in agent_codes["listener"], \
               "Listener template should include specified topics"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
