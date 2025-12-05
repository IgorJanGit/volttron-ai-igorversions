from typing import Optional, Dict, List, Any, Tuple, Callable
import os
import re
import json
import openai
import inspect

try:
    from pydantic_ai_slim import Agent
except ImportError:
    try:
        from pydantic_ai import Agent
    except ImportError:
        print("Warning: Pydantic AI not available. Using OpenAI function calling only.")
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
    configure_fake_driver, start_fake_driver, vctl_install_lib,
    vctl_start_all_agents, vctl_force_remove_agent, run_vctl_help, intelligent_vctl_command_discovery,
    smart_install_package, search_github_for_agent, install_agent_from_github,
    list_volttron_packages, list_running_agents, install_from_github_smart, list_all_installations,
    list_repository_packages, fetch_webpage_content, execute_system_command, 
    setup_postgresql_database, create_historian_config
)

if Agent is not None:
    agent = Agent(
        model=None,
        system_prompt=""  # Will be set dynamically
    )
else:
    agent = None

if agent:
    @agent.tool_plain
    def start_volttron_tool() -> str:
        """Start the VOLTTRON platform."""
        return start_volttron()

    @agent.tool_plain  
    def stop_volttron_tool() -> str:
        """Stop the VOLTTRON platform."""
        return stop_volttron()

    @agent.tool_plain
    def check_volttron_status_tool() -> str:
        """Check if VOLTTRON platform is running."""
        return check_volttron_status()

    @agent.tool_plain
    def get_vctl_status_tool() -> str:
        """Get current status of all installed agents."""
        return vctl_status()

    @agent.tool_plain
    def vctl_status_detailed_tool() -> str:
        """Get detailed status information about VOLTTRON agents."""
        return vctl_status_detailed()

    @agent.tool_plain
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
                    print(f"DEBUG list_agents_tool returning successful status output: {output}")
                    return f"🤖 **Installed VOLTTRON Agents:**\n\n```\n{output}\n```"
                else:
                    print("DEBUG list_agents_tool: Empty output from vctl status")
                    return "No agents are currently installed."
            else:
                error = result.stderr or result.stdout or "Unknown error"
                print(f"DEBUG list_agents_tool command failed: {error}")
                return f"Error listing agents: {error}"
        except Exception as e:
            print(f"DEBUG list_agents_tool exception: {str(e)}")
            return f"Failed to list agents: {str(e)}"

    @agent.tool_plain
    def start_agent_tool(agent_uuid: str) -> str:
        """Start a VOLTTRON agent by UUID.
        
        Args:
            agent_uuid: The UUID or tag of the agent to start
        """
        return vctl_start_agent(agent_uuid)

    @agent.tool_plain
    def stop_agent_tool(agent_uuid: str) -> str:
        """Stop a VOLTTRON agent by UUID.
        
        Args:
            agent_uuid: The UUID or tag of the agent to stop
        """
        return vctl_stop_agent(agent_uuid)

    @agent.tool_plain
    def vctl_health_tool() -> str:
        """Check VOLTTRON platform health."""
        return vctl_health()

    @agent.tool_plain
    def install_platform_driver_tool() -> str:
        """Install the VOLTTRON platform driver agent."""
        return vctl_install_platform_driver()

    @agent.tool_plain
    def show_recent_logs_tool() -> str:
        """Show recent VOLTTRON logs."""
        return show_recent_logs()

    @agent.tool_plain
    def check_volttron_installation_tool() -> str:
        """Check if VOLTTRON is properly installed."""
        return check_volttron_installation()

    @agent.tool_plain
    def kill_existing_processes_tool() -> str:
        """Kill any existing VOLTTRON processes."""
        return kill_existing_volttron_processes()

    @agent.tool_plain
    def uninstall_agent_tool(agent_uuid: str) -> str:
        """Uninstall a VOLTTRON agent by UUID.
        
        Args:
            agent_uuid: The UUID or tag of the agent to uninstall
        """
        return vctl_uninstall_agent(agent_uuid)

    @agent.tool_plain
    def install_listener_agent_tool() -> str:
        """Install a VOLTTRON listener agent."""
        return vctl_install_listener_agent()

    @agent.tool_plain
    def install_agent_tool(agent_name: str) -> str:
        """Install a VOLTTRON agent by name.
        
        Args:
            agent_name: The name of the agent to install
        """
        return vctl_install_agent(agent_name)

    @agent.tool_plain
    def install_volttron_tool() -> str:
        """Install VOLTTRON using pip and set up the environment."""
        return install_volttron_with_pip()

    @agent.tool_plain
    def pip_uninstall_tool(package_name: str) -> str:
        """Uninstall a Python package using pip.
        
        Args:
            package_name: The name of the package to uninstall (e.g., 'volttron-listener')
        """
        return pip_uninstall_package(package_name, force=True)
    
    @agent.tool_plain
    def pip_install_tool(package_name: str, upgrade: bool = False) -> str:
        """Install a Python package using pip.
        
        Args:
            package_name: The name of the package to install (e.g., 'volttron-platform-driver')
            upgrade: Whether to add the --upgrade flag
        """
        return pip_install_package(package_name, upgrade)

    @agent.tool_plain
    def pip_list_tool() -> str:
        """List all installed Python packages."""
        return pip_list_packages()

    @agent.tool_plain
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

    @agent.tool_plain
    def install_fake_driver_library_tool() -> str:
        """Install the volttron-lib-fake-driver package for testing and development."""
        return install_fake_driver_library()

    @agent.tool_plain
    def vctl_install_lib_tool(library_name: str, confirm: bool = True) -> str:
        """Install a VOLTTRON library package using pip (works without VOLTTRON running).
        
        This is an alternative to 'vctl install-lib' that works without VOLTTRON running.
        Use this when user wants to install any VOLTTRON library package.
        
        Args:
            library_name: Name of the library to install (e.g., 'volttron-lib-modbustk-driver', 'volttron-lib-fake-driver')
            confirm: Whether to confirm before installing (default: True)
        
        Returns:
            Status message about the installation
        """
        return vctl_install_lib(library_name, confirm)

    @agent.tool_plain
    def show_fake_driver_logs_tool(num_lines: int = 50) -> str:
        """Show recent fake driver data from VOLTTRON logs.
        
        Args:
            num_lines: Number of recent log lines to check (default: 50)
        """
        return show_fake_driver_logs(num_lines)

    @agent.tool_plain
    def check_fake_driver_status_tool() -> str:
        """Check if the fake driver is actively publishing data by examining recent logs.
        
        This checks actual log activity to determine if fake driver is working, not just installation status.
        Returns clear status information based on real-time log analysis.
        """
        return check_fake_driver_status()

    @agent.tool_plain
    def watch_fake_driver_logs_tool() -> str:
        """Get instructions for watching fake driver logs in real-time using tail -f."""
        return watch_fake_driver_logs()

    @agent.tool_plain
    def setup_fake_driver_complete_tool() -> str:
        """Complete automated setup of fake driver - installs library, platform driver, configures, and starts everything.
        
        This is the ONE COMMAND to fully set up the fake driver so users can immediately see fake data in logs.
        Use this when user wants to 'set up fake driver' or 'install fake driver' - it does EVERYTHING.
        """
        return setup_fake_driver_complete()

    @agent.tool_plain
    def force_remove_agent_tool(agent_tag_or_uuid: str) -> str:
        """Force remove an agent by tag or UUID using aggressive removal methods.
        
        Use this tool when standard removal fails or times out. This tool performs
        multiple removal strategies to ensure the agent is completely removed from
        the system, including direct file manipulation if standard removal fails.
        
        Args:
            agent_tag_or_uuid: The tag or UUID of the agent to force remove
        """
        return vctl_force_remove_agent(agent_tag_or_uuid)
        
    @agent.tool_plain
    def start_all_agents_tool() -> str:
        """Start all available VOLTTRON agents that are not currently running."""
        return vctl_start_all_agents()

    @agent.tool_plain
    def search_github_for_agent_tool(agent_name: str) -> str:
        """Search eclipse-volttron GitHub organization for agent repositories when local agent not found.
        
        Args:
            agent_name: The name of the agent to search for on GitHub
        """
        return search_github_for_agent(agent_name)

    @agent.tool_plain
    def install_agent_from_github_tool(repo_url: str) -> str:
        """Install a VOLTTRON agent from a GitHub repository URL.
        
        Args:
            repo_url: The GitHub repository URL or clone URL to install from
        """
        return install_agent_from_github(repo_url)

    @agent.tool_plain
    def install_from_github_smart_tool(repo_url: str) -> str:
        """Intelligently analyze and install from any GitHub repository.
        
        Reads the README, detects installation method (pip, poetry, ansible, vctl, etc.)
        and provides appropriate installation instructions or executes installation.
        
        Use this when the installation method is unknown or for non-standard repos.
        
        Args:
            repo_url: The GitHub repository URL
        """
        return install_from_github_smart(repo_url)

    @agent.tool_plain
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

    @agent.tool_plain
    def list_repository_packages_tool() -> str:
        """List all VOLTTRON packages in the current repository's virtual environment.
        
        Shows packages installed via pip in THIS workspace (not system VOLTTRON).
        Useful for tracking what's installed during development when installing many packages.
        Includes version numbers and separates VOLTTRON packages from related tools.
        """
        return list_repository_packages()

    @agent.tool_plain
    def run_vctl_help_tool(subcommand: str = None) -> str:
        """Run vctl --help to learn about available commands.
        
        Use this tool when you don't know what vctl command to use or need to learn
        about available options. Can get general help or help for a specific subcommand.
        
        Args:
            subcommand: Optional subcommand to get help for (e.g., 'install', 'status', 'config')
        """
        return run_vctl_help(subcommand)

    @agent.tool_plain
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
        self.last_numbered_options = {}
        self.fake_driver_setup_state = "not_started"  # Track fake driver setup progress
        self.volttron_checked = False
        self.conversation_file = "conversation_history.json"  # File to persist conversation
        self.last_action = None
        self.last_action_details = {}
        self.function_tools = {}
        self.system_prompt = self._get_volttron_system_prompt()
        
        if self.agent:
            try:
                self.agent.model = model_name
                self.agent.system_prompt = self.system_prompt
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
            "vctl_install_lib": {
                "function": vctl_install_lib,
                "schema": {
                    "name": "vctl_install_lib",
                    "description": "Install a VOLTTRON library package using pip (works without VOLTTRON running). This is an alternative to 'vctl install-lib' command. Use this for installing any VOLTTRON library like volttron-lib-modbustk-driver, volttron-lib-bacnet-driver, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "library_name": {
                                "type": "string",
                                "description": "Name of the VOLTTRON library to install (e.g., 'volttron-lib-modbustk-driver', 'volttron-lib-fake-driver')"
                            },
                            "confirm": {
                                "type": "boolean",
                                "description": "Whether to confirm before installing (default: True)",
                                "default": True
                            }
                        },
                        "required": ["library_name"]
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
            }
        }
        
    def get_function_schemas(self) -> List[Dict]:
        """Get OpenAI function schemas for all registered tools."""
        return [tool["schema"] for tool in self.function_tools.values()]
    
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
            "never mind", "nevermind", "cancel that", "undo that", "reverse that",
            "stop that", "wait, don't", "wait don't", "actually stop", "actually, stop",
            "on second thought", "forget that", "abort", "cancel", "undo", "go back",
            "dont do that", "don't do that", "not what i want", "that's not what i want",
            "that's wrong", "wait", "hold on", "scratch that", "nope", "no wait",
            "actually", "instead", "rather", "i don't want", "don't want that"
        ]
        
        for phrase in reversal_phrases:
            if phrase in message_lower:
                self.awaiting_reversal_confirmation = True
                
                if self.last_action == "start_volttron":
                    return True, "It sounds like you want to stop VOLTTRON instead. Should I stop the VOLTTRON platform for you?"
                elif self.last_action == "stop_volttron":
                    return True, "It sounds like you want to start VOLTTRON instead. Should I start the VOLTTRON platform for you?"
                elif self.last_action == "install_agent":
                    agent_type = self.last_action_details.get("agent_type", "the agent")
                    agent_id = self.last_action_details.get("agent_id", "")
                    if agent_id:
                        return True, f"It sounds like you want to uninstall the {agent_type} agent (ID: {agent_id}) that was just installed. Should I uninstall it for you?"
                    else:
                        return True, f"It sounds like you want to uninstall the {agent_type} agent that was just installed. Should I uninstall it for you?"
                elif self.last_action == "uninstall_agent":
                    agent_type = self.last_action_details.get("agent_type", "agent") 
                    return True, f"It sounds like you want to reinstall the {agent_type} agent. Should I install it again for you?"
                elif self.last_action == "create_config":
                    config_type = self.last_action_details.get("config_type", "configuration")
                    return True, f"It sounds like you want to remove the {config_type} files that were just created. Should I delete them for you?"
                elif self.last_action:
                    return True, f"It sounds like you want to reverse the last action ({self.last_action}). What would you like me to do instead?"
                else:
                    recent_action_suggestion = self._analyze_conversation_for_reversal()
                    if recent_action_suggestion:
                        self.awaiting_reversal_confirmation = True
                        return True, recent_action_suggestion
                    else:
                        self.awaiting_reversal_confirmation = False
                        return True, "I noticed you changed your mind, but I'm not sure what to reverse. Can you tell me what you'd like me to help you with instead?"
        
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
    
    def _track_action(self, action: str, details: dict = None):
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
            words = message.lower().split()
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
            words = message.lower().split()
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
            agent = Agent(
                self.model_name,
                system_prompt=self._get_volttron_system_prompt()
            )
            self._register_volttron_tools_on_agent(agent)
            return agent
        else:
            return None
    
    def _register_volttron_tools(self):
        """Register VOLTTRON control tools with the agent using Pydantic AI's tool system."""
        @self.agent.tool_plain
        def start_volttron_tool() -> str:
            """Start the VOLTTRON platform."""
            return start_volttron()
        
        @self.agent.tool_plain
        def stop_volttron_tool() -> str:
            """Stop the VOLTTRON platform."""
            return stop_volttron()
        
        @self.agent.tool_plain
        def check_volttron_status_tool() -> str:
            """Check VOLTTRON platform status and show recent logs."""
            return check_volttron_status()
            
        @self.agent.tool_plain
        def simple_volttron_status_check_tool() -> str:
            """Simple check if VOLTTRON is running with minimal output."""
            return simple_volttron_status_check()
        
        @self.agent.tool_plain
        def get_vctl_status_tool() -> str:
            """Get VOLTTRON platform status using vctl status command."""
            return vctl_status()
        
        @self.agent.tool_plain
        def read_volttron_log_tool(num_lines: int = 10) -> str:
            """Read recent VOLTTRON log entries.
            
            Args:
                num_lines: Number of recent log lines to read (default: 10)
            """
            return read_volttron_log(num_lines)
        
        @self.agent.tool_plain
        def list_agents_tool() -> str:
            """List all installed VOLTTRON agents."""
            return vctl_list_agents()
        
        @self.agent.tool_plain
        def start_agent_tool(agent_uuid: str) -> str:
            """Start a VOLTTRON agent by UUID.
            
            Args:
                agent_uuid: The UUID of the agent to start
            """
            return vctl_start_agent(agent_uuid)
        
        @self.agent.tool_plain
        def stop_agent_tool(agent_uuid: str) -> str:
            """Stop a VOLTTRON agent by UUID.
            
            Args:
                agent_uuid: The UUID of the agent to stop
            """
            return vctl_stop_agent(agent_uuid)
        
        @self.agent.tool_plain
        def install_agent_tool(agent_name: str) -> str:
            """Install a VOLTTRON agent by name.
            
            Args:
                agent_name: Name of the agent to install (e.g., 'listener', 'platform-driver')
            """
            return vctl_install_agent(agent_name)
        
        @self.agent.tool_plain
        def uninstall_agent_tool(agent_uuid: str) -> str:
            """Uninstall a VOLTTRON agent by UUID (stop and remove).
            
            Args:
                agent_uuid: The UUID of the agent to uninstall
            """
            return vctl_uninstall_agent(agent_uuid)
        
        @self.agent.tool_plain
        def get_volttron_help_tool() -> str:
            """Get detailed VOLTTRON installation and setup help."""
            return get_detailed_installation_help()
        
        @self.agent.tool_plain
        def list_available_agents_tool() -> str:
            """Show all available VOLTTRON agents that can be installed."""
            return list_available_agents()
        
        @self.agent.tool_plain
        def vctl_status_detailed_tool() -> str:
            """Get detailed VOLTTRON platform and agent status."""
            return vctl_status_detailed()
        
        @self.agent.tool_plain
        def vctl_health_tool() -> str:
            """Check VOLTTRON platform health status."""
            return vctl_health()
        
        @self.agent.tool_plain
        def install_platform_driver_tool() -> str:
            """Install the VOLTTRON platform driver for device communication."""
            return vctl_install_platform_driver()
        
        @self.agent.tool_plain
        def show_recent_logs_tool(lines: int = 20) -> str:
            """Show recent VOLTTRON log entries.
            
            Args:
                lines: Number of recent log lines to show (default: 20)
            """
            return show_recent_logs(lines)
        
        @self.agent.tool_plain
        def check_volttron_installation_tool() -> str:
            """Check if VOLTTRON is properly installed and configured."""
            return check_volttron_installation()
        
        @self.agent.tool_plain
        def kill_existing_processes_tool() -> str:
            """Kill any existing VOLTTRON processes (cleanup utility)."""
            return kill_existing_volttron_processes()
        
        @self.agent.tool_plain
        def uninstall_all_listeners_tool() -> str:
            """Uninstall all listener agents from the platform."""
            return vctl_uninstall_all_listeners()
        
        @self.agent.tool_plain
        def install_listener_agent_tool() -> str:
            """Install a listener agent for monitoring platform messages."""
            return vctl_install_listener_agent()
        
        @self.agent.tool_plain
        def verify_agent_uninstalled_tool(agent_name: str, verification_type: str = "comprehensive") -> str:
            """Verify that an agent has been completely uninstalled.
            
            Args:
                agent_name: Name or UUID of the agent to verify
                verification_type: Type of verification (basic, comprehensive)
            """
            return verify_agent_uninstalled(agent_name, verification_type)
        
        @self.agent.tool_plain
        def get_volttron_next_steps_tool() -> str:
            """Get suggested next steps for VOLTTRON development."""
            return get_volttron_next_steps()
        
        @self.agent.tool_plain
        def show_formatting_test_tool() -> str:
            """Show a formatting test to verify output display."""
            return show_formatting_test()
        
        @self.agent.tool_plain
        def fetch_webpage_tool(url: str) -> str:
            """Fetch and read content from a webpage, especially useful for documentation.
            
            Args:
                url: The URL to fetch (e.g., GitHub README, documentation page)
            """
            return fetch_webpage_content(url)
        
        @self.agent.tool_plain
        def execute_command_tool(command: str) -> str:
            """Execute a safe system command (checking, info gathering).
            
            Args:
                command: The command to execute (only safe read-only commands allowed)
            """
            return execute_system_command(command)
        
        @self.agent.tool_plain
        def setup_postgresql_tool(db_name: str = "volttron", db_user: str = "volttron", db_password: str = "volttron") -> str:
            """Set up PostgreSQL database for VOLTTRON historian.
            
            Args:
                db_name: Database name (default: volttron)
                db_user: Database user (default: volttron)
                db_password: Database password (default: volttron)
            """
            return setup_postgresql_database(db_name, db_user, db_password)
        
        @self.agent.tool_plain
        def create_historian_config_tool(historian_type: str = "postgresql", db_config: dict = None) -> str:
            """Create historian agent configuration file.
            
            Args:
                historian_type: Type of historian (postgresql, sqlite)
                db_config: Database configuration parameters
            """
            return create_historian_config(historian_type, db_config)

    def _register_volttron_tools_on_agent(self, agent):
        """Register VOLTTRON control tools on a specific agent."""
        @agent.tool_plain
        def start_volttron_tool() -> str:
            """Start the VOLTTRON platform."""
            return start_volttron()
        
        @agent.tool_plain
        def stop_volttron_tool() -> str:
            """Stop the VOLTTRON platform."""
            return stop_volttron()
        
        @agent.tool_plain
        def check_volttron_status_tool() -> str:
            """Check VOLTTRON platform status and show recent logs."""
            return check_volttron_status()
            
        @agent.tool_plain
        def simple_volttron_status_check_tool() -> str:
            """Simple check if VOLTTRON is running with minimal output."""
            return simple_volttron_status_check()
        
        @agent.tool_plain
        def list_agents_tool() -> str:
            """List all installed VOLTTRON agents."""
            return vctl_list_agents()
        
        @agent.tool_plain
        def install_agent_tool(agent_name: str) -> str:
            """Install a VOLTTRON agent by name."""
            return vctl_install_agent(agent_name)
    
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
            "FLEXIBLE INSTALLATION:\n"
            "- When user says 'install X' use smart_install_package tool\n"
            "- It automatically determines pip vs vctl based on package type\n"
            "- Fake driver library MUST use pip (vctl won't work)\n"
            "- Python libraries (volttron-*) use pip\n"
            "- VOLTTRON agents use vctl\n"
            "- Let smart_install_package handle the logic - don't overthink it\n\n"
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
                    base_url=ai_webapp_url
                )
                self.custom_model = self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
                self.agent = self._create_agent_with_tools()
            elif self.model_name.startswith("ollama:"):
                if Agent is not None:
                    from pydantic_ai_slim.models.openai import OpenAIChatModel
                    from pydantic_ai_slim.providers.ollama import OllamaProvider
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
            is_reversal, reversal_response = self._detect_context_reversal(message)
            if is_reversal:
                return reversal_response
            
            if hasattr(self, 'awaiting_reversal_confirmation') and self.awaiting_reversal_confirmation:
                message_lower = message.lower().strip()
                if message_lower in ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay']:
                    self.awaiting_reversal_confirmation = False
                    if self.last_action == "install_agent":
                        agent_type = self.last_action_details.get("agent_type", "agent")
                        return self.call_function_tool("vctl_uninstall_agent", {"agent_uuid_or_tag": agent_type})
                    elif self.last_action == "start_volttron":
                        return self.call_function_tool("stop_volttron", {})
                    elif self.last_action == "stop_volttron":
                        return self.call_function_tool("start_volttron", {})
                    elif self.last_action == "uninstall_agent":
                        agent_type = self.last_action_details.get("agent_type", "agent")
                        return f"To reinstall the {agent_type}, please tell me which agent you'd like to install. You can say 'install listener' or 'what agents can I install' to see options."
                    else:
                        return "I'm not sure how to reverse that action. What would you like me to do?"
                elif message_lower in ['no', 'n', 'nope', 'cancel', 'nevermind']:
                    self.awaiting_reversal_confirmation = False
                    return "No problem! I'll leave everything as is. What would you like to do next?"
            
            message_lower = message.lower().strip()
            if (('what agents are running' in message_lower) or 
                ('which agents are running' in message_lower) or
                ('what agents are installed' in message_lower) or
                ('which agents are installed' in message_lower) or
                (('show' in message_lower or 'list' in message_lower) and 
                 ('running' in message_lower or 'installed' in message_lower) and 
                 'agents' in message_lower)):
                print(f"DIRECT OVERRIDE: Executing vctl_status for '{message}' query")
                return self.call_function_tool("vctl_status", {})
            
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
            
           
            result = await self.agent.arun(message + context_message)
            
          
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": result.data})
            self._save_conversation_history()
            
            return result.data
            
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
            
            if is_claude_model:
                if self.custom_client:
                    response = self.custom_client.chat.completions.create(
                        model=self.custom_model,
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.7
                    )
                else:
                    client = openai.OpenAI()
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.7
                    )
                
                ai_response = response.choices[0].message.content
                
                ai_response = self._process_claude_response_for_commands(ai_response, message)
                
            else:
                function_schemas = self.get_function_schemas()
                
                if self.custom_client:
                    response = self.custom_client.chat.completions.create(
                        model=self.custom_model,
                        messages=messages,
                        functions=function_schemas,
                        function_call="auto",
                        max_tokens=1000,
                        temperature=0.7
                    )
                else:
                    client = openai.OpenAI()
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        functions=function_schemas,
                        function_call="auto",
                        max_tokens=1000,
                        temperature=0.7
                    )
                
                message_response = response.choices[0].message
                
                if message_response.function_call:
                    function_name = message_response.function_call.name
                    function_args = json.loads(message_response.function_call.arguments)
                    
                    function_result = self.execute_function_call(function_name, function_args)
                    
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
                            messages=follow_up_messages,
                            max_tokens=1000,
                            temperature=0.7
                        )
                    else:
                        client = openai.OpenAI()
                        final_response = client.chat.completions.create(
                            model=self.model_name,
                            messages=follow_up_messages,
                            max_tokens=1000,
                            temperature=0.7
                        )
                    
                    ai_response = final_response.choices[0].message.content
                else:
                    ai_response = message_response.content
            
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            self._save_conversation_history()
            
            return ai_response
            
        except Exception as e:
            print(f"Error in AI response generation: {e}")
            return self._handle_direct_command(message) or f"❌ I encountered an error: {str(e)}. Please try again."
    
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
        """Handle direct VOLTTRON commands without AI processing."""
        message_lower = message.lower().strip()
        
        if any(indicator in message for indicator in ['http://', 'https://', 'github.com', 'www.']):
            return None
        
        database_keywords = ['postgresql', 'postgres', 'mysql', 'database', 'db setup', 'sql setup']
        volttron_agent_context = ['agent', 'vctl', 'install agent', 'uninstall agent', 'agent status']
        
        has_database_keyword = any(keyword in message_lower for keyword in database_keywords)
        has_agent_context = any(keyword in message_lower for keyword in volttron_agent_context)
        
        if has_database_keyword and not has_agent_context:
            return None
        
        if message_lower.startswith(('which ', 'psql ', 'cat ', 'ls ', 'grep ', 'find ')):
            return None
        
        workflow_indicators = ['execute all', 'follow all', 'complete setup', 'full setup', 
                              'setup and configure', 'install and setup', 'install and configure']
        if any(indicator in message_lower for indicator in workflow_indicators):
            return None
        
        if 'then' in message_lower or 'and then' in message_lower:
            if any(word in message_lower for word in ['start', 'startup', 'launch']) and 'install' in message_lower:
                if 'listener' in message_lower:
                    return self._execute_start_then_install_listener()
                elif 'driver' in message_lower or 'platform driver' in message_lower:
                    return self._execute_start_then_install_driver()
        
        if any(phrase in message_lower for phrase in ['yes, do it', 'yes do it', 'do it', 'go ahead', 'proceed']):
            if hasattr(self, 'conversation_history') and self.conversation_history:
                recent_messages = self.conversation_history[-3:]
                for msg in recent_messages:
                    if isinstance(msg, dict) and 'content' in msg:
                        content = msg['content'].lower()
                        if 'multi-step solution' in content and 'install' in content:
                            if 'listener' in content:
                                return self._execute_start_then_install_listener()
                            elif 'driver' in content or 'platform driver' in content:
                                return self._execute_start_then_install_driver()
      
        if any(phrase in message_lower for phrase in [
            'what is running', 'what\'s running', 'what running', 'whats running',
            'show me what running', 'tell me what running', 'inform me what running',
            'is anything running', 'anything running', 'is running', 'running status'
        ]):
            return self._handle_whats_running_question(message_lower)
        

        elif any(phrase in message_lower for phrase in [
            'is volttron running', 'is platform running', 'volttron running',
            'volttron running?', 'is it running', 'is volttron up',
            'check if volttron is running', 'check volttron running',
            'volttron status?', 'what is volttron status', 'volttron up?',
            'tell me if volttron', 'is the platform running', 'platform running?',
            'check if volttron', 'volttron active?', 'is volttron active'
        ]):
        
            from chat_app.volttron_commands import is_volttron_running
            return is_volttron_running()
        
        if message_lower in ['status', 'vctl status', 'agent status', 'check status']:
            return self.call_function_tool("vctl_status", {})
        
        elif (any(all(word in message_lower for word in combo) for combo in [
            ['what', 'agents', 'running'], 
            ['which', 'agents', 'running'],
            ['what', 'agents', 'installed'],
            ['which', 'agents', 'installed'],
            ['show', 'running', 'agents'], 
            ['list', 'running', 'agents'], 
            ['show', 'installed', 'agents'],
            ['list', 'installed', 'agents'],
            ['show', 'agents', 'running'],
            ['show', 'agents', 'installed'],
            ['tell', 'running', 'agents'],
            ['tell', 'installed', 'agents'],
            ['report', 'agents', 'running'],
            ['report', 'agents', 'installed'],
            ['agents', 'status'],
            ['agent', 'status']
        ]) or any(phrase in message_lower for phrase in [
            'list agents', 'show agents', 'show me agents', 'list my agents',
            'show my agents', 'what agents', 'which agents', 'agents?',
            'list all agents', 'show all agents', 'get agents', 'vctl status',
            'show me all agents', 'list all my agents', 'display agents'
        ])):
            print(f"Detected agent status pattern in '{message}' - executing vctl_status directly")
            
            return self.call_function_tool("vctl_status", {})
        

        agent_status_patterns = [
            r'(?:what|whats|show|check)?\s*status\s+(?:of\s+)?(?:the\s+)?([a-z0-9\-_]+)\s+agent',  # "status of listener agent"
            r'(?:what|whats|show|check)?\s*(?:the\s+)?([a-z0-9\-_]+)\s+agent\s+status',  # "listener agent status"
            r'how\s+is\s+(?:the\s+)?([a-z0-9\-_]+)\s+agent(?:\s+doing)?',  # "how is listener agent"
            r'is\s+(?:the\s+)?([a-z0-9\-_]+)\s+agent\s+(?:running|active|up)',  # "is listener agent running"
        ]
        
        for pattern in agent_status_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
           
                excluded_words = ['the', 'it', 'that', 'this', 'what', 'how', 'is', 'agent', 'agents', 'are', 'all', 'my', 'your', 'their', 'a', 'an']
                if agent_id not in excluded_words:
        
                    status_result = self.call_function_tool("vctl_status", {})
                    if agent_id in status_result:
                        return status_result
                    else:
                        return f"🔍 **Looking for agent '{agent_id}'...**\n\n{status_result}"
        
       
        start_volttron_patterns = [
            r'\b(?:start|startup|launch|boot|fire\s*up|bring\s*up|turn\s*on)(?:\s+up)?(?:\s+the)?\s+(?:volttron|volltron|volltrron|voltrron|voltron|platform)\b',
            r'\bvolttron\s+(?:start|startup|launch)\b',
        ]
        
        stop_volttron_patterns = [
            r'\b(?:stop|shutdown|shut\s*down|kill|halt|turn\s*off|bring\s*down)(?:\s+the)?\s+(?:volttron|volltron|volltrron|voltrron|voltron|platform)\b',
            r'\bvolttron\s+(?:stop|shutdown)\b',
        ]
        
    
        if any(re.search(pattern, message_lower) for pattern in start_volttron_patterns):
            return self.call_function_tool("start_volttron", {})
        
  
        if any(re.search(pattern, message_lower) for pattern in stop_volttron_patterns):
            return self.call_function_tool("stop_volttron", {})
        
    
        elif any(phrase in message_lower for phrase in [
            'install listener', 'install volttron-listener', 'install volttron listener',
            'vctl install listener', 'vctl install volttron-listener',
            'setup listener', 'set up listener', 'add listener', 'get listener'
        ]):
            return self._handle_install_listener_intent()
        
        elif any(phrase in message_lower for phrase in [
            'install fake driver library', 'install fake driver lib',
            'install the fake driver library', 'fake driver library',
            'setup fake driver library', 'set up fake driver library',
            'install volttron-lib-fake-driver', 'install fake-driver library'
        ]):
            return self.call_function_tool("install_fake_driver_library", {})
        
        # Handle vctl install-lib or generic library installation
        elif any(phrase in message_lower for phrase in [
            'vctl install-lib', 'vctl install lib', 'install-lib',
            'install library', 'install a library', 'install volttron library'
        ]) or (('install' in message_lower) and ('volttron-lib-' in message_lower)):
            # Extract library name from message
            library_name = None
            
            # Try to find library name in various formats
            patterns = [
                r'(?:install-lib|install\s+lib|install\s+library)\s+([a-z0-9\-_]+)',
                r'install\s+(volttron-lib-[a-z0-9\-_]+)',
                r'(volttron-lib-[a-z0-9\-_]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    library_name = match.group(1)
                    break
            
            if library_name:
                # Normalize library name
                if not library_name.startswith('volttron-'):
                    if library_name.startswith('lib-'):
                        library_name = 'volttron-' + library_name
                    else:
                        library_name = 'volttron-lib-' + library_name
                
                return self.call_function_tool("vctl_install_lib", {"library_name": library_name})
            else:
                return """I can help you install VOLTTRON libraries!

To install a library, please specify the library name. For example:
• "install library volttron-lib-modbustk-driver"
• "vctl install-lib volttron-lib-bacnet-driver"
• "install volttron-lib-fake-driver"

**Common VOLTTRON libraries:**
• volttron-lib-fake-driver (for testing/simulation)
• volttron-lib-modbustk-driver (for Modbus devices)
• volttron-lib-bacnet-driver (for BACnet devices)

What library would you like to install?"""
        
        elif any(phrase in message_lower for phrase in [
            'configure fake driver', 'config fake driver', 'setup fake driver',
            'set up fake driver', 'fake driver config', 'configure fake'
        ]):
            return self.call_function_tool("configure_fake_driver", {})
        
        elif any(phrase in message_lower for phrase in [
            'start fake driver', 'start the fake driver', 'run fake driver',
            'launch fake driver', 'enable fake driver', 'turn on fake driver'
        ]):
            return self.call_function_tool("start_fake_driver", {})
        
        elif any(phrase in message_lower for phrase in [
            'install platform driver', 'install driver', 'setup driver',
            'set up platform driver', 'add platform driver', 'install fake driver'
        ]):
            return self._handle_install_driver_intent()
        
        elif 'install' in message_lower and 'agent' in message_lower:
            agent_name_match = re.search(r'install\s+(?:the\s+)?([a-z][a-z0-9\-_]*)\s+agent', message_lower)
            if agent_name_match:
                agent_name = agent_name_match.group(1)
                if agent_name not in ['listener', 'platform', 'driver', 'fake']:
                    return self._handle_install_agent_intent(agent_name)
            return self.call_function_tool("vctl_install_listener_agent", {})
        
        elif any(phrase in message_lower for phrase in [
            'set up monitoring', 'setup monitoring', 'configure monitoring',
            'start monitoring', 'enable monitoring', 'monitor'
        ]):
            return """To set up monitoring:

1. **Install listener agent** (if not already installed):
   - Say: "install listener"

2. **Check agent status**:
   - Say: "show agents" or "status"

3. **View logs** to see monitored data:
   - Say: "show logs" or "show fake driver logs"

The listener agent will automatically monitor all platform messages including fake driver data.

Would you like me to install the listener agent now?"""
        
        elif 'install' in message_lower and not any(char.isdigit() for char in message):
            if any(word in message_lower for word in ['library', 'lib', 'fake', 'driver', 'monitoring', 'monitor']):
                return """I can help you install:

1. **Fake driver library**: Say "install fake driver library"
2. **Platform driver**: Say "install platform driver" (already installed!)
3. **Configure fake driver**: Say "configure fake driver"
4. **Listener agent**: Say "install listener"

What would you like to install?"""
            

        force_remove_patterns = [
            "force remove agent", "force delete agent", "force remove tag", 
            "remove agent force", "delete agent force", "remove with force",
            "force uninstall", "forcibly remove", "forcibly delete",
            "remove agent forcefully", "forcefully remove", "aggressively remove",
            "remove agent aggressively", "force removal", "force agent removal",
            "remove the stuck agent", "remove hanging agent", "kill agent",
            "force kill agent", "permanently remove agent"
        ]
        
        if any(pattern in message_lower for pattern in force_remove_patterns):
            
            words = message_lower.split()
            agent_tag = None
            
            
            digit_pattern = re.search(r'agent\s+([0-9a-z])(?:\s+|$)', message_lower)
            if digit_pattern:
                agent_tag = digit_pattern.group(1)
                return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
                
            
            digit_pattern = re.search(r'(?:remove|delete|kill)\s+([0-9])(?:\s+|$)', message_lower)
            if digit_pattern:
                agent_tag = digit_pattern.group(1)
                return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
                
            
            if "tag" in words:
                tag_index = words.index("tag")
                if tag_index < len(words) - 1:
                    agent_tag = words[tag_index + 1]
                    return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
            
            
            for keyword in ["agent", "with", "tagged", "named", "number", "id", "uuid", "identity"]:
                if keyword in words:
                    keyword_index = words.index(keyword)
                    if keyword_index < len(words) - 1:
                        agent_tag = words[keyword_index + 1]
                        
                        if agent_tag not in ["force", "forcefully", "using", "that", "is", "was", "the", "a"]:
                            return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
            
            
            for force_word in ["force", "forcefully", "aggressively"]:
                if force_word in words:
                    force_index = words.index(force_word)
                    
                    for i in range(force_index+1, min(force_index+5, len(words))):
                        if words[i].isdigit() or (len(words[i]) == 1 and words[i].isalpha()):
                            agent_tag = words[i]
                            return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
            
            
            return """Which agent would you like to force remove? Please specify the agent tag or number.

Examples:
• "Force remove agent 9"
• "Force remove platform.driver"
• "Force remove with tag listener"

You can use "vctl status" to see all agents and their tags."""
        
        
        elif any(phrase in message_lower for phrase in [
            'install fake driver', 'setup fake driver', 'set up fake driver',
            'set up the fake driver', 'setup the fake driver', 'install the fake driver',
            'configure fake driver', 'configure the fake driver', 'fake driver setup',
            'get fake driver', 'add fake driver', 'enable fake driver',
            'setup fake', 'set up fake', 'install fake', 'set up the fake'
        ]):
            return self.call_function_tool("setup_fake_driver_complete", {})
        
        elif any(phrase in message_lower for phrase in [
            'install volttron-lib-fake-driver', 'install fake driver library',
            'install fake library', 'install the fake driver library'
        ]):
            return self.call_function_tool("install_fake_driver_library", {})
        elif any(phrase in message_lower for phrase in [
            'show fake driver logs', 'fake driver logs', 'fake driver data',
            'show fake data', 'fake sensor data', 'view fake driver', 
            'see fake driver', 'fake driver output'
        ]):
            return self.call_function_tool("show_fake_driver_logs", {})
        elif any(phrase in message_lower for phrase in [
            'is fake driver working', 'fake driver working', 'check fake driver',
            'fake driver status', 'is the fake driver running', 'fake driver running',
            'verify fake driver', 'test fake driver', 'fake driver operational'
        ]):
            return self.call_function_tool("check_fake_driver_status", {})
        elif any(phrase in message_lower for phrase in [
            'watch fake driver', 'monitor fake driver', 'tail fake driver',
            'watch fake logs', 'monitor fake logs', 'tail fake logs',
            'watch fake data', 'monitor fake data'
        ]):
            return self.call_function_tool("watch_fake_driver_logs", {})
        
        elif any(phrase in message_lower for phrase in [
            'show logs', 'view logs', 'see logs', 'check logs', 
            'show recent logs', 'view recent logs', 'see recent logs',
            'display logs', 'read logs', 'get logs', 'show the logs',
            'view the logs', 'see the logs', 'i want to see the logs',
            'want to see logs', 'check the logs', 'look at logs'
        ]):
            return self.call_function_tool("show_recent_logs", {})
        
        elif message_lower in ['list available agents', 'available agents', 'what agents can i install']:
            return self.call_function_tool("list_available_agents", {})
        elif message_lower in ['list agents', 'show agents', 'what agents', 'installed agents', 'what agents are installed']:
            
            return self.call_function_tool("vctl_status", {})
        
        
        install_general_patterns = [
            r'install\s+(?:the\s+)?(\S+(?:\s+\S+)?)',  
            r'can\s+you\s+install\s+(?:the\s+)?(\S+(?:\s+\S+)?)',  
            r'please\s+install\s+(?:the\s+)?(\S+(?:\s+\S+)?)',  
            r'i\s+(?:want|need)\s+to\s+install\s+(?:the\s+)?(\S+(?:\s+\S+)?)', 
            r'(?:add|get|setup|set\s+up)\s+(?:the\s+)?(\S+(?:\s+\S+)?)',  
        ]
        
       
        for pattern in install_general_patterns:
            match = re.search(pattern, message_lower)
            if match:
                package_name = match.group(1).strip()
               
                skip_terms = ['fake driver', 'listener', 'logs', 'status', 'agent status']
                if any(term in package_name for term in skip_terms):
                    continue
               
                package_name = package_name.replace(' agent', '').replace(' package', '').strip()
                if package_name and package_name not in ['the', 'a', 'an', 'it', 'this', 'that']:
                    return self.call_function_tool("smart_install_package", {
                        "package_name": package_name,
                        "user_message": message
                    })
        
        
        if ('verify uninstall' in message_lower or 'check uninstall' in message_lower or 
            'confirm removal' in message_lower or 'verify removal' in message_lower or 
            'check if' in message_lower or 'check removal' in message_lower):
           
            words = message_lower.split()
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
                return self.call_function_tool("verify_agent_uninstalled", {"agent_identifier": agent_id})
        
       
        uninstall_patterns = [
            r'uninstall\s+(\w+)',
            r'remove\s+(\w+)', 
            r'delete\s+(\w+)',
            r'uninstall\s+agent\s+(\w+)',
            r'remove\s+agent\s+(\w+)',
            r'delete\s+agent\s+(\w+)'
        ]
        
        for pattern in uninstall_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                if agent_id and agent_id not in ['agent', 'the', 'platform']:
                    return self.call_function_tool("vctl_uninstall_agent", {"agent_uuid_or_tag": agent_id})
        
        
        pip_install_patterns = [
            r'pip\s+install\s+(\S+)',
            r'install\s+package\s+(\S+)',
            r'add\s+package\s+(\S+)',
            r'pip\s+add\s+(\S+)',
            r'install\s+with\s+pip\s+(\S+)',
            r'install\s+the\s+(\S+-\S+)(?:\s+package)?',
            r'install\s+(\S+-\S+)',  
            r'install\s+the\s+platform\s+driver',  
            r'install\s+platform\s+driver', 
            r'install\s+the\s+(\S+)(?:\s+package)?',
            r'install\s+(\S+)(?:\s+agent)?',
            r'install\s+(\S+)(?:\s+using\s+pip)?',
            r'can\s+you\s+install\s+(\S+)'
        ]
        
       
        if ("install platform driver" in message_lower or 
            "install the platform driver" in message_lower or 
            "install a platform driver" in message_lower):
          
            return self.call_function_tool("vctl_install_platform_driver", {})
        
        for pattern in pip_install_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if pattern == r'install\s+the\s+platform\s+driver' or pattern == r'install\s+platform\s+driver':
                    package_name = "platform-driver"
                else:
                    package_name = match.group(1)
                
                if package_name and package_name not in ['package', 'the', 'a', 'an', 'that', 'it', 'this', 'agent']:
                    if package_name == "platform-driver" or package_name == "platform":
                        if "platform driver" in message_lower:
                            return self.call_function_tool("vctl_install_platform_driver", {})
                        else:
                            package_name = "volttron-platform-driver"
                    elif package_name == "listener":
                        return self.call_function_tool("vctl_install_listener_agent", {})
                    elif package_name == "sqlite-historian":
                        return self.call_function_tool("vctl_install_agent", {"agent_name": "sqlite-historian"})
                    elif package_name == "platform_driver":
                        return self.call_function_tool("vctl_install_platform_driver", {})
                    
                    elif package_name == "platform" and ("platform driver" in message_lower):
                        return self.call_function_tool("vctl_install_platform_driver", {})
                
                elif package_name in ["fake-driver", "bacnet-driver", "postgresql-historian", 
                                    "protocol-proxy", "bacnet-proxy", "bacnet-scan", "platform-lookup"]:
                    return self.call_function_tool("vctl_install_agent", {"agent_name": package_name})
                
                upgrade = "--upgrade" in message_lower or "upgrade" in message_lower
                
                return self.call_function_tool("pip_install", {"package_name": package_name, "upgrade": upgrade})
        
        pip_uninstall_patterns = [
            r'pip\s+uninstall\s+(\S+)',
            r'uninstall\s+package\s+(\S+)',
            r'remove\s+package\s+(\S+)',
            r'pip\s+remove\s+(\S+)'
        ]
        
        for pattern in pip_uninstall_patterns:
            match = re.search(pattern, message_lower)
            if match:
                package_name = match.group(1)
                if package_name and package_name not in ['package', 'the']:
                    return self.call_function_tool("pip_uninstall", {"package_name": package_name})
        
        if any(phrase in message_lower for phrase in [
            'pip list', 'list packages', 'show packages', 'what packages', 'pip show',
            'installed packages', 'list installed'
        ]):
            return self.call_function_tool("pip_list", {})
        
        if any(phrase in message_lower for phrase in [
            'start all agents', 'start all agent', 'start everything', 'start them all',
            'run all agents', 'run all agent', 'start every agent', 'get all agents running'
        ]):
            return self.call_function_tool("vctl_start_all_agents", {})
        
        agent_reference_patterns = [
            r'start.*?\*\*([a-z0-9]+)\*\*',
            r'start.*?•\s*\*\*([a-z0-9]+)\*\*',
            r'start.*?(?:agent\s+)?([a-z0-9]+)\s*-\s*volttron',
            r'start.*?(?:uuid\s*:?\s*)?([a-z0-9]+)(?:\s*\)|$)',
        ]
        
        for pattern in agent_reference_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                if len(agent_id) <= 3 and agent_id not in ['the', 'one', 'it', 'this', 'that']:
                    return self.call_function_tool("vctl_start_agent", {"agent_uuid_or_tag": agent_id})
        

        if any(phrase in message_lower for phrase in [
            'start listener', 'start the listener', 'run listener', 'run the listener'
        ]):
            return self.call_function_tool("vctl_start_agent", {"agent_uuid_or_tag": "b"})
        
        start_patterns = [
            r'start\s+(\w+)',
            r'start\s+agent\s+(\w+)'
        ]
        
        for pattern in start_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                volttron_variations = [
                    'agent', 'volttron', 'volltron', 'volltrron', 'voltrron', 'voltron', 'platform', 
                    'the', 'this', 'that', 'one', 'it', 'up', 'of', 'a', 'an', 'my', 'our'
                ]
                if 'volttron' in message_lower or 'volltron' in message_lower or 'voltron' in message_lower:
                    continue
                if agent_id and agent_id not in volttron_variations:
                    return self.call_function_tool("vctl_start_agent", {"agent_uuid_or_tag": agent_id})
        
        stop_patterns = [
            r'stop\s+(\w+)',
            r'stop\s+agent\s+(\w+)'
        ]
        
        for pattern in stop_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                volttron_variations = [
                    'agent', 'volttron', 'volltron', 'volltrron', 'voltrron', 'voltron', 'platform',
                    'the', 'this', 'that', 'one', 'it', 'of', 'a', 'an', 'my', 'our'
                ]
                if 'volttron' in message_lower or 'volltron' in message_lower or 'voltron' in message_lower:
                    continue
                if agent_id and agent_id not in volttron_variations:
                    return self.call_function_tool("vctl_stop_agent", {"agent_uuid_or_tag": agent_id})
        
        return None  
    

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
            
     
        general_keywords = [
            'help', 'what can you do', 'how does this work', 'what is volttron',
            'get started', 'tutorial', 'how to', 'what should i do',
            'status', 'hello', 'hi', 'hey', 'getting started'
        ]
        
        return any(keyword in message_lower for keyword in general_keywords)
    
    def _detect_context_reversal(self, message: str) -> Tuple[bool, str]:
        """Enhanced contextual reversal detection with conversation history analysis."""
        message_lower = message.lower().strip()
        
        reversal_phrases = [
            'i changed my mind', 'change my mind', 'changed my mind',
            'i want to undo', 'undo that', 'undo it', 'undo',
            'reverse that', 'reverse it', 'go back',
            'i dont want', "i don't want", 'cancel that', 'cancel',
            'nevermind', 'never mind', 'forget it', 'forget that',
            'actually no', 'wait no', 'no wait',
            'i made a mistake', 'that was wrong', 'wrong choice',
            'i want the opposite', 'do the opposite'
        ]
        
        is_reversal = any(phrase in message_lower for phrase in reversal_phrases)
        
        if is_reversal and self.last_action:
            self.awaiting_reversal_confirmation = True
            
            if self.last_action == "install_agent":
                agent_type = self.last_action_details.get("agent_type", "agent")
                return True, f"It sounds like you want to uninstall the {agent_type} agent that was just installed. Should I uninstall it for you?"
            elif self.last_action == "uninstall_agent":
                agent_type = self.last_action_details.get("agent_type", "agent")
                return True, f"It sounds like you want to reinstall the {agent_type} agent that was just removed. Should I install it again for you?"
            elif self.last_action == "start_volttron":
                return True, "It sounds like you want to stop VOLTTRON that was just started. Should I stop it for you?"
            elif self.last_action == "stop_volttron":
                return True, "It sounds like you want to start VOLTTRON that was just stopped. Should I start it for you?"
            elif self.last_action == "start_agent":
                agent_id = self.last_action_details.get("agent_id", "agent")
                return True, f"It sounds like you want to stop agent '{agent_id}' that was just started. Should I stop it for you?"
            elif self.last_action == "stop_agent":
                agent_id = self.last_action_details.get("agent_id", "agent")
                return True, f"It sounds like you want to start agent '{agent_id}' that was just stopped. Should I start it for you?"
            else:
                return True, "I understand you want to reverse something, but I'm not sure what. Can you be more specific about what you'd like me to undo?"
        
        return False, ""
    
    def _handle_whats_running_question(self, message_lower: str) -> str:
        """Handle 'what's running' questions with context analysis and clarification."""
        

        context_clues = {
            'volttron': ['volttron', 'platform', 'system', 'daemon'],
            'agents': ['agent', 'agents', 'service', 'services', 'listener', 'driver'],
            'processes': ['process', 'processes', 'pid', 'background']
        }
        

        recent_context = ""
        if hasattr(self, 'conversation_history') and self.conversation_history:

            recent_messages = self.conversation_history[-5:]
            for msg in recent_messages:
                if isinstance(msg, dict) and 'content' in msg:
                    recent_context += msg['content'].lower() + " "
        

        normalized_message = message_lower
        volttron_typos = ['volltron', 'volltrron', 'voltrron', 'voltron']
        for typo in volttron_typos:
            normalized_message = normalized_message.replace(typo, 'volttron')
        
        full_context = (recent_context + " " + normalized_message).lower()
        
        
        scores = {}
        for category, keywords in context_clues.items():
            scores[category] = sum(1 for keyword in keywords if keyword in full_context)
        
        
        max_score = max(scores.values()) if scores.values() else 0
        
        if max_score > 0:
            
            likely_category = max(scores, key=scores.get)
            
            
            tied_categories = [cat for cat, score in scores.items() if score == max_score]
            
            if len(tied_categories) > 1:
               
                pass 
            elif likely_category == 'volttron':
               
                from chat_app.volttron_commands import is_volttron_running
                return is_volttron_running()
            elif likely_category == 'agents':
               
                return self.call_function_tool("vctl_status", {})
            else:
                
                return self.call_function_tool("vctl_status", {})
        
       
        from chat_app.volttron_commands import is_volttron_running, vctl_status
        
       
        volttron_status = is_volttron_running()
        is_platform_running = volttron_status.lower() in ['yes', 'true'] or "✅" in volttron_status or "running" in volttron_status.lower()
        
        if is_platform_running:
            return ("🤔 **What specifically are you asking about?**\n\n"
                   "I can check:\n"
                   "• **VOLTTRON platform** - The main system status\n"
                   "• **VOLTTRON agents** - Individual services and their status\n\n"
                   "💡 Just say *\"platform status\"* or *\"agent status\"* to be specific!")
        else:
            return ("🤔 **What specifically are you asking about?**\n\n"
                   "⚠️ **VOLTTRON platform is not running** - so no agents can be active either.\n\n"
                   "Would you like me to:\n"
                   "• **Start VOLTTRON** - Launch the platform\n"
                   "• **Check system processes** - See what's running on your system")
    
    def _handle_install_listener_intent(self) -> str:
        """Handle listener agent installation with intelligent prerequisite checking and multi-step workflow."""
        from chat_app.volttron_commands import is_volttron_running, start_volttron, vctl_install_listener_agent
        
        
        acknowledgment = "👍 **I understand you want to install the listener agent.**\n\n"
        
      
        volttron_status = is_volttron_running()
        is_running = volttron_status.lower() in ['yes', 'true'] or "✅" in volttron_status
        
        if not is_running:
          
            return (acknowledgment +
                   "⚠️ **VOLTTRON is not running** - it needs to be running to install agents.\n\n"
                   "🔄 **Multi-step solution:**\n"
                   "I can do this for you:\n"
                   "1. Start VOLTTRON platform\n"
                   "2. Wait for it to initialize\n"
                   "3. Install the listener agent\n\n"
                   "💡 **Just say:** *\"yes, do it\"* or *\"start volttron then install listener\"*\n\n"
                   "Or if you prefer to do it manually:\n"
                   "• First say: *\"start volttron\"*\n"
                   "• Then say: *\"install listener\"*")
        
       
        return acknowledgment + vctl_install_listener_agent()
    
    def _handle_install_driver_intent(self) -> str:
        """Handle platform driver installation with intelligent prerequisite checking."""
        from chat_app.volttron_commands import is_volttron_running, vctl_install_platform_driver
        
       
        acknowledgment = "👍 **I understand you want to install the platform driver.**\n\n"
        
 
        volttron_status = is_volttron_running()
        is_running = volttron_status.lower() in ['yes', 'true'] or "✅" in volttron_status
        
        if not is_running:
           
            return (acknowledgment +
                   "⚠️ **VOLTTRON is not running** - it needs to be running to install agents.\n\n"
                   "🔄 **Multi-step solution:**\n"
                   "I can do this for you:\n"
                   "1. Start VOLTTRON platform\n"
                   "2. Wait for it to initialize\n"
                   "3. Install the platform driver\n\n"
                   "💡 **Just say:** *\"yes, do it\"* or *\"start volttron then install platform driver\"*\n\n"
                   "Or if you prefer to do it manually:\n"
                   "• First say: *\"start volttron\"*\n"
                   "• Then say: *\"install platform driver\"*")
        
      
        return acknowledgment + vctl_install_platform_driver()
    
    def _handle_install_agent_intent(self, agent_name: str) -> str:
        """Handle generic agent installation with intelligent prerequisite checking."""
        from chat_app.volttron_commands import is_volttron_running, vctl_install_agent
     
        acknowledgment = f"👍 **I understand you want to install the {agent_name} agent.**\n\n"
        
     
        volttron_status = is_volttron_running()
        is_running = volttron_status.lower() in ['yes', 'true'] or "✅" in volttron_status
        
        if not is_running:
         
            return (acknowledgment +
                   "⚠️ **VOLTTRON is not running** - it needs to be running to install agents.\n\n"
                   "🔄 **Multi-step solution:**\n"
                   "I can do this for you:\n"
                   f"1. Start VOLTTRON platform\n"
                   f"2. Wait for it to initialize\n"
                   f"3. Install the {agent_name} agent\n\n"
                   f"💡 **Just say:** *\"yes, do it\"* or *\"start volttron then install {agent_name}\"*\n\n"
                   "Or if you prefer to do it manually:\n"
                   "• First say: *\"start volttron\"*\n"
                   f"• Then say: *\"install {agent_name}\"*")
        
        
        return acknowledgment + vctl_install_agent(agent_name)
    
    def _execute_start_then_install_listener(self) -> str:
        """Execute multi-step workflow: start VOLTTRON then install listener agent."""
        from chat_app.volttron_commands import start_volttron, is_volttron_running, vctl_install_listener_agent
        import time
        
        response = "🔄 **Executing multi-step workflow:**\n\n"
        
        
        response += "**Step 1/3:** Starting VOLTTRON platform...\n"
        start_result = start_volttron()
        response += start_result + "\n\n"
        
       
        if "❌" in start_result or "error" in start_result.lower():
            return response + "⚠️ **Workflow stopped** - Could not start VOLTTRON. Please check the error above."
        
        
        response += "**Step 2/3:** Waiting for VOLTTRON to initialize"
        wait_time = int(os.getenv('VOLTTRON_STARTUP_WAIT', '5'))
        for i in range(wait_time):
            time.sleep(1)
            response += "."
        response += " Done!\n\n"
        
        
        status = is_volttron_running()
        if status.lower() not in ['yes', 'true'] and "✅" not in status:
            return response + "⚠️ **Workflow stopped** - VOLTTRON didn't start properly. Try starting it manually."
        
       
        response += "**Step 3/3:** Installing listener agent...\n"
        install_result = vctl_install_listener_agent()
        response += install_result + "\n\n"
        
        
        if "✅" in install_result or "success" in install_result.lower():
            response += "🎉 **Multi-step workflow completed successfully!**"
        else:
            response += "⚠️ **Workflow completed with issues** - Check the installation result above."
        
        return response
    
    def _execute_start_then_install_driver(self) -> str:
        """Execute multi-step workflow: start VOLTTRON then install platform driver."""
        from chat_app.volttron_commands import start_volttron, is_volttron_running, vctl_install_platform_driver
        import time
        
        response = "🔄 **Executing multi-step workflow:**\n\n"
        
        
        response += "**Step 1/3:** Starting VOLTTRON platform...\n"
        start_result = start_volttron()
        response += start_result + "\n\n"
        
        
        if "❌" in start_result or "error" in start_result.lower():
            return response + "⚠️ **Workflow stopped** - Could not start VOLTTRON. Please check the error above."
        
        
        response += "**Step 2/3:** Waiting for VOLTTRON to initialize"
        wait_time = int(os.getenv('VOLTTRON_STARTUP_WAIT', '5'))
        for i in range(wait_time):
            time.sleep(1)
            response += "."
        response += " Done!\n\n"
        
        
        status = is_volttron_running()
        if status.lower() not in ['yes', 'true'] and "✅" not in status:
            return response + "⚠️ **Workflow stopped** - VOLTTRON didn't start properly. Try starting it manually."
        
        
        response += "**Step 3/3:** Installing platform driver...\n"
        install_result = vctl_install_platform_driver()
        response += install_result + "\n\n"
        
        
        if "✅" in install_result or "success" in install_result.lower():
            response += "🎉 **Multi-step workflow completed successfully!**"
        else:
            response += "⚠️ **Workflow completed with issues** - Check the installation result above."
        
        return response
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "provider": self.model_name.split(":")[0] if ":" in self.model_name else "unknown",
            "model_id": self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
        }
        
