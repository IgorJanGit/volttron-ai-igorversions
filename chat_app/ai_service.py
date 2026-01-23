from typing import Optional, Dict, List, Any, Tuple, Callable
import os
import re
import json
import openai
import inspect

try:
    from pydantic_ai import Agent
except ImportError:
    pass  # Pydantic AI not available
    Agent = None

from .volttron_commands import (
    start_volttron, stop_volttron, check_volttron_status, simple_volttron_status_check, read_volttron_log,
    vctl_status, vctl_status_detailed, vctl_list_agents, vctl_start_agent, vctl_stop_agent, vctl_health,
    show_formatting_test, get_detailed_installation_help, get_volttron_next_steps,
    vctl_install_platform_driver, show_recent_logs, check_volttron_installation, kill_existing_volttron_processes,
    vctl_uninstall_agent, vctl_uninstall_all_listeners, vctl_install_listener_agent,
    vctl_install_agent, list_available_agents, verify_agent_uninstalled, install_volttron_with_pip,
    pip_uninstall_package, pip_install_package, pip_list_packages, install_fake_driver_library,
    show_fake_driver_logs, check_fake_driver_status, watch_fake_driver_logs, setup_fake_driver_complete,
    configure_fake_driver, start_fake_driver,
    vctl_start_all_agents, vctl_force_remove_agent, run_vctl_help, intelligent_vctl_command_discovery,
    smart_install_package, search_github_for_agent, install_agent_from_github,
    list_volttron_packages, list_running_agents, install_from_github_smart, list_all_installations,
    list_repository_packages, fetch_webpage_content, execute_system_command, 
    setup_postgresql_database, create_historian_config
)

from .agent_creator import (
    collect_requirements, generate_templates, write_agent_project,
    build_package, install_agent_package, validate_agent_name,
    validate_vip_identity, AgentRequirements, analyze_url_for_agent
)

if Agent is not None:
    agent = Agent(
        model=None,
        system_prompt=""  # Will be set dynamically
    )
else:
    agent = None

if agent:
    @agent.tool_plain  # type: ignore[union-attr]
    def start_volttron_tool() -> str:
        """Start the VOLTTRON platform."""
        return start_volttron()

    @agent.tool_plain  # type: ignore[union-attr]
    def stop_volttron_tool() -> str:
        """Stop the VOLTTRON platform."""
        return stop_volttron()

    @agent.tool_plain  # type: ignore[union-attr]
    def check_volttron_status_tool() -> str:
        """Check if VOLTTRON platform is running."""
        return check_volttron_status()

    @agent.tool_plain  # type: ignore[union-attr]
    def get_vctl_status_tool() -> str:
        """Get current status of all installed agents."""
        return vctl_status()

    @agent.tool_plain  # type: ignore[union-attr]
    def vctl_status_detailed_tool() -> str:
        """Get detailed status information about VOLTTRON agents."""
        return vctl_status_detailed()

    @agent.tool_plain  # type: ignore[union-attr]
    def list_agents_tool() -> str:
        """List all installed VOLTTRON agents."""
        import subprocess
        import os
        from chat_app.volttron_commands import get_volttron_home, find_vctl_command
        
        volttron_home = get_volttron_home()
        vctl_path = find_vctl_command()
        
        if not vctl_path:
            return "❌ Could not find vctl command. Please ensure VOLTTRON is installed."
        
        try:
            env = os.environ.copy()
            env["VOLTTRON_HOME"] = volttron_home
            
            result = subprocess.run(
                [vctl_path, "status"],
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                output = result.stdout
                if output.strip():
                    return f"🤖 **Installed VOLTTRON Agents:**\n\n```\n{output}\n```"
                else:
                    return "No agents are currently installed."
            else:
                error = result.stderr or result.stdout or "Unknown error"
                return f"Error listing agents: {error}"
        except Exception as e:
            return f"Failed to list agents: {str(e)}"

    @agent.tool_plain  # type: ignore[union-attr]
    def start_agent_tool(agent_uuid: str) -> str:
        """Start a VOLTTRON agent by UUID.
        
        Args:
            agent_uuid: The UUID or tag of the agent to start
        """
        return vctl_start_agent(agent_uuid)

    @agent.tool_plain  # type: ignore[union-attr]
    def stop_agent_tool(agent_uuid: str) -> str:
        """Stop a VOLTTRON agent by UUID.
        
        Args:
            agent_uuid: The UUID or tag of the agent to stop
        """
        return vctl_stop_agent(agent_uuid)

    @agent.tool_plain  # type: ignore[union-attr]
    def vctl_health_tool() -> str:
        """Check VOLTTRON platform health."""
        return vctl_health()

    @agent.tool_plain  # type: ignore[union-attr]
    def install_platform_driver_tool() -> str:
        """Install the VOLTTRON platform driver agent."""
        return vctl_install_platform_driver()

    @agent.tool_plain  # type: ignore[union-attr]
    def show_recent_logs_tool() -> str:
        """Show recent VOLTTRON logs."""
        return show_recent_logs()

    @agent.tool_plain  # type: ignore[union-attr]
    def check_volttron_installation_tool() -> str:
        """Check if VOLTTRON is properly installed."""
        return check_volttron_installation()

    @agent.tool_plain  # type: ignore[union-attr]
    def kill_existing_processes_tool() -> str:
        """Kill any existing VOLTTRON processes."""
        return kill_existing_volttron_processes()

    @agent.tool_plain  # type: ignore[union-attr]
    def uninstall_agent_tool(agent_uuid: str) -> str:
        """Uninstall a VOLTTRON agent by UUID.
        
        Args:
            agent_uuid: The UUID or tag of the agent to uninstall
        """
        return vctl_uninstall_agent(agent_uuid)

    @agent.tool_plain  # type: ignore[union-attr]
    def install_listener_agent_tool() -> str:
        """Install a VOLTTRON listener agent."""
        return vctl_install_listener_agent()

    @agent.tool_plain  # type: ignore[union-attr]
    def install_agent_tool(agent_name: str) -> str:
        """Install a VOLTTRON agent by name.
        
        Args:
            agent_name: The name of the agent to install
        """
        return vctl_install_agent(agent_name)

    @agent.tool_plain  # type: ignore[union-attr]
    def install_volttron_tool() -> str:
        """Install VOLTTRON using pip and set up the environment."""
        return install_volttron_with_pip()

    @agent.tool_plain  # type: ignore[union-attr]
    def pip_uninstall_tool(package_name: str) -> str:
        """Uninstall a Python package using pip.
        
        Args:
            package_name: The name of the package to uninstall (e.g., 'volttron-listener')
        """
        return pip_uninstall_package(package_name, force=True)
    
    @agent.tool_plain  # type: ignore[union-attr]
    def pip_install_tool(package_name: str, upgrade: bool = False) -> str:
        """Install a Python package using pip.
        
        Args:
            package_name: The name of the package to install (e.g., 'volttron-platform-driver')
            upgrade: Whether to add the --upgrade flag
        """
        return pip_install_package(package_name, upgrade)

    @agent.tool_plain  # type: ignore[union-attr]
    def pip_list_tool() -> str:
        """List all installed Python packages."""
        return pip_list_packages()

    @agent.tool_plain  # type: ignore[union-attr]
    def smart_install_tool(package_name: str, user_message: str = "") -> str:
        """Intelligently install a package using pip or vctl based on package type.
        
        This is the flexible installation tool that handles all installation requests.
        It automatically determines whether to use pip or vctl based on what's being installed.
        
        Rules:
        - Fake driver library → MUST use pip (vctl won't work)
        - Python libraries (volttron-*) → Use pip
        - VOLTTRON agents → Use vctl install
        
        Args:
            package_name: Name of package/agent to install
            user_message: Original user message for context
        """
        return smart_install_package(package_name, user_message)

    @agent.tool_plain  # type: ignore[union-attr]
    def install_fake_driver_library_tool() -> str:
        """Install the volttron-lib-fake-driver package for testing and development."""
        return install_fake_driver_library()

    @agent.tool_plain  # type: ignore[union-attr]
    def show_fake_driver_logs_tool(num_lines: int = 50) -> str:
        """Show recent fake driver data from VOLTTRON logs.
        
        Args:
            num_lines: Number of recent log lines to check (default: 50)
        """
        return show_fake_driver_logs(num_lines)

    @agent.tool_plain  # type: ignore[union-attr]
    def check_fake_driver_status_tool() -> str:
        """Check if the fake driver is actively publishing data by examining recent logs.
        
        This checks actual log activity to determine if fake driver is working, not just installation status.
        Returns clear status information based on real-time log analysis.
        """
        return check_fake_driver_status()

    @agent.tool_plain  # type: ignore[union-attr]
    def watch_fake_driver_logs_tool() -> str:
        """Get instructions for watching fake driver logs in real-time using tail -f."""
        return watch_fake_driver_logs()

    @agent.tool_plain  # type: ignore[union-attr]
    def setup_fake_driver_complete_tool() -> str:
        """Complete automated setup of fake driver - installs library, platform driver, configures, and starts everything.
        
        This is the ONE COMMAND to fully set up the fake driver so users can immediately see fake data in logs.
        Use this when user wants to 'set up fake driver' or 'install fake driver' - it does EVERYTHING.
        """
        return setup_fake_driver_complete()

    @agent.tool_plain  # type: ignore[union-attr]
    def force_remove_agent_tool(agent_tag_or_uuid: str) -> str:
        """Force remove an agent by tag or UUID using aggressive removal methods.
        
        Use this tool when standard removal fails or times out. This tool performs
        multiple removal strategies to ensure the agent is completely removed from
        the system, including direct file manipulation if standard removal fails.
        
        Args:
            agent_tag_or_uuid: The tag or UUID of the agent to force remove
        """
        return vctl_force_remove_agent(agent_tag_or_uuid)
        
    @agent.tool_plain  # type: ignore[union-attr]
    def start_all_agents_tool() -> str:
        """Start all available VOLTTRON agents that are not currently running."""
        return vctl_start_all_agents()

    @agent.tool_plain  # type: ignore[union-attr]
    def search_github_for_agent_tool(agent_name: str) -> str:
        """Search eclipse-volttron GitHub organization for agent repositories when local agent not found.
        
        Args:
            agent_name: The name of the agent to search for on GitHub
        """
        return search_github_for_agent(agent_name)

    @agent.tool_plain  # type: ignore[union-attr]
    def install_agent_from_github_tool(repo_url: str) -> str:
        """Install a VOLTTRON agent from a GitHub repository URL.
        
        Args:
            repo_url: The GitHub repository URL or clone URL to install from
        """
        return install_agent_from_github(repo_url)

    @agent.tool_plain  # type: ignore[union-attr]
    def install_from_github_smart_tool(repo_url: str) -> str:
        """Intelligently analyze and install from any GitHub repository.
        
        Reads the README, detects installation method (pip, poetry, ansible, vctl, etc.)
        and provides appropriate installation instructions or executes installation.
        
        Use this when the installation method is unknown or for non-standard repos.
        
        Args:
            repo_url: The GitHub repository URL
        """
        return install_from_github_smart(repo_url)

    @agent.tool_plain  # type: ignore[union-attr]
    def list_all_installations_tool() -> str:
        """List everything installed: agents, pip packages, Ansible roles, and more.
        
        Shows comprehensive installation status across all tools:
        - VOLTTRON agents (vctl status)
        - Python packages (pip list for volttron-*)
        - Ansible roles (ansible-galaxy list)
        - Other tool-specific installations
        
        Use this for any query about what's installed.
        """
        return list_all_installations()

    @agent.tool_plain  # type: ignore[union-attr]
    def list_repository_packages_tool() -> str:
        """List all VOLTTRON packages in the current repository's virtual environment.
        
        Shows packages installed via pip in THIS workspace (not system VOLTTRON).
        Useful for tracking what's installed during development when installing many packages.
        Includes version numbers and separates VOLTTRON packages from related tools.
        """
        return list_repository_packages()

    @agent.tool_plain  # type: ignore[union-attr]
    def run_vctl_help_tool(subcommand: Optional[str] = None) -> str:
        """Run vctl --help to learn about available commands.
        
        Use this tool when you don't know what vctl command to use or need to learn
        about available options. Can get general help or help for a specific subcommand.
        
        Args:
            subcommand: Optional subcommand to get help for (e.g., 'install', 'status', 'config')
        """
        return run_vctl_help(subcommand)

    @agent.tool_plain  # type: ignore[union-attr]
    def intelligent_vctl_discovery_tool(user_intent: str, context: str = "") -> str:
        """Intelligently discover and execute vctl commands by learning from --help.
        
        This tool automatically:
        1. Runs vctl --help to see available commands
        2. Analyzes the user's intent
        3. Picks the most likely command
        4. Executes it and returns the result
        
        Use this when the user asks for something that might need a vctl command but
        you're not sure which one.
        
        Args:
            user_intent: What the user is trying to do (e.g., "check agent health")
            context: Additional context about the request
        """
        result = intelligent_vctl_command_discovery(user_intent, context)
        
        response = f"**Command Discovery Results:**\n\n"
        response += f"**Intent:** {user_intent}\n"
        response += f"**Help Consulted:** {', '.join(result['help_consulted'])}\n"
        
        if result['command_used']:
            response += f"**Command Used:** `{result['command_used']}`\n"
        
        response += f"**Status:** {'✅ Success' if result['success'] else '❌ Failed'}\n\n"
        response += f"**Output:**\n```\n{result['output']}\n```"
        
        return response

class AIService:
    """Service for handling AI model interactions with function tools support."""
    
    def __init__(self, model_name: str):
        """Initialize the AI service with a specific model."""
        self.model_name = model_name
        self.agent = agent
        self.custom_client = None
        self.conversation_history = []
        self.agent_creator_state: dict = {}
        self.last_numbered_options = {}
        self.fake_driver_setup_state = "not_started"  # Track fake driver setup progress
        self.volttron_checked = False
        self.conversation_file = "conversation_history.json"  # File to persist conversation
        self.last_action = None
        self.last_action_details = {}
        self.function_tools = {}
        self.system_prompt = self._get_volttron_system_prompt()
        self.cancellation_requested = False
        
        if self.agent:
            try:
                self.agent.model = model_name
            except Exception as e:
                print(f"Warning: Could not configure Pydantic AI agent: {e}")
                self.agent = None
        
        self._register_fallback_function_tools()
        self._load_conversation_history()
        self._setup_agent()
    
    def _load_conversation_history(self):
        """Load conversation history from file if it exists."""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, 'r') as f:
                    data = json.load(f)
                    self.conversation_history = data.get('history', [])[-20:]
                    print(f"Loaded {len(self.conversation_history)} previous conversation messages")
        except Exception as e:
            print(f"Could not load conversation history: {e}")
            self.conversation_history = []
    
    def _save_conversation_history(self):
        """Save conversation history to file."""
        try:
            data = {
                'history': self.conversation_history[-20:],
                'timestamp': str(os.path.getmtime(self.conversation_file)) if os.path.exists(self.conversation_file) else None
            }
            with open(self.conversation_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Could not save conversation history: {e}")
    
    async def ping_ai(self) -> dict:
        """
        Test AI API connection with a simple ping request.
        Works with multiple providers: custom webapp, Ollama, OpenAI-compatible APIs.
        Returns response indicating if AI API is working.
        """
        try:
            import httpx
            
            # Detect provider based on model configuration
            ai_webapp_url = os.getenv("AI_WEBAPP_URL")
            ai_api_key = os.getenv("AI_API_KEY")
            is_ollama = self.model_name.startswith("ollama:")
            
            # Extract actual model name (remove provider prefix)
            actual_model = self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
            
            # Configure based on provider
            if is_ollama:
                # Ollama provider
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                endpoint = f"{base_url}/api/generate" if not base_url.endswith("/v1") else f"{base_url}/chat/completions"
                headers = {"Content-Type": "application/json"}
                
                # Try OpenAI-compatible endpoint first (Ollama v1 API)
                if "/v1" in base_url or endpoint.endswith("/completions"):
                    payload = {
                        "model": actual_model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 10
                    }
                else:
                    # Native Ollama API
                    payload = {
                        "model": actual_model,
                        "prompt": "test",
                        "stream": False
                    }
                    
            elif ai_webapp_url and ai_api_key:
                # Custom webapp (PNNL AI Incubator or similar)
                endpoint = ai_webapp_url if "/completions" in ai_webapp_url else f"{ai_webapp_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {ai_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": actual_model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10
                }
                
            else:
                # Standard OpenAI/Anthropic via pydantic-ai (no direct ping available)
                return {
                    "status": "info",
                    "message": f"Using {self.model_name} via Pydantic AI",
                    "provider": self.model_name.split(":")[0] if ":" in self.model_name else "default",
                    "details": "Direct API ping not available for this provider. Try sending a chat message to test."
                }
            
            # Make the API request
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract response content based on provider format
                    if is_ollama and "response" in data:
                        # Native Ollama format
                        sample = data.get("response", "")[:50]
                    elif "choices" in data:
                        # OpenAI-compatible format
                        sample = data.get("choices", [{}])[0].get("message", {}).get("content", "")[:50]
                    else:
                        sample = str(data)[:50]
                    
                    return {
                        "status": "success",
                        "message": "AI API is working",
                        "provider": "ollama" if is_ollama else "custom" if ai_webapp_url else "standard",
                        "model": self.model_name,
                        "endpoint": endpoint,
                        "response_sample": sample
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API returned status {response.status_code}",
                        "provider": "ollama" if is_ollama else "custom" if ai_webapp_url else "standard",
                        "endpoint": endpoint,
                        "details": response.text[:200]
                    }
                    
        except httpx.ConnectError as e:
            return {
                "status": "error",
                "message": "Cannot connect to AI API",
                "details": f"Connection failed: {str(e)}. Check if the service is running and accessible."
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "message": "AI API request timed out",
                "details": "The request took too long. Check if the service is responsive."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to ping AI API",
                "details": f"{type(e).__name__}: {str(e)}"
            }

    def get_model_info(self) -> dict:
        """Get information about the configured model.
        
        Returns:
            dict: Model information including name, provider, and model_id
        """
        info = {
            'model_name': self.model_name,
            'model_id': self.model_name
        }
        
        # Parse provider prefix if present (e.g., "openai:gpt-4o-mini")
        if ':' in self.model_name:
            parts = self.model_name.split(':', 1)
            info['provider'] = parts[0]
            info['model_id'] = parts[1]
        
        return info

    def get_model_info(self) -> dict:
        """Get information about the configured model.
        
        Returns:
            dict: Model information including name, provider, and model_id
        """
        info = {
            'model_name': self.model_name,
            'model_id': self.model_name
        }
        
        # Parse provider prefix if present (e.g., "openai:gpt-4o-mini")
        if ':' in self.model_name:
            parts = self.model_name.split(':', 1)
            info['provider'] = parts[0]
            info['model_id'] = parts[1]
        
        return info

    def _register_fallback_function_tools(self):
        """Register all VOLTTRON function tools with their schemas."""
        self.function_tools = {
            "start_volttron": {
                "function": start_volttron,
                "schema": {
                    "name": "start_volttron",
                    "description": "Start the VOLTTRON platform",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "stop_volttron": {
                "function": stop_volttron,
                "schema": {
                    "name": "stop_volttron", 
                    "description": "Stop the VOLTTRON platform",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "check_volttron_status": {
                "function": check_volttron_status,
                "schema": {
                    "name": "check_volttron_status",
                    "description": "Check if VOLTTRON platform is running. Returns a clear yes/no answer. Use this when user asks 'is VOLTTRON running?' or similar questions.",
                    "parameters": {
                        "type": "object", 
                        "properties": {},
                        "required": []
                    }
                }
            },
            "simple_volttron_status_check": {
                "function": simple_volttron_status_check,
                "schema": {
                    "name": "simple_volttron_status_check",
                    "description": "Simple check if VOLTTRON is running with minimal output",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "vctl_status": {
                "function": vctl_status,
                "schema": {
                    "name": "vctl_status",
                    "description": "List all installed VOLTTRON agents with their status. Use when user asks 'what agents do I have', 'list agents', 'show agents', or 'which agents are installed'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "vctl_install_listener_agent": {
                "function": vctl_install_listener_agent,
                "schema": {
                    "name": "vctl_install_listener_agent",
                    "description": "Install the VOLTTRON listener agent for monitoring platform messages",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "vctl_uninstall_agent": {
                "function": vctl_uninstall_agent,
                "schema": {
                    "name": "vctl_uninstall_agent",
                    "description": "Uninstall/remove a specific agent by UUID or tag with verification",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_uuid_or_tag": {
                                "type": "string",
                                "description": "The UUID or tag of the agent to uninstall"
                            }
                        },
                        "required": ["agent_uuid_or_tag"]
                    }
                }
            },
            "verify_agent_uninstalled": {
                "function": verify_agent_uninstalled,
                "schema": {
                    "name": "verify_agent_uninstalled",
                    "description": "Verify that an agent has been completely uninstalled",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_identifier": {
                                "type": "string", 
                                "description": "Agent UUID, tag, or name to verify removal of"
                            }
                        },
                        "required": ["agent_identifier"]
                    }
                }
            },
            "vctl_start_agent": {
                "function": vctl_start_agent,
                "schema": {
                    "name": "vctl_start_agent",
                    "description": "Start a specific agent by UUID or tag",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_uuid_or_tag": {
                                "type": "string",
                                "description": "The UUID or tag of the agent to start"
                            }
                        },
                        "required": ["agent_uuid_or_tag"]
                    }
                }
            },
            "vctl_stop_agent": {
                "function": vctl_stop_agent,
                "schema": {
                    "name": "vctl_stop_agent",
                    "description": "Stop a specific agent by UUID or tag", 
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_uuid_or_tag": {
                                "type": "string",
                                "description": "The UUID or tag of the agent to stop"
                            }
                        },
                        "required": ["agent_uuid_or_tag"]
                    }
                }
            },
            "list_available_agents": {
                "function": list_available_agents,
                "schema": {
                    "name": "list_available_agents",
                    "description": "List all available VOLTTRON agents that can be installed",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "install_volttron_with_pip": {
                "function": install_volttron_with_pip,
                "schema": {
                    "name": "install_volttron_with_pip",
                    "description": "Install VOLTTRON using pip and set up the environment",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "pip_uninstall": {
                "function": pip_uninstall_package,
                "schema": {
                    "name": "pip_uninstall",
                    "description": "Uninstall a Python package using pip",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package_name": {
                                "type": "string",
                                "description": "The name of the package to uninstall (e.g., 'volttron-listener')"
                            }
                        },
                        "required": ["package_name"]
                    }
                }
            },
            "pip_install": {
                "function": pip_install_package,
                "schema": {
                    "name": "pip_install",
                    "description": "Install a Python package using pip",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package_name": {
                                "type": "string",
                                "description": "The name of the package to install (e.g., 'volttron-platform-driver')"
                            },
                            "upgrade": {
                                "type": "boolean",
                                "description": "Whether to add the --upgrade flag",
                                "default": False
                            }
                        },
                        "required": ["package_name"]
                    }
                }
            },
            "pip_list": {
                "function": pip_list_packages,
                "schema": {
                    "name": "pip_list",
                    "description": "List all installed Python packages",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "vctl_install_platform_driver": {
                "function": vctl_install_platform_driver,
                "schema": {
                    "name": "vctl_install_platform_driver",
                    "description": "Install the VOLTTRON platform driver agent",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "smart_install_package": {
                "function": smart_install_package,
                "schema": {
                    "name": "smart_install_package",
                    "description": "Intelligently install a package using pip or vctl. Automatically determines the right installation method. Use this for all 'install X' requests.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package_name": {
                                "type": "string",
                                "description": "Name of the package or agent to install"
                            },
                            "user_message": {
                                "type": "string",
                                "description": "Original user message for context",
                                "default": ""
                            }
                        },
                        "required": ["package_name"]
                    }
                }
            },
            "install_fake_driver_library": {
                "function": install_fake_driver_library,
                "schema": {
                    "name": "install_fake_driver_library",
                    "description": "Install the volttron-lib-fake-driver package for testing and simulating device data",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "show_fake_driver_logs": {
                "function": show_fake_driver_logs,
                "schema": {
                    "name": "show_fake_driver_logs",
                    "description": "Show recent fake driver data and activity from VOLTTRON logs",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "num_lines": {
                                "type": "integer",
                                "description": "Number of recent log lines to check (default: 50)",
                                "default": 50
                            }
                        },
                        "required": []
                    }
                }
            },
            "check_fake_driver_status": {
                "function": check_fake_driver_status,
                "schema": {
                    "name": "check_fake_driver_status",
                    "description": "Check if fake driver is actively publishing data by examining recent log activity. Returns status based on actual log data, not just installation.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "watch_fake_driver_logs": {
                "function": watch_fake_driver_logs,
                "schema": {
                    "name": "watch_fake_driver_logs",
                    "description": "Get instructions for watching fake driver logs in real-time using tail -f command",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "setup_fake_driver_complete": {
                "function": setup_fake_driver_complete,
                "schema": {
                    "name": "setup_fake_driver_complete",
                    "description": "Complete automated setup of fake driver - installs library, platform driver, configures, and starts everything so user can immediately see fake data in logs",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "configure_fake_driver": {
                "function": configure_fake_driver,
                "schema": {
                    "name": "configure_fake_driver",
                    "description": "Configure the fake driver with config files and restart platform driver",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "start_fake_driver": {
                "function": start_fake_driver,
                "schema": {
                    "name": "start_fake_driver",
                    "description": "Complete workflow to start fake driver - installs library, platform driver, configures, and starts everything",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "vctl_start_all_agents": {
                "function": vctl_start_all_agents,
                "schema": {
                    "name": "vctl_start_all_agents",
                    "description": "Start all available VOLTTRON agents that are not currently running",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "vctl_force_remove_agent": {
                "function": vctl_force_remove_agent,
                "schema": {
                    "name": "vctl_force_remove_agent",
                    "description": "Force remove a VOLTTRON agent by tag or UUID, using aggressive methods to ensure complete removal even when standard removal fails",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_tag": {
                                "type": "string",
                                "description": "The tag or UUID of the agent to force remove"
                            }
                        },
                        "required": ["agent_tag"]
                    }
                }
            },
            "search_github_for_agent": {
                "function": search_github_for_agent,
                "schema": {
                    "name": "search_github_for_agent",
                    "description": "Search eclipse-volttron GitHub organization repositories for an agent when it's not found locally. Returns matching repositories with URLs for user confirmation before installation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_name": {
                                "type": "string",
                                "description": "The name of the agent to search for on GitHub"
                            }
                        },
                        "required": ["agent_name"]
                    }
                }
            },
            "install_agent_from_github": {
                "function": install_agent_from_github,
                "schema": {
                    "name": "install_agent_from_github",
                    "description": "Install a VOLTTRON agent from a GitHub repository URL after user confirms. Use this after search_github_for_agent when user confirms which repository to install.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "The GitHub repository URL or clone URL to install the agent from"
                            }
                        },
                        "required": ["repo_url"]
                    }
                }
            },
            "install_from_github_smart": {
                "function": install_from_github_smart,
                "schema": {
                    "name": "install_from_github_smart",
                    "description": "Intelligently analyze any GitHub repository and determine how to install it. Detects pip, poetry, ansible, copier templates, documentation sites, and provides appropriate installation instructions. Use this when installation method is unclear or for non-standard repositories.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "The GitHub repository URL to analyze and install"
                            }
                        },
                        "required": ["repo_url"]
                    }
                }
            },
            "list_all_installations": {
                "function": list_all_installations,
                "schema": {
                    "name": "list_all_installations",
                    "description": "List everything installed: VOLTTRON agents (vctl), pip packages (volttron-*), Ansible roles, and other installations. Use for any 'what is installed' or installation status query.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "list_repository_packages": {
                "function": list_repository_packages,
                "schema": {
                    "name": "list_repository_packages",
                    "description": "List all VOLTTRON packages installed in the current repository's virtual environment with version numbers. Shows what's in THIS workspace, not system VOLTTRON. Useful when installing many packages.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "show_recent_logs": {
                "function": show_recent_logs,
                "schema": {
                    "name": "show_recent_logs",
                    "description": "Show recent VOLTTRON logs with focus on fake driver and agent activity",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "run_vctl_help": {
                "function": run_vctl_help,
                "schema": {
                    "name": "run_vctl_help",
                    "description": "Run vctl --help to learn about available commands. Use this when you don't know what vctl command to use.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subcommand": {
                                "type": "string",
                                "description": "Optional subcommand to get help for (e.g., 'install', 'status', 'config')"
                            }
                        },
                        "required": []
                    }
                }
            },
            "intelligent_vctl_command_discovery": {
                "function": lambda user_intent, context="": intelligent_vctl_command_discovery(user_intent, context),
                "schema": {
                    "name": "intelligent_vctl_command_discovery",
                    "description": "Intelligently discover and execute vctl commands by analyzing user intent and consulting vctl --help. Use this when user asks for something that might need a vctl command but you're not sure which one.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_intent": {
                                "type": "string",
                                "description": "What the user is trying to do (e.g., 'check agent health', 'list peers')"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context about the request"
                            }
                        },
                        "required": ["user_intent"]
                    }
                }
            },
            "start_agent_creator_tool": {
                "function": lambda: self._start_agent_creator_impl(),
                "schema": {
                    "name": "start_agent_creator_tool",
                    "description": "Start the agent creation wizard. Use this when user wants to create a new VOLTTRON agent.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "agent_creator_next_step_tool": {
                "function": lambda user_input: self._agent_creator_next_step_impl(user_input),
                "schema": {
                    "name": "agent_creator_next_step_tool",
                    "description": "Advance to the next step in the agent creation wizard.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_input": {
                                "type": "string",
                                "description": "User's response to current wizard step"
                            }
                        },
                        "required": ["user_input"]
                    }
                }
            },
            "agent_scaffold_tool": {
                "function": lambda: self._agent_scaffold_impl(),
                "schema": {
                    "name": "agent_scaffold_tool",
                    "description": "Generate agent project files based on collected requirements.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "agent_package_tool": {
                "function": lambda: self._agent_package_impl(),
                "schema": {
                    "name": "agent_package_tool",
                    "description": "Build the agent package (wheel or editable install).",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "agent_install_tool": {
                "function": lambda start_agent=True: self._agent_install_impl(start_agent),
                "schema": {
                    "name": "agent_install_tool",
                    "description": "Install the built agent package to VOLTTRON.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_agent": {
                                "type": "boolean",
                                "description": "Whether to start the agent after installation",
                                "default": True
                            }
                        },
                        "required": []
                    }
                }
            }
        }
    def get_function_schemas(self) -> List[Dict]:
        """Get OpenAI function schemas for all registered tools."""
        return [tool["schema"] for tool in self.function_tools.values()]
    
    def get_tools_schemas(self) -> List[Dict]:
        """Get OpenAI tools format (new format) for all registered tools."""
        return [
            {
                "type": "function",
                "function": tool["schema"]
            }
            for tool in self.function_tools.values()
        ]
    
    def call_function_tool(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Call a registered function tool with the provided arguments."""
        if function_name not in self.function_tools:
            return f"❌ Unknown function: {function_name}"
        
        try:
            tool = self.function_tools[function_name]
            function = tool["function"]
            
            if arguments:
                result = function(**arguments)
            else:
                result = function()
            
            self._track_action_for_reversal(function_name, arguments, result)
            
            return str(result)
        except Exception as e:
            return f"❌ Error calling {function_name}: {str(e)}"
    
    def _track_action_for_reversal(self, function_name: str, arguments: Dict, result: str):
        """Track function calls for contextual reversal detection."""
        if "uninstall" in function_name or "remove" in function_name:
            self.last_action = "uninstall_agent"
            self.last_action_details = {
                "function": function_name,
                "arguments": arguments,
                "result": result
            }
        elif "install" in function_name:
            self.last_action = "install_agent"
            self.last_action_details = {
                "function": function_name,
                "arguments": arguments,
                "result": result
            }
        elif "start" in function_name:
            self.last_action = "start_agent"
            self.last_action_details = {
                "function": function_name,
                "arguments": arguments,
                "result": result
            }
        elif "stop" in function_name:
            self.last_action = "stop_agent" 
            self.last_action_details = {
                "function": function_name,
                "arguments": arguments,
                "result": result
            }
    
    def _should_check_volttron_installation(self, message: str) -> bool:
        """
        Determine if we should check VOLTTRON installation based on the message content.
        Returns True for first-time interactions or general VOLTTRON queries.
        """
        message_lower = message.lower().strip()
        
        if self.volttron_checked:
            return False
        
        if len(self.conversation_history) == 0:
            return True
        
        general_queries = [
            'hello', 'hi', 'hey', 'start', 'begin', 'help', 'what can you do',
            'how do i', 'getting started', 'setup', 'install', 'volttron',
            'what is volttron', 'how does volttron work', 'agents', 'status',
            'what agents', 'show me', 'list', 'what can i install'
        ]
        
        if any(term in message_lower for term in general_queries):
            return True
        
        return False
    
    def _detect_numbered_option_request(self, message: str) -> Tuple[bool, int]:
        """
        Detect if user is referencing a numbered option from previous response.
        Returns: (is_numbered_request, option_number)
        """
        import re
        
        patterns = [
            r'option\s*(\d+)',
            r'number\s*(\d+)', 
            r'choice\s*(\d+)',
            r'do\s*(\d+)',
            r'step\s*(\d+)',
            r'lets?\s+do\s*step\s*(\d+)',
            r'lets?\s+do\s*(\d+)',
            r'#(\d+)',
            r'(\d+)(?:\s*$)',
            r'can\s+we\s+do\s+(\d+)',
            r'let\'s\s+do\s+(\d+)',
            r'pick\s+(\d+)',
            r'select\s+(\d+)',
            r'go\s+with\s+(\d+)',
        ]
        
        message_lower = message.lower().strip()
        
        if "next step" in message_lower:
            return True, -1
        
        if re.match(r'^\s*\d+\s*$', message_lower):
            try:
                option_num = int(message_lower.strip())
                if 1 <= option_num <= 10:
                    return True, option_num
            except ValueError:
                pass
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    option_num = int(match.group(1))
                    if 1 <= option_num <= 10:
                        return True, option_num
                except ValueError:
                    continue
        
        return False, 0
    
    def _detect_context_reversal(self, message: str) -> Tuple[bool, str]:
        """
        Detect if the user wants to reverse/undo the last action based on context.
        Enhanced to analyze conversation history when last_action tracking isn't available.
        Returns (is_reversal, suggested_action)
        """
        message_lower = message.lower().strip()
        
        reversal_phrases = [
            "i changed my mind", "i change my mind", "change my mind", "changed my mind",
            "actually don't", "actually, don't", "actually no", "actually, no",
            "never mind", "nevermind", "cancel that", "undo that", "reverse that", "reverse it",
            "stop that", "wait, don't", "wait don't", "actually stop", "actually, stop",
            "on second thought", "forget that", "forget it", "abort", "cancel", "undo", "go back",
            "dont do that", "don't do that", "not what i want", "that's not what i want",
            "that's wrong", "wait", "hold on", "scratch that", "nope", "no wait",
            "actually", "instead", "rather", "i don't want", "don't want that", "i made a mistake"
        ]
        
        for phrase in reversal_phrases:
            if phrase in message_lower:
                self.awaiting_reversal_confirmation = True
                
                if self.last_action == "start_volttron":
                    return True, "It sounds like you want to stop VOLTTRON instead. Should I stop the VOLTTRON platform for you?"
                elif self.last_action == "stop_volttron":
                    return True, "It sounds like you want to start VOLTTRON instead. Should I start the VOLTTRON platform for you?"
                elif self.last_action == "install_agent":
                    agent_type = self.last_action_details.get("agent_type", "the agent") if self.last_action_details else "the agent"
                    agent_id = self.last_action_details.get("agent_id", "") if self.last_action_details else ""
                    if agent_id:
                        return True, f"It sounds like you want to uninstall the {agent_type} agent (ID: {agent_id}) that was just installed. Should I uninstall it for you?"
                    else:
                        return True, f"It sounds like you want to uninstall the {agent_type} agent that was just installed. Should I uninstall it for you?"
                elif self.last_action == "uninstall_agent":
                    agent_type = self.last_action_details.get("agent_type", "agent") if self.last_action_details else "agent" 
                    return True, f"It sounds like you want to reinstall the {agent_type} agent. Should I install it again for you?"
                elif self.last_action == "create_config":
                    config_type = self.last_action_details.get("config_type", "configuration") if self.last_action_details else "configuration"
                    return True, f"It sounds like you want to remove the {config_type} files that were just created. Should I delete them for you?"
                elif self.last_action:
                    return True, f"It sounds like you want to reverse the last action ({self.last_action}). What would you like me to do instead?"
                else:
                    # No last_action tracked, check conversation history
                    recent_action_suggestion = self._analyze_conversation_for_reversal()
                    if recent_action_suggestion:
                        self.awaiting_reversal_confirmation = True
                        return True, recent_action_suggestion
                    else:
                        # No action to reverse found
                        self.awaiting_reversal_confirmation = False
                        return False, ""
        
        return False, ""
    
    def _analyze_conversation_for_reversal(self):
        """Deep analysis of conversation history to infer what user wants to reverse."""
        if not hasattr(self, 'conversation_history') or not self.conversation_history:
            return None
        
        recent_messages = self.conversation_history[-10:]
        
        action_patterns = {
            'agent_installation': [
                'installed successfully', 'agent installed', 'installation complete',
                'now installed and running', 'actively monitoring', 'listener agent installed',
                'platform driver installed', 'historian installed', '🎉', 'listener agent',
                'agent is now active', 'monitoring your volttron platform'
            ],
            'volttron_start': [
                'volttron started', 'started with pid', 'platform is running',
                'volttron platform started', 'volttron is now running', 'background process',
                'successfully started', 'started server process'
            ],
            'volttron_stop': [
                'volttron stopped', 'platform stopped', 'shutting down',
                'volttron has been stopped', 'platform shutdown', 'stopped successfully',
                'gracefully stopped'
            ],
            'agent_uninstall': [
                'completely removed', 'agent uninstalled', 'removed from platform',
                'uninstall successful', 'agent removed', 'deletion complete',
                'verification passed', 'successfully removed'
            ],
            'config_creation': [
                'config created', 'configuration files', 'fake.config',
                'driver configuration', 'config file generated', 'stored successfully'
            ],
            'status_check': [
                'status:', 'running agents:', 'no installed agents',
                'platform status', 'current agents', 'uuid'
            ]
        }
        
        for message in reversed(recent_messages):
            content = message.get('content', '').lower()
            role = message.get('role', '')
            
            if role == 'assistant':
                for action_type, indicators in action_patterns.items():
                    if any(indicator in content for indicator in indicators):
                        suggestion = self._create_reversal_suggestion(action_type, content)
                        if suggestion:
                            return suggestion
        
        return None
    
    def _create_reversal_suggestion(self, action_type: str, content: str):
        """Create specific reversal suggestion based on detected action."""
        if action_type == 'agent_installation':
           
            if 'listener' in content:
                self.last_action = "install_agent"
                self.last_action_details = {"agent_type": "listener"}
               
                import re
                uuid_match = re.search(r'uuid[:\s]+([a-f0-9\-]+|\w+)', content, re.IGNORECASE)
                if uuid_match:
                    self.last_action_details["agent_id"] = uuid_match.group(1)
                    return f"I see we just installed a listener agent (ID: {uuid_match.group(1)}). Should I uninstall it for you?"
                else:
                    return "I see we just installed a listener agent. Should I uninstall it for you?"
            elif 'platform driver' in content or 'driver' in content:
                self.last_action = "install_agent"
                self.last_action_details = {"agent_type": "platform driver"}
                return "I see we just installed a platform driver. Should I uninstall it for you?"
            elif 'historian' in content:
                self.last_action = "install_agent"
                self.last_action_details = {"agent_type": "historian"}
                return "I see we just installed a historian agent. Should I uninstall it for you?"
            else:
                self.last_action = "install_agent"
                self.last_action_details = {"agent_type": "agent"}
                return "I see we just installed an agent. Should I uninstall it for you?"
                
        elif action_type == 'volttron_start':
            self.last_action = "start_volttron"
            self.last_action_details = {}
            return "I see we just started VOLTTRON. Should I stop it for you?"
            
        elif action_type == 'volttron_stop':
            self.last_action = "stop_volttron"
            self.last_action_details = {}
            return "I see we just stopped VOLTTRON. Should I start it again for you?"
            
        elif action_type == 'agent_uninstall':
            self.last_action = "uninstall_agent"
            if 'listener' in content:
                self.last_action_details = {"agent_type": "listener"}
                return "I see we just uninstalled a listener agent. Should I reinstall it for you?"
            else:
                self.last_action_details = {"agent_type": "agent"}
                return "I see we just uninstalled an agent. Should I reinstall it for you?"
                
        elif action_type == 'config_creation':
            self.last_action = "create_config"
            if 'fake' in content:
                self.last_action_details = {"config_type": "fake driver configuration"}
                return "I see we just created fake driver configuration files. Should I remove them for you?"
            else:
                self.last_action_details = {"config_type": "configuration"}
                return "I see we just created configuration files. Should I remove them for you?"
                
        return None
    
    def _track_action(self, action: str, details: Optional[dict] = None):
        """Track the last action performed for context reversal."""
        self.last_action = action
        self.last_action_details = details or {}
    
    def _store_numbered_options(self, response: str):
        """Extract and store numbered options from AI response."""
        import re
        
        
        pattern = r'(\d+)\.\s*\*\*(.*?)\*\*\s*-\s*(.*?)(?=\n\d+\.|$)'
        matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
        
        if matches:
            self.last_numbered_options = {}
            for match in matches:
                option_num = int(match[0])
                option_title = match[1].strip()
                option_description = match[2].strip()
                self.last_numbered_options[option_num] = {
                    'title': option_title,
                    'description': option_description,
                    'full_text': f"**{option_title}** - {option_description}"
                }
    
    def _execute_numbered_option(self, option_num: int) -> str:
        """Execute the action for a specific numbered option."""
        
        if option_num == -1:
            return self._execute_next_step()
        
        if option_num not in self.last_numbered_options:
            return f"Sorry, I don't remember option {option_num}. Could you ask me again what you'd like to do?"
        
        option = self.last_numbered_options[option_num]
        title = option['title'].lower()
        description = option['description'].lower()
        
        if 'current agents' in title or 'what\'s running' in title or 'show' in title and 'agents' in title:
            return vctl_status()
        elif 'platform driver' in title and 'install' in title:
            self._track_action("install_agent", {"agent_type": "platform driver"})
            return vctl_install_platform_driver()
        elif 'listener' in title and 'install' in title:
            self._track_action("install_agent", {"agent_type": "listener"})
            return vctl_install_listener_agent()
        elif 'install' in title and ('agent' in title or any(agent in title for agent in ['historian', 'sqlite', 'postgresql', 'bacnet', 'fake-driver', 'protocol', 'lookup', 'scan'])):
            words = title.lower().split()
            agent_name = None
            
            for word in words:
                if word in ['sqlite-historian', 'postgresql-historian', 'bacnet-driver', 'fake-driver', 'protocol-proxy', 'bacnet-proxy', 'platform-lookup', 'bacnet-scan']:
                    agent_name = word
                    break
                elif word in ['sqlite', 'postgresql'] and 'historian' in title:
                    agent_name = f"{word}-historian"
                    break
                elif word in ['bacnet'] and ('driver' in title or 'proxy' in title):
                    agent_name = 'bacnet-driver' if 'driver' in title else 'bacnet-proxy'
                    break
                elif word == 'fake' and 'driver' in title:
                    agent_name = 'fake-driver'
                    break
            
            if agent_name:
                self._track_action("install_agent", {"agent_type": agent_name})
                return vctl_install_agent(agent_name)
            else:
                return list_available_agents()
        elif 'what agents' in title or 'available agents' in title or 'can i install' in title:
            return list_available_agents()
        elif 'volttron status' in title or 'check' in title and 'status' in title or 'healthy' in title:
            return check_volttron_status()
        elif 'historian agent' in title:
            return "📊 Setting up Historian Agent would go here - this feature is coming soon!"
        elif 'weather agent' in title:
            return "🌤️ Setting up Weather Agent would go here - this feature is coming soon!"
        elif 'scheduler agent' in title:
            return "⏰ Setting up Scheduler Agent would go here - this feature is coming soon!"
        elif 'start volttron' in title:
            self._track_action("start_volttron")
            return start_volttron()
        elif 'stop volttron' in title:
            self._track_action("stop_volttron")
            return stop_volttron()
        elif 'kill volttron' in title or 'cleanup volttron' in title or 'force stop volttron' in title:
            self._track_action("stop_volttron")
            return kill_existing_volttron_processes()
        elif 'agent list' in title or 'list agents' in title:
            return vctl_list_agents()
        elif 'uninstall all listeners' in title or 'remove all listeners' in title or 'cleanup listeners' in title:
            self._track_action("uninstall_agent", {"agent_type": "all listeners"})
            return vctl_uninstall_all_listeners()
        elif ('verify uninstall' in title or 'check uninstall' in title or 'confirm removal' in title or 
              'verify removal' in title or 'check if' in title or 'check removal' in title):
            words = title.lower().split()
            agent_id = None
            
            for i, word in enumerate(words):
                if word in ['verify', 'check', 'confirm']:
                    for j in range(i + 1, len(words)):
                        potential_id = words[j]
                        if potential_id in ['uninstall', 'removal', 'of', 'agent', 'the', 'if', 'was', 'removed', 'that']:
                            continue
                        if potential_id:
                            agent_id = potential_id
                            break
                    if agent_id:
                        break
            
            if not agent_id:
                for i, word in enumerate(words):
                    if word in ['uninstall', 'removal'] and i + 1 < len(words):
                        potential_id = words[i + 1]
                        if potential_id not in ['of', 'agent', 'the', 'was']:
                            agent_id = potential_id
                            break
            
            if agent_id:
                return verify_agent_uninstalled(agent_id)
            else:
                return """❌ **Agent ID/UUID required for verification**

Please specify which agent to verify removal of. Examples:
• **"Verify uninstall 1"** - Check if agent with UUID 1 is removed
• **"Check removal of listener"** - Verify listener agent is gone
• **"Confirm uninstall platform.driver"** - Verify platform driver removal

Use 'vctl status' to see current agents if you're unsure."""
        elif 'uninstall' in title or 'remove agent' in title or 'delete agent' in title:
            words = title.lower().split()
            agent_id = None
            
            for i, word in enumerate(words):
                if word in ['uninstall', 'remove', 'delete']:
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        if next_word != 'agent':  
                            agent_id = next_word
                        elif i + 2 < len(words):  
                            agent_id = words[i + 2]
                    break
            
            if not agent_id:
                for word in words:
                    if word.isdigit():
                        agent_id = word
                        break
            
            if agent_id:
                self._track_action("uninstall_agent", {"agent_id": agent_id})
                return vctl_uninstall_agent(agent_id)
            else:
                return """❌ **Agent ID/UUID required for uninstall**

Please specify which agent to uninstall. Examples:
• **"Uninstall 1"** - Remove agent with UUID 1
• **"Remove agent platform.driver"** - Remove by identity
• **"Delete agent listener"** - Remove by tag

💡 **Tip:** Use **"List agents"** first to see available agents with their UUIDs."""
        elif 'config directory' in title or 'create the config directory' in title:
            return f"🎯 Executing option {option_num}: **{option['title']}**\n\n{option['description']}\n\nLet me know if you'd like me to help with this specific task!"
        
        # Default case if no condition matched
        return f"🎯 Executing option {option_num}: **{option['title']}**\n\n{option['description']}"
    
    def _execute_next_step(self) -> str:
        """Execute the next logical step based on current fake driver setup state."""
        
        if self.fake_driver_setup_state == "not_started":
            self.fake_driver_setup_state = "platform_driver_ready"
            return vctl_install_platform_driver()
        elif self.fake_driver_setup_state == "platform_driver_ready":
            return "🎉 **Platform driver installation is complete!**\n\nWhat would you like to do next?\n1. **Check VOLTTRON status** - See how everything is running\n2. **View agent list** - See all your active agents\n3. **Check logs** - See recent activity"
        else:
            
            return check_volttron_status()
    
    def _create_agent_with_tools(self):
        """Create an agent for custom client usage with tools."""
        if Agent is not None:
            # If using custom OpenAI-compatible API (like PNNL), configure it
            if hasattr(self, 'custom_client') and self.custom_client:
                try:
                    from pydantic_ai.models.openai import OpenAIChatModel
                    from pydantic_ai.providers.openai import OpenAIProvider
                    # Use custom model name (without provider prefix)
                    model_name = self.custom_model if hasattr(self, 'custom_model') else self.model_name
                    # Create custom provider with PNNL API endpoint
                    provider = OpenAIProvider(
                        base_url=os.getenv("AI_WEBAPP_URL"),
                        api_key=os.getenv("AI_API_KEY")
                    )
                    # Create OpenAI model with custom provider
                    model = OpenAIChatModel(
                        model_name,
                        provider=provider
                    )
                    agent = Agent(
                        model,
                        system_prompt=self._get_volttron_system_prompt()
                    )
                    print(f"✓ Using Pydantic AI with custom API: {os.getenv('AI_WEBAPP_URL')}")
                except ImportError as e:
                    # Fallback if OpenAIModel not available
                    print(f"Warning: Could not import from pydantic_ai ({e}), using default")
                    agent = Agent(
                        self.model_name,
                        system_prompt=self._get_volttron_system_prompt()
                    )
            else:
                agent = Agent(
                    self.model_name,
                    system_prompt=self._get_volttron_system_prompt()
                )
            
            self._register_volttron_tools_on_agent(agent)
            return agent
        else:
            return None
    

    # Agent Creator Implementation Methods (for fallback function tools)
    def _start_agent_creator_impl(self):
        """Implementation for starting the agent creator wizard."""
        # Check if wizard is already active
        if self.agent_creator_state.get("agent_creator_active"):
            current_step = self.agent_creator_state.get("agent_creator_step", 1)
            req_data = self.agent_creator_state.get("agent_requirements", {})
            agent_name = req_data.get("name", "your agent")
            
            return f"""⚠️ **Agent Creator Already In Progress!**

You're currently creating an agent called **"{agent_name}"** (Step {current_step}/10).

**Options:**
1. **Continue** - Type your response to the current step to keep going
2. **Cancel** - Type **'cancel wizard'** to stop and start fresh
3. **Restart** - Type **'restart wizard'** to clear and start from Step 1
4. **Status** - Type **'wizard status'** to see your progress
5. **Help** - Type **'wizard help'** for all commands

**Tip:** Type 'wizard help' to see all available commands!
"""
        
        # Initialize wizard state in conversation history
        conversation_history = self._load_conversation_history()
        self.agent_creator_state["agent_creator_active"] = True
        self.agent_creator_state["agent_creator_step"] = 1
        self.agent_creator_state["agent_requirements"] = {}
        
        self._save_conversation_history()
        
        welcome = """
🎉 **Welcome to the VOLTTRON Agent Creator!**

This wizard will help you build a production-ready VOLTTRON agent with:

✨ **Automated Code Generation**
   - Complete agent structure with all required files
   - Extensively commented code explaining VOLTTRON patterns
   - Best practices built-in (error handling, logging, configuration)

🎓 **Educational Guidance**
   - Each step explains VOLTTRON concepts
   - Links to official documentation
   - Examples for common use cases

🤖 **AI-Powered Analysis** (NEW!)
   - Paste any API documentation URL
   - Get implementation recommendations automatically
   - TODO comments guide you through integration

📚 **What You'll Get:**
   - `agent.py` - Your agent code with detailed comments
   - `pyproject.toml` - Package configuration
   - `README.md` - Installation and usage guide
   - `config/default_config.json` - Configuration template
   - `tests/test_agent.py` - Test skeleton

**📖 Reference Documentation:**
https://volttron.readthedocs.io/en/9.0.4/developing-volttron/developing-agents/agent-development.html

💡 **Ready to start?** Type 'yes' or press enter to begin!
"""
        
        # Store that we need to show the process info next
        self.agent_creator_state["show_process_next"] = True
        return welcome
    
    def _agent_creator_next_step_impl(self, user_input):
        """Implementation for advancing to next step in agent creator wizard."""
        conversation_history = self._load_conversation_history()
        
        if not self.agent_creator_state.get("agent_creator_active"):
            return "❌ Agent creator not active. Start with 'create a new agent' first."
        
        # Check for cancellation commands FIRST before processing as wizard input
        user_input_lower = user_input.lower().strip()
        cancel_commands = [
            'cancel', 'cancel wizard', 'stop', 'stop wizard', 'exit', 'exit wizard',
            'quit', 'quit wizard', 'abort', 'leave', 'stop this', 'cancel this',
            'stop agent creation', 'cancel agent creation', 'exit agent creation'
        ]
        
        if any(cmd == user_input_lower or user_input_lower.startswith(cmd + ' ') for cmd in cancel_commands):
            agent_name = self.agent_creator_state.get("agent_requirements", {}).get("name", "your agent")
            current_step = self.agent_creator_state.get("agent_creator_step", 1)
            self.agent_creator_state["agent_creator_active"] = False
            self.agent_creator_state["agent_creator_step"] = 1
            self.agent_creator_state["agent_requirements"] = {}
            self._save_conversation_history()
            return f"""✅ **Agent Creator Cancelled**

Agent creation for "{agent_name}" has been cancelled at Step {current_step}/10.

Your progress was not saved. Type **"create an agent"** to start fresh."""
        
        # Check for undo/back commands - go to previous step
        undo_commands = [
            'undo', 'back', 'go back', 'previous', 'previous step', 
            'step back', 'undo step', 'reverse', 'go to previous step'
        ]
        
        if any(cmd == user_input_lower or user_input_lower.startswith(cmd + ' ') for cmd in undo_commands):
            current_step = self.agent_creator_state.get("agent_creator_step", 1)
            
            if current_step <= 1:
                return """⚠️ **Can't Go Back**

You're already at Step 1 (the first step).

**Options:**
• Continue answering the current step
• Type **"restart wizard"** to start over
• Type **"cancel wizard"** to cancel"""
            
            # Go back one step
            previous_step = current_step - 1
            self.agent_creator_state["agent_creator_step"] = previous_step
            self._save_conversation_history()
            
            # Get the prompt for the previous step
            req_data = self.agent_creator_state.get("agent_requirements", {})
            _, _, previous_prompt = collect_requirements(req_data, previous_step, "")
            previous_prompt_with_cta = self._add_wizard_cta(previous_prompt, previous_step, req_data)
            
            # Show what they previously entered for that step
            previous_values = {
                1: req_data.get('name', 'Not set'),
                2: req_data.get('vip_identity', 'Not set'),
                3: req_data.get('description', 'Not set'),
                3.5: req_data.get('doc_url', 'Not set'),
                4: req_data.get('template', 'Not set'),
                5: ', '.join(req_data.get('subscribe_topics', [])) if req_data.get('subscribe_topics') else 'None',
                6: ', '.join(req_data.get('publish_topics', [])) if req_data.get('publish_topics') else 'None',
                7: req_data.get('schedule', 'Not set'),
                8: ', '.join(req_data.get('dependencies', [])) if req_data.get('dependencies') else 'None',
                9: req_data.get('package_format', 'Not set')
            }
            
            previous_value = previous_values.get(previous_step, 'Not set')
            
            return f"""⬅️ **Going Back to Step {previous_step}/10**

Your previous answer: **{previous_value}**

{previous_prompt_with_cta}"""

        # Check if we need to show process info first
        if self.agent_creator_state.get("show_process_next"):
            self.agent_creator_state["show_process_next"] = False
            process_info = """
**🚀 Process:**
10 quick steps → Generate code → Build package → Install to VOLTTRON

**⚠️ Important:** Generated code is a starting template. Review and test thoroughly before production use.

Let's begin!

"""
            # Get first step prompt
            req = AgentRequirements()
            _, _, first_prompt = collect_requirements({}, 1, "")
            first_prompt_with_cta = self._add_wizard_cta(first_prompt, 1, {})
            return process_info + first_prompt_with_cta

        
        current_step = self.agent_creator_state.get("agent_creator_step", 1)
        req_data = self.agent_creator_state.get("agent_requirements", {})
        
        # Collect requirements
        req, next_step, next_prompt = collect_requirements(
            {"agent_requirements": req_data},
            current_step,
            user_input
        )
        
        # If step 3.6 (URL analysis), analyze the URL
        if next_step == 3.6 and req.url:
            try:
                recommendations = analyze_url_for_agent(req.url, req.description)
                req.ai_recommendations = recommendations
                next_prompt = f"✅ **URL Analysis Complete!**\n\n{recommendations[:500]}...\n\n(Full recommendations will be included in generated code)\n\nPress Enter to continue."
                # Stay at 3.6, will advance to 4 on next input
                # next_step is already 3.6
            except Exception as e:
                next_prompt = f"⚠️ Could not analyze URL: {str(e)}\n\nContinuing without URL analysis. Press Enter to continue."
                # Stay at 3.6, will advance to 4 on next input
        
        # Update conversation history
        self.agent_creator_state["agent_creator_step"] = next_step
        self.agent_creator_state["agent_requirements"] = req.to_dict()
        
        if next_step > 9:
            # All steps complete, trigger scaffolding
            self.agent_creator_state["agent_creator_active"] = False
            self._save_conversation_history()
            
            return next_prompt + "\n\n" + self._agent_scaffold_impl()
        else:
            self._save_conversation_history()
            return self._add_wizard_cta(next_prompt, next_step, req.to_dict())
    
    def _add_wizard_cta(self, prompt: str, step: int, req_data: dict = None) -> str:
        """Add clear call-to-action footer to wizard prompts."""
        # Special handling for step 2 to show actual suggested VIP identity
        if step == 2 and req_data and req_data.get('vip_identity'):
            suggested_vip = req_data.get('vip_identity')
            cta = f"\n\n💡 **Suggested:** {suggested_vip}\n   Type **'yes'** to use it, or provide your own."
            return prompt + cta
        
        cta_messages = {
            1: "\n\n💡 **Ready?** Just type your agent name (e.g., 'weather-monitor') and press enter.",
            2: "\n\n💡 **Suggested:** Based on your agent name, I recommend this VIP identity.\n   Type **'yes'** to use it, or provide your own.",
            3: "\n\n💡 **Ready?** Describe what your agent does in 1-2 sentences.",
            4: "\n\n💡 **Options:** Type the template number (1-4) or name (minimal/listener/driver/historian).",
            5: "\n\n💡 **Add topics:** Enter topics separated by commas, or type **'none'** to skip.",
            6: "\n\n💡 **Add topics:** Enter topics separated by commas, or type **'none'** to skip.",
            7: "\n\n💡 **Choose schedule:** Type 'none', an interval (e.g., '60s', '5m'), or cron expression.",
            8: "\n\n💡 **Add packages:** Enter package names separated by commas, or type **'none'** to skip.",
            9: "\n\n💡 **Choose format:** Type **'wheel'** (recommended) or **'editable'**."
        }
        
        cta = cta_messages.get(step, "\n\n💡 **Ready?** Type **'yes'** or **'continue'** to proceed.")
        return prompt + cta

    def _agent_scaffold_impl(self):
        """Implementation for scaffolding the agent project files."""
        conversation_history = self._load_conversation_history()
        req_data = self.agent_creator_state.get("agent_requirements", {})
        
        if not req_data:
            return "❌ No agent requirements found. Start the agent creator first."
        
        req = AgentRequirements.from_dict(req_data)
        
        # Validate name
        valid, msg = validate_agent_name(req.name)
        if not valid:
            return msg
        
        # Validate VIP identity
        valid, msg = validate_vip_identity(req.vip_identity)
        if not valid:
            return msg
        
        try:
            # Generate project
            project_dir = write_agent_project(req)
            
            # Store project directory in conversation history
            self.agent_creator_state["agent_project_dir"] = project_dir
            self.agent_creator_state["agent_package_format"] = req.package_format
            self._save_conversation_history()
            
            return f"""✅ **Agent project created successfully!**

**Location:** `{project_dir}`

**Generated Files:**
- `{req.name.replace('-', '_')}/agent.py` - Main agent code with detailed comments
- `pyproject.toml` - Project metadata and dependencies
- `README.md` - Usage instructions and documentation
- `config/default_config.json` - Default configuration
- `tests/test_agent.py` - Basic unit tests

📋 **What would you like to do next?**

**Option 1: Quick Start (Recommended)**
• Type: **"install and run"** or **"start it"**
• I'll start VOLTTRON (if needed), build, install, and run your agent

**Option 2: Step by Step**
• Type: **"build"** - Just build the package
• Type: **"install"** - Build and install (without starting)
• Type: **"start volttron"** - Start VOLTTRON platform first

**Option 3: Manual Review**
• Review the code in `{project_dir}` first
• Come back when ready with: **"install my agent"**

⚠️ **Note:** Generated code may require adjustments. Review before production use.

**Your choice:** Type what you'd like to do next (or **"help"** for more options)
"""
        except Exception as e:
            return f"❌ Error creating agent project: {str(e)}"
    
    def _agent_package_impl(self):
        """Implementation for building the agent package."""
        conversation_history = self._load_conversation_history()
        project_dir = self.agent_creator_state.get("agent_project_dir")
        package_format = self.agent_creator_state.get("agent_package_format", "wheel")
        
        if not project_dir:
            return "❌ No agent project found. Create an agent first."
        
        success, message = build_package(project_dir, package_format)
        
        if success:
            # Store build status
            self.agent_creator_state["agent_built"] = True
            self._save_conversation_history()
            
            return message + "\n\n**Ready to install?** Say 'install my agent' or I can do it automatically now."
        else:
            return message
    
    def _agent_install_impl(self, start_agent=True):
        """Implementation for installing the agent into VOLTTRON."""
        conversation_history = self._load_conversation_history()
        project_dir = self.agent_creator_state.get("agent_project_dir")
        req_data = self.agent_creator_state.get("agent_requirements", {})
        
        if not project_dir:
            return "❌ No agent project found. Create an agent first."
        
        if not req_data:
            return "❌ No agent requirements found."
        
        req = AgentRequirements.from_dict(req_data)
        
        # Check if agent was built
        if not self.agent_creator_state.get("agent_built"):
            # Build first
            success, build_msg = build_package(project_dir, req.package_format)
            if not success:
                return f"❌ Build failed before installation:\n{build_msg}"
        
        # Install using vctl
        success, message = install_agent_package(
            project_dir,
            req.vip_identity,
            start=start_agent,
            method="vctl"
        )
        
        if success:
            self.agent_creator_state["agent_installed"] = True
            self._save_conversation_history()
            
            return message + f"""

🎉 **Congratulations!** Your agent is now running!

⚠️ **Remember:** This is a template. Review and test the generated code before production use.

**What's next?**

• **Check status:** Say 'show agent status' or 'vctl status'
• **View logs:** Say 'show logs' to see your agent in action
• **Configure:** Edit `{project_dir}/config/default_config.json` and update with `vctl config store`
• **Modify code:** The agent is in `{project_dir}`, edit and reinstall
• **Create another:** Say 'create a new agent' to make another one!

**Agent Details:**
- Name: {req.name}
- VIP Identity: {req.vip_identity}
- Template: {req.template_type}

**Documentation:** https://volttron.readthedocs.io/
"""
        else:
            return message


    def _register_volttron_tools(self):
        """Register VOLTTRON control tools with the agent using Pydantic AI's tool system."""
        @self.agent.tool_plain  # type: ignore[union-attr]
        def start_volttron_tool() -> str:
            """Start the VOLTTRON platform."""
            return start_volttron()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def stop_volttron_tool() -> str:
            """Stop the VOLTTRON platform."""
            return stop_volttron()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def check_volttron_status_tool() -> str:
            """Check VOLTTRON platform status and show recent logs."""
            return check_volttron_status()
            
        @self.agent.tool_plain  # type: ignore[union-attr]
        def simple_volttron_status_check_tool() -> str:
            """Simple check if VOLTTRON is running with minimal output."""
            return simple_volttron_status_check()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def get_vctl_status_tool() -> str:
            """Get VOLTTRON platform status using vctl status command."""
            return vctl_status()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def read_volttron_log_tool(num_lines: int = 10) -> str:
            """Read recent VOLTTRON log entries.
            
            Args:
                num_lines: Number of recent log lines to read (default: 10)
            """
            return read_volttron_log(num_lines)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def list_agents_tool() -> str:
            """List all installed VOLTTRON agents."""
            return vctl_list_agents()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def start_agent_tool(agent_uuid: str) -> str:
            """Start a VOLTTRON agent by UUID.
            
            Args:
                agent_uuid: The UUID of the agent to start
            """
            return vctl_start_agent(agent_uuid)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def stop_agent_tool(agent_uuid: str) -> str:
            """Stop a VOLTTRON agent by UUID.
            
            Args:
                agent_uuid: The UUID of the agent to stop
            """
            return vctl_stop_agent(agent_uuid)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def install_agent_tool(agent_name: str) -> str:
            """Install a VOLTTRON agent by name.
            
            Args:
                agent_name: Name of the agent to install (e.g., 'listener', 'platform-driver')
            """
            return vctl_install_agent(agent_name)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def uninstall_agent_tool(agent_uuid: str) -> str:
            """Uninstall a VOLTTRON agent by UUID (stop and remove).
            
            Args:
                agent_uuid: The UUID of the agent to uninstall
            """
            return vctl_uninstall_agent(agent_uuid)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def get_volttron_help_tool() -> str:
            """Get detailed VOLTTRON installation and setup help."""
            return get_detailed_installation_help()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def list_available_agents_tool() -> str:
            """Show all available VOLTTRON agents that can be installed."""
            return list_available_agents()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def vctl_status_detailed_tool() -> str:
            """Get detailed VOLTTRON platform and agent status."""
            return vctl_status_detailed()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def vctl_health_tool() -> str:
            """Check VOLTTRON platform health status."""
            return vctl_health()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def install_platform_driver_tool() -> str:
            """Install the VOLTTRON platform driver for device communication."""
            return vctl_install_platform_driver()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def show_recent_logs_tool(lines: int = 20) -> str:
            """Show recent VOLTTRON log entries.
            
            Args:
                lines: Number of recent log lines to show (default: 20)
            """
            return show_recent_logs()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def check_volttron_installation_tool() -> str:
            """Check if VOLTTRON is properly installed and configured."""
            return check_volttron_installation()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def kill_existing_processes_tool() -> str:
            """Kill any existing VOLTTRON processes (cleanup utility)."""
            return kill_existing_volttron_processes()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def uninstall_all_listeners_tool() -> str:
            """Uninstall all listener agents from the platform."""
            return vctl_uninstall_all_listeners()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def install_listener_agent_tool() -> str:
            """Install a listener agent for monitoring platform messages."""
            return vctl_install_listener_agent()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def verify_agent_uninstalled_tool(agent_name: str, verification_type: str = "comprehensive") -> str:
            """Verify that an agent has been completely uninstalled.
            
            Args:
                agent_name: Name or UUID of the agent to verify
                verification_type: Type of verification (basic, comprehensive)
            """
            return verify_agent_uninstalled(agent_name)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def get_volttron_next_steps_tool() -> str:
            """Get suggested next steps for VOLTTRON development."""
            return get_volttron_next_steps()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def show_formatting_test_tool() -> str:
            """Show a formatting test to verify output display."""
            return show_formatting_test()
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def fetch_webpage_tool(url: str) -> str:
            """Fetch and read content from a webpage, especially useful for documentation.
            
            Args:
                url: The URL to fetch (e.g., GitHub README, documentation page)
            """
            return fetch_webpage_content(url)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def execute_command_tool(command: str) -> str:
            """Execute a safe system command (checking, info gathering).
            
            Args:
                command: The command to execute (only safe read-only commands allowed)
            """
            return execute_system_command(command)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def setup_postgresql_tool(db_name: str = "volttron", db_user: str = "volttron", db_password: str = "volttron") -> str:
            """Set up PostgreSQL database for VOLTTRON historian.
            
            Args:
                db_name: Database name (default: volttron)
                db_user: Database user (default: volttron)
                db_password: Database password (default: volttron)
            """
            return setup_postgresql_database(db_name, db_user, db_password)
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def create_historian_config_tool(historian_type: str = "postgresql", db_config: Optional[dict] = None) -> str:
            """Create historian agent configuration file.
            
            Args:
                historian_type: Type of historian (postgresql, sqlite)
                db_config: Database configuration parameters
            """
            return create_historian_config(historian_type, db_config or {})
        
        # Agent Creator Tools
        @self.agent.tool_plain  # type: ignore[union-attr]
        def start_agent_creator_tool() -> str:
            """Start the guided agent creation wizard.
            
            This tool initiates a step-by-step process to create a custom VOLTTRON agent.
            Use this when the user wants to:
            - Create a new agent
            - Build a custom agent
            - Develop their own agent
            
            Returns:
                Initial greeting and first step prompt
            """
            # Initialize wizard state in conversation history
            conversation_history = self._load_conversation_history()
            
            self.agent_creator_state["agent_creator_active"] = True
            self.agent_creator_state["agent_creator_step"] = 1
            self.agent_creator_state["agent_requirements"] = {}
            
            self._save_conversation_history()
            
            welcome = """
🎉 **Welcome to the VOLTTRON Agent Creator!**

This wizard will help you build a production-ready VOLTTRON agent with:

✨ **Automated Code Generation**
   - Complete agent structure with all required files
   - Extensively commented code explaining VOLTTRON patterns
   - Best practices built-in (error handling, logging, configuration)

🎓 **Educational Guidance**
   - Each step explains VOLTTRON concepts
   - Links to official documentation
   - Examples for common use cases

🤖 **AI-Powered Analysis** (NEW!)
   - Paste any API documentation URL
   - Get implementation recommendations automatically
   - TODO comments guide you through integration

📚 **What You'll Get:**
   - `agent.py` - Your agent code with detailed comments
   - `pyproject.toml` - Package configuration
   - `README.md` - Installation and usage guide
   - `config/default_config.json` - Configuration template
   - `tests/test_agent.py` - Test skeleton

**📖 Reference Documentation:**
https://volttron.readthedocs.io/en/9.0.4/developing-volttron/developing-agents/agent-development.html

💡 **Ready to start?** Type 'yes' or press enter to begin!
"""
            
            # Store that we need to show the process info next
            self.agent_creator_state["show_process_next"] = True
            return welcome
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def agent_creator_next_step_tool(user_input: str) -> str:
            """Advance to the next step in the agent creation wizard.
            
            This tool processes the user's response to the current step and
            provides the next step's prompt.
            
            Args:
                user_input: User's response to current wizard step
                
            Returns:
                Next step prompt or completion message
            """
            conversation_history = self._load_conversation_history()
            
            if not self.agent_creator_state.get("agent_creator_active"):
                return "❌ Agent creator not active. Start with 'create a new agent' first."
            
            current_step = self.agent_creator_state.get("agent_creator_step", 1)
            req_data = self.agent_creator_state.get("agent_requirements", {})
            
            # Collect requirements
            req, next_step, next_prompt = collect_requirements(
                {"agent_requirements": req_data},
                current_step,
                user_input
            )
            
            # If step 3.6 (URL analysis), analyze the URL
            if next_step == 3.6 and req.url:
                try:
                    recommendations = analyze_url_for_agent(req.url, req.description)
                    req.ai_recommendations = recommendations
                    next_prompt = f"✅ **URL Analysis Complete!**\n\n{recommendations[:500]}...\n\n(Full recommendations will be included in generated code)\n\nPress Enter to continue to template selection."
                    # Auto-advance to step 4 after showing recommendations
                    next_step = 4
                except Exception as e:
                    next_prompt = f"⚠️ Could not analyze URL: {str(e)}\n\nContinuing without URL analysis. Press Enter to continue."
                    next_step = 4
            
            # Update conversation history
            self.agent_creator_state["agent_creator_step"] = next_step
            self.agent_creator_state["agent_requirements"] = req.to_dict()
            
            if next_step > 9:
                # All steps complete, trigger scaffolding
                self.agent_creator_state["agent_creator_active"] = False
                self._save_conversation_history()
                
                return next_prompt + "\n\n" + agent_scaffold_tool()
            else:
                self._save_conversation_history()
                return next_prompt
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def agent_scaffold_tool() -> str:
            """Generate agent project files based on collected requirements.
            
            This tool creates the complete agent project structure with:
            - Agent code with extensive comments
            - pyproject.toml for packaging
            - README.md with usage instructions
            - Configuration files
            - Tests
            
            Returns:
                Status message and project location
            """
            conversation_history = self._load_conversation_history()
            req_data = self.agent_creator_state.get("agent_requirements", {})
            
            if not req_data:
                return "❌ No agent requirements found. Start the agent creator first."
            
            req = AgentRequirements.from_dict(req_data)
            
            # Validate name
            valid, msg = validate_agent_name(req.name)
            if not valid:
                return msg
            
            # Validate VIP identity
            valid, msg = validate_vip_identity(req.vip_identity)
            if not valid:
                return msg
            
            try:
                # Generate project
                project_dir = write_agent_project(req)
                
                # Store project directory in conversation history
                self.agent_creator_state["agent_project_dir"] = project_dir
                self.agent_creator_state["agent_package_format"] = req.package_format
                self._save_conversation_history()
                
                return f"""✅ **Agent project created successfully!**

**Location:** `{project_dir}`

**Generated Files:**
- `{req.name.replace('-', '_')}/agent.py` - Main agent code with detailed comments
- `pyproject.toml` - Project metadata and dependencies
- `README.md` - Usage instructions and documentation
- `config/default_config.json` - Default configuration
- `tests/test_agent.py` - Basic unit tests

**Next Steps:**

1. **Review the code** - Check `{project_dir}/{req.name.replace('-', '_')}/agent.py`

⚠️ **Note:** Generated code may require adjustments to work correctly. Please review and test thoroughly.

Ready to build the package? (Proceed automatically...)
3. **Install and test** - We'll install it into VOLTTRON

Ready to build the package? (Proceed automatically...)
"""
            except Exception as e:
                return f"❌ Error creating agent project: {str(e)}"
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def agent_package_tool() -> str:
            """Build the agent package (wheel or editable install).
            
            This tool packages the agent for installation using the format
            specified during creation (wheel or editable).
            
            Returns:
                Build status and package location
            """
            conversation_history = self._load_conversation_history()
            project_dir = self.agent_creator_state.get("agent_project_dir")
            package_format = self.agent_creator_state.get("agent_package_format", "wheel")
            
            if not project_dir:
                return "❌ No agent project found. Create an agent first."
            
            success, message = build_package(project_dir, package_format)
            
            if success:
                # Store build status
                self.agent_creator_state["agent_built"] = True
                self._save_conversation_history()
                
                return message + "\n\n**Ready to install?** Say 'install my agent' or I can do it automatically now."
            else:
                return message
        
        @self.agent.tool_plain  # type: ignore[union-attr]
        def agent_install_tool(start_agent: bool = True) -> str:
            """Install the created agent into VOLTTRON.
            
            This tool installs the agent using vctl and optionally starts it.
            
            Args:
                start_agent: Whether to start the agent after installation (default: True)
                
            Returns:
                Installation status and next steps
            """
            conversation_history = self._load_conversation_history()
            project_dir = self.agent_creator_state.get("agent_project_dir")
            req_data = self.agent_creator_state.get("agent_requirements", {})
            
            if not project_dir:
                return "❌ No agent project found. Create an agent first."
            
            if not req_data:
                return "❌ No agent requirements found."
            
            req = AgentRequirements.from_dict(req_data)
            
            # Check if agent was built
            if not self.agent_creator_state.get("agent_built"):
                # Build first
                success, build_msg = build_package(project_dir, req.package_format)
                if not success:
                    return f"❌ Build failed before installation:\n{build_msg}"
            
            # Install using vctl
            success, message = install_agent_package(
                project_dir,
                req.vip_identity,
                start=start_agent,
                method="vctl"
            )
            
            if success:
                self.agent_creator_state["agent_installed"] = True
                self._save_conversation_history()
                
                return message + f"""

🎉 **Congratulations!** Your agent is now running!

⚠️ **Remember:** This is a template. Review and test the generated code before production use.

**What's next?**

• **Check status:** Say 'show agent status' or 'vctl status'
• **View logs:** Say 'show logs' to see your agent in action
• **Configure:** Edit `{project_dir}/config/default_config.json` and update with `vctl config store`
• **Modify code:** The agent is in `{project_dir}`, edit and reinstall
• **Create another:** Say 'create a new agent' to make another one!

**Agent Details:**
- Name: {req.name}
- VIP Identity: {req.vip_identity}
- Template: {req.template_type}
- Location: {project_dir}
"""
            else:
                return message

    def _register_volttron_tools_on_agent(self, agent):
        """Register VOLTTRON control tools on a specific agent."""
        @agent.tool_plain  # type: ignore[union-attr]
        def start_volttron_tool() -> str:
            """Start the VOLTTRON platform."""
            return start_volttron()
        
        @agent.tool_plain  # type: ignore[union-attr]
        def stop_volttron_tool() -> str:
            """Stop the VOLTTRON platform."""
            return stop_volttron()
        
        @agent.tool_plain  # type: ignore[union-attr]
        def check_volttron_status_tool() -> str:
            """Check VOLTTRON platform status and show recent logs."""
            return check_volttron_status()
            
        @agent.tool_plain  # type: ignore[union-attr]
        def simple_volttron_status_check_tool() -> str:
            """Simple check if VOLTTRON is running with minimal output."""
            return simple_volttron_status_check()
        
        @agent.tool_plain  # type: ignore[union-attr]
        def list_agents_tool() -> str:
            """List all installed VOLTTRON agents."""
            return vctl_list_agents()
        
        @agent.tool_plain  # type: ignore[union-attr]
        def install_agent_tool(agent_name: str) -> str:
            """Install a VOLTTRON agent by name."""
            return vctl_install_agent(agent_name)
    
        
        @agent.tool_plain  # type: ignore[union-attr]
        def start_agent_creator_tool() -> str:
            """Start the agent creation wizard to build a custom VOLTTRON agent.
            
            Use this tool when the user wants to create a new agent, build a custom agent,
            or develop their own agent for VOLTTRON.
            """
            return self._start_agent_creator_impl()
        
    def _get_volttron_system_prompt(self):
        """Get the system prompt for VOLTTRON AI assistant."""
        return (
            "You are a VOLTTRON AI Assistant. Be extremely concise and direct.\n\n"
            "RESPONSE STYLE:\n"
            "- Keep responses SHORT (1-2 sentences max)\n"
            "- NO detailed explanations unless asked\n"
            "- NO numbered lists unless requested\n" 
            "- NO \"I'll do X for you\" - just do it\n"
            "- NO progress reports - just show final status\n\n"
            "INSTALLATION COMMANDS - ABSOLUTELY MANDATORY:\n"
            "============================================\n"
            "When user says ANYTHING like 'install X' or 'install the X' YOU MUST:\n"
            "1. Extract package name (e.g., 'volttron-lib-modbustk-driver')\n"
            "2. IMMEDIATELY call smart_install_package(package_name)\n"
            "3. DO NOT respond with text - ONLY call the function\n"
            "4. NO options, NO menus, NO questions - JUST CALL THE FUNCTION\n\n"
            "EXAMPLE:\n"
            "User: 'install volttron-lib-modbustk-driver'\n"
            "You: [call smart_install_package('volttron-lib-modbustk-driver')] <-- DO THIS\n"
            "You: NOT 'I can help you install...' <-- NEVER DO THIS\n\n"
            "The smart_install_package function handles EVERYTHING automatically:\n"
            "- Detects if it's a library or agent\n"
            "- Uses vctl for VOLTTRON packages\n"
            "- Uses pip for fake driver and other Python libraries\n"
            "- Returns success/failure message\n\n"
            "WEBPAGE AND DOCUMENTATION:\n"
            "- When asked to read a URL or webpage, use fetch_webpage_tool\n"
            "- Especially for GitHub repositories and documentation\n"
            "- Extract installation steps, configuration details, or instructions from the content\n\n"
            "SYSTEM COMMANDS:\n"
            "- Use execute_command_tool for safe read-only commands (which, ps, ls, cat, etc.)\n"
            "- For PostgreSQL setup, use setup_postgresql_tool to guide the user\n"
            "- For historian configuration, use create_historian_config_tool\n\n"
            "INTELLIGENT COMMAND DISCOVERY:\n"
            "- When you don't know a vctl command, use 'run_vctl_help' tool\n"
            "- Or use 'intelligent_vctl_command_discovery' to automatically find and run the right command\n"
            "- Learn from help output and pick the best command\n"
            "- Keep context from previous help queries\n\n"
            "CONVERSATIONAL AGENT CREATION - NEW WORKFLOW:\n"
            "When user wants to create an agent:\n"
            "\n"
            "1. **UNDERSTAND THE INTENT**: Ask what the agent should do (if not clear)\n"
            "   - Example: 'I want to create an agent' → Ask: 'What would you like the agent to do?'\n"
            "\n"
            "2. **INTELLIGENT TEMPLATE SELECTION**: Based on user's description, automatically choose:\n"
            "   - create_minimal_agent_tool() - Learning, testing, simple tasks\n"
            "   - create_template_agent_tool() - Monitoring, listening to topics, event-driven\n"
            "   - create_driver_agent_tool() - Polling devices, scheduled data collection\n"
            "   - create_historian_agent_tool() - Recording data, logging to database\n"
            "\n"
            "3. **EXTRACT PARAMETERS FROM DESCRIPTION**:\n"
            "   - Agent name from the purpose (e.g., 'temperature monitor' → 'temperature-monitor')\n"
            "   - Topics from what it monitors (e.g., 'monitor devices' → 'devices/#')\n"
            "   - Device address for drivers (e.g., 'poll BACnet device' → device address)\n"
            "   - Database type for historians (e.g., 'save to database' → 'sqlite')\n"
            "\n"
            "4. **ASK ONLY IF CRITICAL INFO MISSING**: Don't ask for every detail\n"
            "   - If user says 'monitor temperature sensors' → You know: listener, devices/temperature/#\n"
            "   - If user says 'test agent' → You know: minimal, simple name\n"
            "   - Only ask if truly ambiguous\n"
            "\n"
            "5. **CREATE AND REPORT**: Call the appropriate tool and show results\n"
            "\n"
            "**EXAMPLES:**\n"
            "User: 'I want to build an agent' → Ask: 'What would you like the agent to do?'\n"
            "User: 'Monitor temperature' → [Call create_template_agent_tool('temp-monitor', 'Monitors temperature data', 'devices/temperature/#')]\n"
            "User: 'Poll BACnet every 30s' → [Call create_driver_agent_tool('bacnet-driver', 'Polls BACnet', 'devices/bacnet/1', 30)]\n"
            "User: 'Log data to database' → [Call create_historian_agent_tool('device-historian', 'Logs data', 'devices/#', 'sqlite')]\n"
            "\n"
            "**KEY PRINCIPLES:**\n"
            "- Be conversational, infer from context, use template tools directly\n"
            "- Fill in reasonable defaults, ask only when necessary\n"
            "- Use start_agent_creator_tool ONLY if user asks for 'wizard' or 'step-by-step'\n"
            "\n"
            "TOOLS AVAILABLE:\n"
            "- start_volttron_tool: Start VOLTTRON\n"
            "- stop_volttron_tool: Stop VOLTTRON\n"
            "- check_volttron_status_tool: Check status\n"
            "- vctl_status: Get agent status\n"
            "- smart_install_package: Flexible installation (use this for 'install X' requests)\n"
            "- fetch_webpage_tool: Fetch and read webpage content (use for URLs, especially GitHub)\n"
            "- execute_command_tool: Execute safe system commands\n"
            "- setup_postgresql_tool: Guide PostgreSQL database setup\n"
            "- create_historian_config_tool: Create historian configuration\n"
            "- run_vctl_help: Get vctl help (general or specific command)\n"
            "- intelligent_vctl_command_discovery: Auto-discover and run vctl commands\n"
            "- start_agent_creator_tool: Create custom VOLTTRON agents (use for 'create agent' requests)\n"
            "- agent_creator_next_step_tool: Advance through agent creation wizard\n"
            "- agent_scaffold_tool: Generate agent project files\n"
            "- agent_package_tool: Build agent package (wheel or editable)\n"
            "- agent_install_tool: Install agent to VOLTTRON\n"
            "- install_listener_agent_tool: Install listener\n"
            "- list_agents_tool: List agents\n"
            "- And other VOLTTRON management tools\n\n"
            "EXECUTE COMMANDS DIRECTLY - don't explain what you'll do, just do it and report the result briefly.\n"
            "When uncertain about a command, use intelligent_vctl_command_discovery to figure it out.\n"
            "When given a URL, ALWAYS use fetch_webpage_tool to read it first before responding."
        )

    def _setup_agent(self):
        """Setup the Pydantic-AI agent with the specified model or custom webapp if configured."""
        ai_webapp_url = os.getenv("AI_WEBAPP_URL")
        ai_api_key = os.getenv("AI_API_KEY")
        
        try:
            if ai_webapp_url and ai_api_key:
                self.custom_client = openai.OpenAI(
                    api_key=ai_api_key,
                    base_url=ai_webapp_url,
                    timeout=120.0
                )
                self.custom_model = self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
                self.agent = self._create_agent_with_tools()
            elif self.model_name.startswith("ollama:"):
                if Agent is not None:
                    from pydantic_ai.models.openai import OpenAIChatModel
                    from pydantic_ai.providers.ollama import OllamaProvider
                    model_id = self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
                    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
                    print(f"Connecting to Ollama at: {ollama_base_url}")
                    print(f"Using model: {model_id}")
                    self.agent = Agent(
                        OpenAIChatModel(
                            model_id,
                            provider=OllamaProvider(base_url=ollama_base_url)
                        ),
                        system_prompt=self._get_volttron_system_prompt()
                    )
                    self._register_volttron_tools()
                else:
                    print("Ollama support requires Pydantic AI")
                    self.agent = None
            else:
                if Agent is not None:
                    self.agent = Agent(
                        self.model_name,
                        system_prompt=self._get_volttron_system_prompt()
                    )
                    self._register_volttron_tools()
                else:
                    print("Using OpenAI function calling (Pydantic AI not available)")
                    self.agent = None
            
            print(f"✓ AI service initialized with model: {self.model_name}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI model '{self.model_name}': {str(e)}")
    
    async def generate_response(self, message: str) -> str:
        """Generate a response to the user's message using function tools."""
        try:
            # Handle blank/empty messages (but allow them for wizard)
            if (not message or not message.strip()) and not self.agent_creator_state.get("agent_creator_active"):
                return "👋 I'm here! What would you like to do?"
            
            is_reversal, reversal_response = self._detect_context_reversal(message)
            if is_reversal:
                return reversal_response
            
            # WIZARD MODE AUTO-HANDLING: Force immediate tool call when wizard is active
            if self.agent_creator_state.get("agent_creator_active"):
                print(f"🧙 WIZARD AUTO-MODE: Calling next_step with input: '{message}'")
                return self._agent_creator_next_step_impl(message)
            
            if hasattr(self, 'awaiting_reversal_confirmation') and self.awaiting_reversal_confirmation:
                message_lower = message.lower().strip()
                if message_lower in ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay']:
                    self.awaiting_reversal_confirmation = False
                    if self.last_action == "install_agent":
                        agent_type = self.last_action_details.get("agent_type", "agent") if self.last_action_details else "agent"
                        return self.call_function_tool("vctl_uninstall_agent", {"agent_uuid_or_tag": agent_type})
                    elif self.last_action == "start_volttron":
                        return self.call_function_tool("stop_volttron", {})
                    elif self.last_action == "stop_volttron":
                        return self.call_function_tool("start_volttron", {})
                    elif self.last_action == "uninstall_agent":
                        agent_type = self.last_action_details.get("agent_type", "agent") if self.last_action_details else "agent"
                        return f"To reinstall the {agent_type}, please tell me which agent you'd like to install. You can say 'install listener' or 'what agents can I install' to see options."
                    else:
                        return "I'm not sure how to reverse that action. What would you like me to do?"
                elif message_lower in ['no', 'n', 'nope', 'cancel', 'nevermind']:
                    self.awaiting_reversal_confirmation = False
                    return "No problem! I'll leave everything as is. What would you like to do next?"
            
            # Let the AI handle most requests through function tools
            print(f"DEBUG generate_response: Processing message: '{message}'")
            direct_result = self._handle_direct_command(message)
            if direct_result:
                return direct_result
            
            if self.agent:
                return await self._generate_response_with_pydantic_ai(message)
            
            return await self._generate_ai_response_with_tools(message)
            
        except Exception as e:
            print(f"Error in generate_response: {e}")
            return f"❌ I encountered an error: {str(e)}. Please try again or rephrase your request."
    
    async def _generate_response_with_pydantic_ai(self, message: str) -> str:
        """Generate response using Pydantic AI agent with proper tool support."""
        try:
            if not self.agent:
                raise Exception("Pydantic AI agent not available")
            
            
            conversation_messages = []
            for msg in self.conversation_history[-10:]:  
                if msg['role'] == 'user':
                    conversation_messages.append(f"User: {msg['content']}")
                elif msg['role'] == 'assistant':
                    conversation_messages.append(f"Assistant: {msg['content']}")
            
          
            context_message = ""
            if conversation_messages:
                context_message = f"\n\nRecent conversation:\n" + "\n".join(conversation_messages)
            
           
            result = await self.agent.run(message + context_message)
            
          
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": result.output})
            self._save_conversation_history()
            
            return result.output
            
        except Exception as e:
            print(f"Error in Pydantic AI response generation: {e}")
           
            return await self._generate_ai_response_with_tools(message)
    
    async def _generate_ai_response_with_tools(self, message: str) -> str:
        """Generate AI response with function tools support."""
        try:
            is_claude_model = "claude" in self.model_name.lower() or "anthropic" in self.model_name.lower()
            
            messages = [
                {
                    "role": "system", 
                    "content": self.system_prompt + self._get_enhanced_system_prompt()
                }
            ]
            
            for msg in self.conversation_history[-10:]: 
                messages.append(msg)
            
            messages.append({"role": "user", "content": message})
            
            # Get tools in the new OpenAI format
            tools = self.get_tools_schemas()
            
            if is_claude_model:
                # Claude models via PNNL API support tools in OpenAI format
                if self.custom_client:
                    response = self.custom_client.chat.completions.create(
                        model=self.custom_model,
                        messages=messages,  # type: ignore[arg-type]
                        tools=tools,  # type: ignore[arg-type]
                        tool_choice="auto",
                        max_tokens=1000,
                        temperature=0.7
                    )
                else:
                    client = openai.OpenAI()
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,  # type: ignore[arg-type]
                        tools=tools,  # type: ignore[arg-type]
                        tool_choice="auto",
                        max_tokens=1000,
                        temperature=0.7
                    )
                
                message_response = response.choices[0].message
                
                # Check if Claude called a tool
                if message_response.tool_calls:
                    tool_call = message_response.tool_calls[0]
                    function_name = tool_call.function.name  # type: ignore[attr-defined]
                    function_args = json.loads(tool_call.function.arguments)  # type: ignore[attr-defined]
                    
                    function_result = self.call_function_tool(function_name, function_args)
                    
                    # Get final response with function result
                    follow_up_messages = messages + [
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": tool_call.function.arguments  # type: ignore[attr-defined]
                                }
                            }]
                        },
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": function_result
                        }
                    ]
                    
                    if self.custom_client:
                        final_response = self.custom_client.chat.completions.create(
                            model=self.custom_model,
                            messages=follow_up_messages,  # type: ignore[arg-type]
                            tools=tools,  # type: ignore[arg-type]
                            tool_choice="auto",
                            max_tokens=1000,
                            temperature=0.7
                        )
                    else:
                        client = openai.OpenAI()
                        final_response = client.chat.completions.create(
                            model=self.model_name,
                            messages=follow_up_messages,  # type: ignore[arg-type]
                            tools=tools,  # type: ignore[arg-type]
                            tool_choice="auto",
                            max_tokens=1000,
                            temperature=0.7
                        )
                    
                    ai_response = final_response.choices[0].message.content
                else:
                    ai_response = message_response.content
                
            else:
                # Non-Claude models: use old functions format for backward compatibility
                function_schemas = self.get_function_schemas()
                
                if self.custom_client:
                    response = self.custom_client.chat.completions.create(
                        model=self.custom_model,
                        messages=messages,  # type: ignore[arg-type]
                        functions=function_schemas,  # type: ignore[arg-type]
                        function_call="auto",
                        max_tokens=1000,
                        temperature=0.7
                    )
                else:
                    client = openai.OpenAI()
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,  # type: ignore[arg-type]
                        functions=function_schemas,  # type: ignore[arg-type]
                        function_call="auto",
                        max_tokens=1000,
                        temperature=0.7
                    )
                
                message_response = response.choices[0].message
                
                if message_response.function_call:
                    function_name = message_response.function_call.name
                    function_args = json.loads(message_response.function_call.arguments)
                    
                    function_result = self.call_function_tool(function_name, function_args)
                    
                    follow_up_messages = messages + [
                        {
                            "role": "assistant",
                            "content": None,
                            "function_call": {
                                "name": function_name,
                                "arguments": message_response.function_call.arguments
                            }
                        },
                        {
                            "role": "function",
                            "name": function_name,
                            "content": function_result
                        }
                    ]
                    
                    if self.custom_client:
                        final_response = self.custom_client.chat.completions.create(
                            model=self.custom_model,
                            messages=follow_up_messages,  # type: ignore[arg-type]
                            tools=tools,  # type: ignore[arg-type]
                            tool_choice="auto",
                            max_tokens=1000,
                            temperature=0.7
                        )
                    else:
                        client = openai.OpenAI()
                        final_response = client.chat.completions.create(
                            model=self.model_name,
                            messages=follow_up_messages,  # type: ignore[arg-type]
                            tools=tools,  # type: ignore[arg-type]
                            tool_choice="auto",
                            max_tokens=1000,
                            temperature=0.7
                        )
                    
                    ai_response = final_response.choices[0].message.content
                else:
                    ai_response = message_response.content
            
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            self._save_conversation_history()
            
            return ai_response or ""
            
        except Exception as e:
            print(f"Error in AI response generation: {e}")
            fallback_result = self._handle_direct_command(message)
            if fallback_result:
                return f"ℹ️ **Using fallback command handler** (AI connection failed)\n\n{fallback_result}"
            return f"❌ I encountered an error: {str(e)}. Please try again."
    
    def _process_claude_response_for_commands(self, ai_response: str, user_message: str) -> str:
        """Process Claude response and try to execute any VOLTTRON commands mentioned."""
        try:
            
            command_patterns = {
                r"vctl\s+status": "vctl_status",
                r"start.*volttron": "start_volttron",
                r"start.*volltron": "start_volttron",
                r"stop.*volttron": "stop_volttron",
                r"stop.*volltron": "stop_volttron",
                r"list\s+(all\s+)?agents(?!\s+\w)": "vctl_list_agents",
                r"install.*(the|a)?.*platform.*driver": "vctl_install_platform_driver",
                r"install.*(the|a)?.*listener.*agent": "vctl_install_listener_agent",
                
                r"show.*logs": "show_recent_logs",
                r"health.*check": "vctl_health"
            }
            
           
            if any(phrase in user_message.lower() for phrase in [
                'what agents are running', 'which agents are running', 'show running agents',
                'list running agents', 'show agents running', 'tell me running agents'
            ]):
               
                return self.call_function_tool("vctl_status", {})
            
         
            text_to_check = (user_message + " " + ai_response).lower()
            
         
            executed_commands = []
            for pattern, function_name in command_patterns.items():
                if re.search(pattern, text_to_check):
                    try:
                        if function_name in self.function_tools:
                         
                            func = self.function_tools[function_name]["function"]
                            result = func()
                            
                            executed_commands.append(f"\n{result}")
                                    
                    except Exception as e:
                        executed_commands.append(f"\n❌ {function_name} error: {str(e)}")
            
           
            if executed_commands:
                ai_response += "".join(executed_commands)
            
            return ai_response
            
        except Exception as e:
            print(f"Error processing Claude response: {e}")
            return ai_response
    
    def _get_enhanced_system_prompt(self) -> str:
        """Get enhanced system prompt with function tools information."""
        return """

FUNCTION TOOLS AVAILABLE:
You have access to the following VOLTTRON function tools:
- start_volttron: Start the VOLTTRON platform
- stop_volttron: Stop the VOLTTRON platform  
- check_volttron_status: Check if VOLTTRON is running
- vctl_status: Get status of all installed agents
- vctl_install_listener_agent: Install listener agent
- vctl_uninstall_agent: Uninstall an agent by UUID/tag
- vctl_start_agent: Start an agent by UUID/tag
- vctl_stop_agent: Stop an agent by UUID/tag
- verify_agent_uninstalled: Verify agent removal
- list_available_agents: List all available agents

IMPORTANT GUIDELINES:
1. Use function tools for VOLTTRON operations when appropriate
2. Always provide clear, helpful responses
3. Track user actions for contextual reversal ("I changed my mind")
4. Verify agent operations when requested
5. Be conversational and helpful

When users ask for VOLTTRON operations, use the appropriate function tools."""

    def _handle_direct_command(self, message: str) -> Optional[str]:
        """Handle only critical direct commands that require immediate responses.
        Everything else should go to the AI for intelligent processing."""
        message_lower = message.lower().strip()
        
        # WIZARD MODE: Always handle wizard navigation directly
        if self.agent_creator_state.get("agent_creator_active"):
            # Let wizard commands through to AI, but handle immediate navigation
            if message_lower in ['cancel wizard', 'stop wizard', 'exit wizard']:
                agent_name = self.agent_creator_state.get("agent_requirements", {}).get("name", "your agent")
                self.agent_creator_state["agent_creator_active"] = False
                self.agent_creator_state["agent_creator_step"] = 1
                self.agent_creator_state["agent_requirements"] = {}
                self._save_conversation_history()
                return f"""✅ **Agent Creator Cancelled**

Agent creation for "{agent_name}" has been cancelled.

Type **"create an agent"** if you want to start fresh."""
        
        # HELP: Show available commands (exact match only)
        if message_lower in ['help', 'commands']:
            return """📚 **VOLTTRON AI Assistant**

I can help you with:
• Starting/stopping VOLTTRON platform
• Creating, installing, and managing agents  
• Checking agent status
• Installing packages
• Viewing logs

Just ask me naturally! For example:
• "start volttron"
• "create an agent"
• "what agents are running?"
• "install listener agent"

I'm powered by AI, so feel free to ask questions in your own words!"""
        
        # Only return None - let the AI handle everything else!
        # The AI has access to all the tools and can make intelligent decisions
        return None

