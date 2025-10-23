from typing import Optional, Dict, List, Any, Tuple, Callable
import os
import re
import json
import openai
import inspect
try:
    from pydantic_ai_slim import Agent
except ImportError:
    # Fallback for different package names
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
    show_fake_driver_logs, watch_fake_driver_logs, setup_fake_driver_complete,
    vctl_start_all_agents, vctl_force_remove_agent
)

# Initialize the Pydantic AI agent with proper function tools using decorators
try:
    # Try to create agent with Pydantic AI
    from pydantic_ai_slim import Agent
    agent = Agent(
        model=None,  # Will be set dynamically
        system_prompt=""  # Will be set dynamically
    )
except ImportError:
    try:
        from pydantic_ai import Agent
        agent = Agent(
            model=None,  # Will be set dynamically  
            system_prompt=""  # Will be set dynamically
        )
    except ImportError:
        print("Warning: Pydantic AI not available. Using OpenAI function calling only.")
        agent = None

# Register VOLTTRON function tools using @agent.tool_plain decorator
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
        # Import subprocess locally to avoid any import issues
        import subprocess
        import os
        
        # Hard-coded paths that we know work
        volttron_home = "/home/igorj/volttron-fresh/volttron_home"
        vctl_path = "/home/igorj/volttron-fresh/venv-fresh/bin/vctl"
        
        # Directly run vctl status with the correct paths
        try:
            env = os.environ.copy()
            env["VOLTTRON_HOME"] = volttron_home
            
            # Run the command directly
            result = subprocess.run(
                [vctl_path, "status"],
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                # Process the output to make it user-friendly
                output = result.stdout
                if output.strip():
                    # Log what we're returning to help debug
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
    def install_fake_driver_library_tool() -> str:
        """Install the volttron-lib-fake-driver package for testing and development."""
        return install_fake_driver_library()

    @agent.tool_plain
    def show_fake_driver_logs_tool(num_lines: int = 50) -> str:
        """Show recent fake driver data from VOLTTRON logs.
        
        Args:
            num_lines: Number of recent log lines to check (default: 50)
        """
        return show_fake_driver_logs(num_lines)

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

class AIService:
    """Service for handling AI model interactions with function tools support."""
    
    def __init__(self, model_name: str):
        """Initialize the AI service with a specific model."""
        self.model_name = model_name
        self.agent = agent  # Use the globally defined Pydantic AI agent
        self.custom_client = None
        self.conversation_history = []  # Track conversation for context
        self.last_numbered_options = {}  # Track last numbered options provided
        self.fake_driver_setup_state = "not_started"  # Track fake driver setup progress
        self.volttron_checked = False  # Track if we've checked VOLTTRON installation
        self.conversation_file = "conversation_history.json"  # File to persist conversation
        self.last_action = None  # Track the last action performed for context reversal
        self.last_action_details = {}  # Store details about the last action
        self.function_tools = {}  # Registry of available function tools (for fallback)
        self.system_prompt = self._get_volttron_system_prompt()  # Initialize system prompt
        
        # Setup the agent with the correct model and system prompt
        if self.agent:
            try:
                # Update agent model and system prompt
                self.agent.model = model_name
                self.agent.system_prompt = self.system_prompt
            except Exception as e:
                print(f"Warning: Could not configure Pydantic AI agent: {e}")
                self.agent = None
        
        # Fallback function tools registration for non-Pydantic AI usage
        self._register_fallback_function_tools()
        self._load_conversation_history()  # Load any previous conversation
        self._setup_agent()
    
    def _load_conversation_history(self):
        """Load conversation history from file if it exists."""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, 'r') as f:
                    data = json.load(f)
                    # Only load recent history (last 20 messages) to avoid growing too large
                    self.conversation_history = data.get('history', [])[-20:]
                    print(f"Loaded {len(self.conversation_history)} previous conversation messages")
        except Exception as e:
            print(f"Could not load conversation history: {e}")
            self.conversation_history = []
    
    def _save_conversation_history(self):
        """Save conversation history to file."""
        try:
            # Only save last 20 messages to keep file size reasonable
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
                    "description": "Check if VOLTTRON platform is running",
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
                    "description": "Get current status of all installed agents",
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
            
            # Call the function with the provided arguments
            if arguments:
                result = function(**arguments)
            else:
                result = function()
            
            # Track the action for context reversal
            self._track_action_for_reversal(function_name, arguments, result)
            
            return str(result)
        except Exception as e:
            return f"❌ Error calling {function_name}: {str(e)}"
    
    def _track_action_for_reversal(self, function_name: str, arguments: Dict, result: str):
        """Track function calls for contextual reversal detection."""
        # Check for uninstall/remove first (more specific)
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
        
        # Don't check again if we already checked in this session
        if self.volttron_checked:
            return False
        
        # Check on first interaction (empty conversation history)
        if len(self.conversation_history) == 0:
            return True
        
        # Check if user is asking general questions that suggest they're new
        general_queries = [
            'hello', 'hi', 'hey', 'start', 'begin', 'help', 'what can you do',
            'how do i', 'getting started', 'setup', 'install', 'volttron',
            'what is volttron', 'how does volttron work', 'agents', 'status',
            'what agents', 'show me', 'list', 'what can i install'
        ]
        
        # If message contains any general query terms, check installation
        if any(term in message_lower for term in general_queries):
            return True
        
        return False
    
    def _detect_numbered_option_request(self, message: str) -> Tuple[bool, int]:
        """
        Detect if user is referencing a numbered option from previous response.
        Returns: (is_numbered_request, option_number)
        """
        import re
        
        # Common patterns for referencing numbered options
        patterns = [
            r'option\s*(\d+)',
            r'number\s*(\d+)', 
            r'choice\s*(\d+)',
            r'do\s*(\d+)',
            r'step\s*(\d+)',              # "step 1", "do step 1" 
            r'lets?\s+do\s*step\s*(\d+)', # "lets do step 1"
            r'lets?\s+do\s*(\d+)',        # "lets do 1"
            r'#(\d+)',
            r'(\d+)(?:\s*$)',  # Just a number at the end
            r'can\s+we\s+do\s+(\d+)',  # "can we do 1"
            r'let\'s\s+do\s+(\d+)',   # "let's do 1"
            r'pick\s+(\d+)',          # "pick 1"
            r'select\s+(\d+)',        # "select 1"
            r'go\s+with\s+(\d+)',     # "go with 1"
        ]
        
        message_lower = message.lower().strip()
        
        # Special case: "next step" should execute the logical next action
        if "next step" in message_lower:
            return True, -1  # Use -1 to indicate "next step" action
        
        # Special case: if message is just a number
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
                    # Only consider it a numbered option if it's a reasonable range
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
        
        # Enhanced phrases that indicate wanting to reverse/change the last action
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
        
        # Check if message contains reversal phrases
        for phrase in reversal_phrases:
            if phrase in message_lower:
                # Set flag to await confirmation
                self.awaiting_reversal_confirmation = True
                
                # First check tracked action
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
                    # No tracked action - analyze conversation history more deeply
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
        
        # Look at last 10 messages for better context
        recent_messages = self.conversation_history[-10:]
        
        # Enhanced action patterns with more specific indicators
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
        
        # Analyze recent messages (both user and AI)
        for message in reversed(recent_messages):
            content = message.get('content', '').lower()
            role = message.get('role', '')
            
            # Focus on AI responses that indicate completed actions
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
            # Extract agent details
            if 'listener' in content:
                self.last_action = "install_agent"
                self.last_action_details = {"agent_type": "listener"}
                # Try to extract UUID
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
        
        # Pattern to match numbered list items
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
        
        # Handle "next step" logic
        if option_num == -1:
            return self._execute_next_step()
        
        if option_num not in self.last_numbered_options:
            return f"Sorry, I don't remember option {option_num}. Could you ask me again what you'd like to do?"
        
        option = self.last_numbered_options[option_num]
        title = option['title'].lower()
        description = option['description'].lower()
        
        # Map option titles to VOLTTRON commands based on common patterns
        if 'current agents' in title or 'what\'s running' in title or 'show' in title and 'agents' in title:
            return vctl_status()
        elif 'platform driver' in title and 'install' in title:
            self._track_action("install_agent", {"agent_type": "platform driver"})
            return vctl_install_platform_driver()
        elif 'listener' in title and 'install' in title:
            self._track_action("install_agent", {"agent_type": "listener"})
            return vctl_install_listener_agent()
        elif 'install' in title and ('agent' in title or any(agent in title for agent in ['historian', 'sqlite', 'postgresql', 'bacnet', 'fake-driver', 'protocol', 'lookup', 'scan'])):
            # Extract agent name from title
            words = title.lower().split()
            agent_name = None
            
            # Look for agent names in the title
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
            # Try to extract agent UUID or name from the message
            words = message.lower().split()
            agent_id = None
            
            # Look for patterns like "verify uninstall 1", "check removal of agent 1", etc.
            for i, word in enumerate(words):
                if word in ['verify', 'check', 'confirm']:
                    # Look ahead for agent identifier after keywords
                    for j in range(i + 1, len(words)):
                        potential_id = words[j]
                        # Skip common words
                        if potential_id in ['uninstall', 'removal', 'of', 'agent', 'the', 'if', 'was', 'removed', 'that']:
                            continue
                        # Found a potential agent identifier
                        if potential_id:
                            agent_id = potential_id
                            break
                    if agent_id:
                        break
            
            # Also check for patterns where the agent ID comes right after 'uninstall' or 'removal'
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
            # Try to extract agent UUID or name from the message
            words = message.lower().split()
            agent_id = None
            
            # Look for patterns like "uninstall 1", "uninstall agent 1", "remove 1", etc.
            for i, word in enumerate(words):
                if word in ['uninstall', 'remove', 'delete']:
                    # Check next word
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        if next_word != 'agent':  # Direct ID like "uninstall 1"
                            agent_id = next_word
                        elif i + 2 < len(words):  # "uninstall agent 1" format
                            agent_id = words[i + 2]
                    break
            
            # Also check for standalone numbers at the end (like "can we uninstall 1")
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
            # Default response when we can't match
            return f"🎯 Executing option {option_num}: **{option['title']}**\n\n{option['description']}\n\nLet me know if you'd like me to help with this specific task!"
    
    def _execute_next_step(self) -> str:
        """Execute the next logical step based on current fake driver setup state."""
        
        if self.fake_driver_setup_state == "not_started":
            self.fake_driver_setup_state = "platform_driver_ready"
            return vctl_install_platform_driver()
        elif self.fake_driver_setup_state == "platform_driver_ready":
            return "🎉 **Platform driver installation is complete!**\n\nWhat would you like to do next?\n1. **Check VOLTTRON status** - See how everything is running\n2. **View agent list** - See all your active agents\n3. **Check logs** - See recent activity"
        else:
            # Default to checking status if we're not sure where we are
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
            "TOOLS AVAILABLE:\n"
            "- start_volttron_tool: Start VOLTTRON\n"
            "- stop_volttron_tool: Stop VOLTTRON\n"
            "- check_volttron_status_tool: Check status\n"
            "- vctl_status: Get agent status\n"
            "- install_listener_agent_tool: Install listener\n"
            "- list_agents_tool: List agents\n"
            "- And other VOLTTRON management tools\n\n"
            "EXECUTE COMMANDS DIRECTLY - don't explain what you'll do, just do it and report the result briefly."
        )

    def _setup_agent(self):
        """Setup the Pydantic-AI agent with the specified model or custom webapp if configured."""
        ai_webapp_url = os.getenv("AI_WEBAPP_URL")
        ai_api_key = os.getenv("AI_API_KEY")
        
        try:
            # Use custom OpenAI-compatible API (like PNNL)
            if ai_webapp_url and ai_api_key:
                self.custom_client = openai.OpenAI(
                    api_key=ai_api_key,
                    base_url=ai_webapp_url
                )
                self.custom_model = self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
                # Create agent for custom client with tools
                self.agent = self._create_agent_with_tools()
            # Use Ollama if model_name starts with 'ollama:'
            elif self.model_name.startswith("ollama:"):
                if Agent is not None:
                    from pydantic_ai_slim.models.openai import OpenAIChatModel
                    from pydantic_ai_slim.providers.ollama import OllamaProvider
                    # Extract model name after provider prefix
                    model_id = self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
                    # Use Ollama provider
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
                # Use default provider logic (OpenAI, Anthropic, etc.) with pydantic-ai
                if Agent is not None:
                    self.agent = Agent(
                        self.model_name,
                        system_prompt=self._get_volttron_system_prompt()
                    )
                    self._register_volttron_tools()
                else:
                    # Fallback to OpenAI function calling if Pydantic AI not available
                    print("Using OpenAI function calling (Pydantic AI not available)")
                    self.agent = None
            
            print(f"✓ AI service initialized with model: {self.model_name}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI model '{self.model_name}': {str(e)}")
    
    async def generate_response(self, message: str) -> str:
        """Generate a response to the user's message using function tools."""
        try:
            # CHECK FOR CONTEXTUAL REVERSAL FIRST
            is_reversal, reversal_response = self._detect_context_reversal(message)
            if is_reversal:
                return reversal_response
            
            # CHECK FOR CONFIRMATION RESPONSES (yes/no after reversal suggestions)
            if hasattr(self, 'awaiting_reversal_confirmation') and self.awaiting_reversal_confirmation:
                message_lower = message.lower().strip()
                if message_lower in ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay']:
                    # User confirmed the reversal action
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
                    # User declined the reversal
                    self.awaiting_reversal_confirmation = False
                    return "No problem! I'll leave everything as is. What would you like to do next?"
            
            # Special override for "what agents are running/installed" query to ensure it always works
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
            
            # Try direct command handling first
            direct_result = self._handle_direct_command(message)
            if direct_result:
                return direct_result
            
            # Try Pydantic AI agent first
            if self.agent:
                return await self._generate_response_with_pydantic_ai(message)
            
            # Fallback to manual function tools for Claude models or if Pydantic AI unavailable
            return await self._generate_ai_response_with_tools(message)
            
        except Exception as e:
            print(f"Error in generate_response: {e}")
            return f"❌ I encountered an error: {str(e)}. Please try again or rephrase your request."
    
    async def _generate_response_with_pydantic_ai(self, message: str) -> str:
        """Generate response using Pydantic AI agent with proper tool support."""
        try:
            if not self.agent:
                raise Exception("Pydantic AI agent not available")
            
            # Update conversation history in the agent context
            conversation_messages = []
            for msg in self.conversation_history[-10:]:  # Last 10 messages for context
                if msg['role'] == 'user':
                    conversation_messages.append(f"User: {msg['content']}")
                elif msg['role'] == 'assistant':
                    conversation_messages.append(f"Assistant: {msg['content']}")
            
            # Add context if available
            context_message = ""
            if conversation_messages:
                context_message = f"\n\nRecent conversation:\n" + "\n".join(conversation_messages)
            
            # Run the agent with the message and context
            result = await self.agent.arun(message + context_message)
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": result.data})
            self._save_conversation_history()
            
            return result.data
            
        except Exception as e:
            print(f"Error in Pydantic AI response generation: {e}")
            # Fallback to manual approach
            return await self._generate_ai_response_with_tools(message)
    
    async def _generate_ai_response_with_tools(self, message: str) -> str:
        """Generate AI response with function tools support."""
        try:
            # Check if we're using a Claude model that doesn't support OpenAI function calling
            is_claude_model = "claude" in self.model_name.lower() or "anthropic" in self.model_name.lower()
            
            # Prepare messages for the AI model
            messages = [
                {
                    "role": "system", 
                    "content": self.system_prompt + self._get_enhanced_system_prompt()
                }
            ]
            
            # Add conversation history
            for msg in self.conversation_history[-10:]:  # Last 10 messages for context
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # For Claude models, use a simpler approach without function calling
            if is_claude_model:
                # Make API call without function parameters for Claude
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
                
                # Process Claude response and try to extract commands
                ai_response = response.choices[0].message.content
                
                # Try to execute any commands the AI mentions
                ai_response = self._process_claude_response_for_commands(ai_response, message)
                
            else:
                # For OpenAI models, use function calling
                function_schemas = self.get_function_schemas()
                
                # Make API call with function tools
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
                
                # Process the response
                message_response = response.choices[0].message
                
                # Check if the model wants to call a function
                if message_response.function_call:
                    # Extract function name and arguments
                    function_name = message_response.function_call.name
                    function_args = json.loads(message_response.function_call.arguments)
                    
                    # Execute the function
                    function_result = self.execute_function_call(function_name, function_args)
                    
                    # Create a follow-up message with the function result
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
                    
                    # Get final response
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
                    # No function call, just return the AI response
                    ai_response = message_response.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            self._save_conversation_history()
            
            return ai_response
            
        except Exception as e:
            print(f"Error in AI response generation: {e}")
            # Fallback to direct command handling
            return self._handle_direct_command(message) or f"❌ I encountered an error: {str(e)}. Please try again."
    
    def _process_claude_response_for_commands(self, ai_response: str, user_message: str) -> str:
        """Process Claude response and try to execute any VOLTTRON commands mentioned."""
        try:
            # Look for common command patterns in the response
            command_patterns = {
                r"vctl\s+status": "vctl_status",
                r"start.*volttron": "start_volttron",
                r"start.*volltron": "start_volttron",  # Handle common misspelling
                r"stop.*volttron": "stop_volttron",
                r"stop.*volltron": "stop_volttron",   # Handle common misspelling
                r"list.*agents": "vctl_list_agents",
                r"install.*(the|a)?.*platform.*driver": "vctl_install_platform_driver",
                r"install.*(the|a)?.*listener.*agent": "vctl_install_listener_agent",
                r"install.*agent": "vctl_install_listener_agent",
                r"show.*logs": "show_recent_logs",
                r"health.*check": "vctl_health"
            }
            
            # Special handling for "what agents are running" and similar queries
            if any(phrase in user_message.lower() for phrase in [
                'what agents are running', 'which agents are running', 'show running agents',
                'list running agents', 'show agents running', 'tell me running agents'
            ]):
                # Execute vctl_status directly for these specific queries
                return self.call_function_tool("vctl_status", {})
            
            # Check user message and AI response for command patterns
            text_to_check = (user_message + " " + ai_response).lower()
            
            # Try to execute relevant commands
            executed_commands = []
            for pattern, function_name in command_patterns.items():
                if re.search(pattern, text_to_check):
                    try:
                        if function_name in self.function_tools:
                            # Get the actual function from the function tools registry
                            func = self.function_tools[function_name]["function"]
                            result = func()
                            
                            # Super minimal output - only show essential status
                            if "start_volttron" in function_name:
                                # After starting, check if it's actually running
                                try:
                                    import time
                                    time.sleep(2)  # Wait a moment for startup
                                    status_func = self.function_tools.get("check_volttron_status", {}).get("function")
                                    if status_func:
                                        status_result = status_func()
                                        if "running" in status_result.lower() and "✅" in status_result:
                                            executed_commands.append("\n✅ VOLTTRON started and running")
                                        else:
                                            executed_commands.append("\n❌ VOLTTRON failed to start (likely configuration or permission issue)")
                                    else:
                                        executed_commands.append("\n✅ VOLTTRON start command completed")
                                except:
                                    executed_commands.append("\n❌ VOLTTRON startup verification failed")
                                    
                            elif "check_volttron_status" in function_name:
                                # Only show for explicit status checks, not automatic ones
                                if "is.*running" in text_to_check or "status" in user_message.lower():
                                    if "running" in result.lower() and "✅" in result:
                                        executed_commands.append("\n✅ Running")
                                    else:
                                        executed_commands.append("\n❌ Not running")
                                        
                            # Don't show output for other commands unless there's an error
                            elif "❌" in result or "Error" in result or "failed" in result.lower():
                                executed_commands.append(f"\n❌ {function_name} failed")
                                
                    except Exception as e:
                        executed_commands.append(f"\n❌ {function_name} error")
            
            # Append minimal status to AI response
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
        
        # Enhanced "what's running" analysis with context awareness
        if any(phrase in message_lower for phrase in [
            'what is running', 'what\'s running', 'what running', 'whats running',
            'show me what running', 'tell me what running', 'inform me what running',
            'is anything running', 'anything running', 'is running', 'running status'
        ]):
            return self._handle_whats_running_question(message_lower)
        
        # Simple VOLTTRON platform status questions
        elif any(phrase in message_lower for phrase in [
            'is volttron running', 'is platform running', 'volttron running'
        ]):
            # For simple yes/no questions about the platform itself
            from chat_app.volttron_commands import is_volttron_running
            return is_volttron_running()
        
        # Status commands
        if message_lower in ['status', 'vctl status', 'agent status', 'check status']:
            return self.call_function_tool("vctl_status", {})
        elif message_lower in ['is volttron running', 'check if volttron is running', 'volttron running']:
            return self.call_function_tool("simple_volttron_status_check", {})
        elif message_lower in ['volttron status', 'platform status', 'check volttron']:
            return self.call_function_tool("check_volttron_status", {})
        # More comprehensive pattern matching for "what agents are running/installed"
        elif any(all(word in message_lower for word in combo) for combo in [
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
            ['agents', 'status']
        ]):
            print(f"Detected agent status pattern in '{message}' - executing vctl_status directly")
            # Directly show agent status when explicitly asked about running agents
            return self.call_function_tool("vctl_status", {})
        
        # Individual agent status queries
        agent_status_patterns = [
            r'(?:what|whats|show|check)?\s*status\s+(?:of\s+)?(?:agent\s+)?([a-z0-9]+)',
            r'(?:what|whats|show|check)?\s*(?:agent\s+)?([a-z0-9]+)\s+status',
            r'how\s+is\s+(?:agent\s+)?([a-z0-9]+)(?:\s+doing)?',
            r'is\s+(?:agent\s+)?([a-z0-9]+)\s+(?:running|active|up)',
        ]
        
        for pattern in agent_status_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                # Make sure it's a reasonable agent ID (short identifier)
                if len(agent_id) <= 5 and agent_id not in ['the', 'it', 'that', 'this', 'what', 'how', 'is']:
                    # Return the full status but with focus on the specific agent
                    status_result = self.call_function_tool("vctl_status", {})
                    if agent_id in status_result:
                        return status_result
                    else:
                        return f"🔍 **Looking for agent '{agent_id}'...**\n\n{status_result}"
        
        # Start/Stop commands with better spelling handling
        if any(phrase in message_lower for phrase in [
            'start volttron', 'start volltron', 'start volltrron', 'start voltrron',
            'start voltron', 'start platform', 'launch volttron', 'launch volltron',
            'start the volttron', 'start the volltron', 'start the volltrron', 'start the voltrron',
            'start the voltron', 'start the platform', 'launch the volttron', 'launch the volltron'
        ]):
            return self.call_function_tool("start_volttron", {})
        elif any(phrase in message_lower for phrase in [
            'stop volttron', 'stop volltron', 'stop volltrron', 'stop voltrron',
            'stop voltron', 'stop platform', 'shutdown volttron', 'shutdown volltron',
            'stop the volttron', 'stop the volltron', 'stop the volltrron', 'stop the voltrron',
            'stop the voltron', 'stop the platform', 'shutdown the volttron', 'shutdown the volltron'
        ]):
            return self.call_function_tool("stop_volttron", {})
        
        # Install commands
        elif any(phrase in message_lower for phrase in [
            'install listener', 'install volttron-listener', 'install volttron listener',
            'vctl install listener', 'vctl install volttron-listener',
            'setup listener', 'set up listener', 'add listener', 'get listener'
        ]):
            return self.call_function_tool("vctl_install_listener_agent", {})
            
        # Agent removal commands with tag and force option - enhanced pattern matching
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
            # Try to extract the tag/agent identifier
            words = message_lower.split()
            agent_tag = None
            
            # Try pattern: agent DIGIT (or single letter)
            digit_pattern = re.search(r'agent\s+([0-9a-z])(?:\s+|$)', message_lower)
            if digit_pattern:
                agent_tag = digit_pattern.group(1)
                return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
                
            # Try direct number pattern - standalone digits
            digit_pattern = re.search(r'(?:remove|delete|kill)\s+([0-9])(?:\s+|$)', message_lower)
            if digit_pattern:
                agent_tag = digit_pattern.group(1)
                return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
                
            # Look for the word "tag" and get the next word
            if "tag" in words:
                tag_index = words.index("tag")
                if tag_index < len(words) - 1:
                    agent_tag = words[tag_index + 1]
                    return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
            
            # Look for patterns like "force remove agent [tag]"
            for keyword in ["agent", "with", "tagged", "named", "number", "id", "uuid", "identity"]:
                if keyword in words:
                    keyword_index = words.index(keyword)
                    if keyword_index < len(words) - 1:
                        agent_tag = words[keyword_index + 1]
                        # Skip common words that aren't likely to be tags
                        if agent_tag not in ["force", "forcefully", "using", "that", "is", "was", "the", "a"]:
                            return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
            
            # Handle "force remove 9" type pattern (just a number)
            for force_word in ["force", "forcefully", "aggressively"]:
                if force_word in words:
                    force_index = words.index(force_word)
                    # Check words after "force"
                    for i in range(force_index+1, min(force_index+5, len(words))):
                        if words[i].isdigit() or (len(words[i]) == 1 and words[i].isalpha()):
                            agent_tag = words[i]
                            return self.call_function_tool("vctl_force_remove_agent", {"agent_tag": agent_tag})
            
            # If we couldn't extract a tag, ask for clarification
            return """Which agent would you like to force remove? Please specify the agent tag or number.

Examples:
• "Force remove agent 9"
• "Force remove platform.driver"
• "Force remove with tag listener"

You can use "vctl status" to see all agents and their tags."""
        
        # Fake driver commands - COMPLETE SETUP
        elif any(phrase in message_lower for phrase in [
            'install fake driver', 'setup fake driver', 'set up fake driver',
            'set up the fake driver', 'setup the fake driver', 'install the fake driver',
            'configure fake driver', 'configure the fake driver', 'fake driver setup',
            'get fake driver', 'add fake driver', 'enable fake driver',
            'setup fake', 'set up fake', 'install fake', 'set up the fake'
        ]):
            return self.call_function_tool("setup_fake_driver_complete", {})
        # Just install the library (not full setup)
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
            'watch fake driver', 'monitor fake driver', 'tail fake driver',
            'watch fake logs', 'monitor fake logs', 'tail fake logs',
            'watch fake data', 'monitor fake data'
        ]):
            return self.call_function_tool("watch_fake_driver_logs", {})
        # General logs commands
        elif any(phrase in message_lower for phrase in [
            'show logs', 'view logs', 'see logs', 'check logs', 
            'show recent logs', 'view recent logs', 'see recent logs',
            'display logs', 'read logs', 'get logs', 'show the logs',
            'view the logs', 'see the logs', 'i want to see the logs',
            'want to see logs', 'check the logs', 'look at logs'
        ]):
            return self.call_function_tool("show_recent_logs", {})
        # List commands
        elif message_lower in ['list available agents', 'available agents', 'what agents can i install']:
            return self.call_function_tool("list_available_agents", {})
        elif message_lower in ['list agents', 'show agents', 'what agents', 'installed agents', 'what agents are installed']:
            # Use vctl_status directly for better reliability
            return self.call_function_tool("vctl_status", {})
        
        # Uninstall/verification commands with pattern matching
        elif ('verify uninstall' in message_lower or 'check uninstall' in message_lower or 
              'confirm removal' in message_lower or 'verify removal' in message_lower or 
              'check if' in message_lower or 'check removal' in message_lower):
            # Extract agent identifier
            words = message_lower.split()
            agent_id = None
            
            for i, word in enumerate(words):
                if word in ['verify', 'check', 'confirm']:
                    # Look ahead for agent identifier after keywords
                    for j in range(i + 1, len(words)):
                        potential_id = words[j]
                        # Skip common words
                        if potential_id in ['uninstall', 'removal', 'of', 'agent', 'the', 'if', 'was', 'removed', 'that']:
                            continue
                        # Found a potential agent identifier
                        if potential_id:
                            agent_id = potential_id
                            break
                    if agent_id:
                        break
            
            # Also check for patterns where the agent ID comes right after 'uninstall' or 'removal'
            if not agent_id:
                for i, word in enumerate(words):
                    if word in ['uninstall', 'removal'] and i + 1 < len(words):
                        potential_id = words[i + 1]
                        if potential_id not in ['of', 'agent', 'the', 'was']:
                            agent_id = potential_id
                            break
            
            if agent_id:
                return self.call_function_tool("verify_agent_uninstalled", {"agent_identifier": agent_id})
        
        # Pattern matching for uninstall commands
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
        
        # Pattern matching for pip install commands
        pip_install_patterns = [
            r'pip\s+install\s+(\S+)',
            r'install\s+package\s+(\S+)',
            r'add\s+package\s+(\S+)',
            r'pip\s+add\s+(\S+)',
            r'install\s+with\s+pip\s+(\S+)',
            r'install\s+the\s+(\S+-\S+)(?:\s+package)?',  # Hyphenated package names with "the"
            r'install\s+(\S+-\S+)',  # Hyphenated package names
            r'install\s+the\s+platform\s+driver',  # Special case for platform driver
            r'install\s+platform\s+driver',  # Special case for platform driver
            r'install\s+the\s+(\S+)(?:\s+package)?',
            r'install\s+(\S+)(?:\s+agent)?',
            r'install\s+(\S+)(?:\s+using\s+pip)?',
            r'can\s+you\s+install\s+(\S+)'
        ]
        
        # Special case for "platform driver" before pattern matching
        if ("install platform driver" in message_lower or 
            "install the platform driver" in message_lower or 
            "install a platform driver" in message_lower):
            # Skip pip install and directly call vctl_install_platform_driver
            # which will handle both pip install AND vctl install
            return self.call_function_tool("vctl_install_platform_driver", {})
        
        for pattern in pip_install_patterns:
            match = re.search(pattern, message_lower)
            if match:
                # Handle special case patterns that don't have capture groups
                if pattern == r'install\s+the\s+platform\s+driver' or pattern == r'install\s+platform\s+driver':
                    package_name = "platform-driver"
                else:
                    package_name = match.group(1)
                
                # Skip common words that aren't likely to be packages
                if package_name and package_name not in ['package', 'the', 'a', 'an', 'that', 'it', 'this', 'agent']:
                    # Handle special cases for volttron packages - install as agents, not just pip packages
                    if package_name == "platform-driver" or package_name == "platform":
                        # For platform driver, use vctl_install_platform_driver to properly install the agent
                        if "platform driver" in message_lower:
                            return self.call_function_tool("vctl_install_platform_driver", {})
                        else:
                            package_name = "volttron-platform-driver"
                    elif package_name == "listener":
                        # For listener, use vctl_install_listener_agent to properly install the agent
                        return self.call_function_tool("vctl_install_listener_agent", {})
                    elif package_name == "sqlite-historian":
                        # For sqlite historian, use generic agent installer
                        return self.call_function_tool("vctl_install_agent", {"agent_name": "sqlite-historian"})
                    elif package_name == "platform_driver":
                        # For platform_driver, use vctl_install_platform_driver
                        return self.call_function_tool("vctl_install_platform_driver", {})
                    
                    # Look for multi-word package names that may have been truncated
                    # Check for platform driver specifically in the original message
                    elif package_name == "platform" and ("platform driver" in message_lower):
                        return self.call_function_tool("vctl_install_platform_driver", {})
                    
                    # Check if this might be a VOLTTRON agent
                    # If package name is in AVAILABLE_AGENTS, route to agent installer
                    elif package_name in ["fake-driver", "bacnet-driver", "postgresql-historian", 
                                        "protocol-proxy", "bacnet-proxy", "bacnet-scan", "platform-lookup"]:
                        return self.call_function_tool("vctl_install_agent", {"agent_name": package_name})
                    
                    # For normal pip packages, proceed with pip install
                    # Check if upgrade flag is present
                    upgrade = "--upgrade" in message_lower or "upgrade" in message_lower
                    
                    return self.call_function_tool("pip_install", {"package_name": package_name, "upgrade": upgrade})
        
        # Pattern matching for pip uninstall commands
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
        
        # Pattern matching for pip list commands
        if any(phrase in message_lower for phrase in [
            'pip list', 'list packages', 'show packages', 'what packages', 'pip show',
            'installed packages', 'list installed'
        ]):
            return self.call_function_tool("pip_list", {})
        
        # Pattern matching for "start all agents" command
        if any(phrase in message_lower for phrase in [
            'start all agents', 'start all agent', 'start everything', 'start them all',
            'run all agents', 'run all agent', 'start every agent', 'get all agents running'
        ]):
            return self.call_function_tool("vctl_start_all_agents", {})
        
        # Enhanced pattern matching for agent commands with natural language
        # Look for agent references in conversational format
        agent_reference_patterns = [
            r'start.*?\*\*([a-z0-9]+)\*\*',  # "start this one • **b** - volttron..."
            r'start.*?•\s*\*\*([a-z0-9]+)\*\*',  # More specific bullet pattern
            r'start.*?(?:agent\s+)?([a-z0-9]+)\s*-\s*volttron',  # "start agent b - volttron..."
            r'start.*?(?:uuid\s*:?\s*)?([a-z0-9]+)(?:\s*\)|$)',  # "start agent (b)" or "start UUID: b"
        ]
        
        for pattern in agent_reference_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                # Make sure it's a valid agent ID (single letter or short number)
                if len(agent_id) <= 3 and agent_id not in ['the', 'one', 'it', 'this', 'that']:
                    return self.call_function_tool("vctl_start_agent", {"agent_uuid_or_tag": agent_id})
        
        # Simple conversational agent commands
        if any(phrase in message_lower for phrase in [
            'start listener', 'start the listener', 'run listener', 'run the listener'
        ]):
            # Try to start the most recently mentioned listener or first available
            return self.call_function_tool("vctl_start_agent", {"agent_uuid_or_tag": "b"})
        
        # Pattern matching for start/stop agent commands (basic patterns)
        start_patterns = [
            r'start\s+(\w+)',
            r'start\s+agent\s+(\w+)'
        ]
        
        for pattern in start_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                # Exclude VOLTTRON platform variations and common misspellings
                volttron_variations = ['agent', 'volttron', 'volltron', 'volltrron', 'voltrron', 'voltron', 'platform', 'the', 'this', 'that', 'one']
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
                if agent_id and agent_id not in ['agent', 'volttron', 'platform', 'the']:
                    return self.call_function_tool("vctl_stop_agent", {"agent_uuid_or_tag": agent_id})
        
        return None  # No direct command matched
    
    # Additional methods that were preserved
    def _should_check_volttron_installation(self, message: str) -> bool:
        """
        Determine if we should check VOLTTRON installation based on the message content.
        Returns True for first-time interactions or general VOLTTRON queries.
        """
        message_lower = message.lower().strip()
        
        # Don't check if we already checked recently
        if self.volttron_checked:
            return False
            
        # First message of the session
        if len(self.conversation_history) == 0:
            return True
            
        # General VOLTTRON questions
        general_keywords = [
            'help', 'what can you do', 'how does this work', 'what is volttron',
            'get started', 'tutorial', 'how to', 'what should i do',
            'status', 'hello', 'hi', 'hey', 'getting started'
        ]
        
        return any(keyword in message_lower for keyword in general_keywords)
    
    def _detect_context_reversal(self, message: str) -> Tuple[bool, str]:
        """Enhanced contextual reversal detection with conversation history analysis."""
        message_lower = message.lower().strip()
        
        # Direct reversal phrases
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
            # Set flag to await confirmation
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
        
        # First, try to infer from context what they're asking about
        context_clues = {
            'volttron': ['volttron', 'platform', 'system', 'daemon'],
            'agents': ['agent', 'agents', 'service', 'services', 'listener', 'driver'],
            'processes': ['process', 'processes', 'pid', 'background']
        }
        
        # Check conversation history for recent context
        recent_context = ""
        if hasattr(self, 'conversation_history') and self.conversation_history:
            # Look at last few messages for context
            recent_messages = self.conversation_history[-5:]
            for msg in recent_messages:
                if isinstance(msg, dict) and 'content' in msg:
                    recent_context += msg['content'].lower() + " "
        
        # Add current message to context (handle VOLTTRON typos)
        normalized_message = message_lower
        volttron_typos = ['volltron', 'volltrron', 'voltrron', 'voltron']
        for typo in volttron_typos:
            normalized_message = normalized_message.replace(typo, 'volttron')
        
        full_context = (recent_context + " " + normalized_message).lower()
        
        # Score different interpretations based on context
        scores = {}
        for category, keywords in context_clues.items():
            scores[category] = sum(1 for keyword in keywords if keyword in full_context)
        
        # Determine most likely interpretation
        max_score = max(scores.values()) if scores.values() else 0
        
        if max_score > 0:
            # Find the category with highest score
            likely_category = max(scores, key=scores.get)
            
            # Check if there are tied scores (ambiguous context)
            tied_categories = [cat for cat, score in scores.items() if score == max_score]
            
            if len(tied_categories) > 1:
                # Ambiguous context - ask for clarification
                pass  # Fall through to clarification section
            elif likely_category == 'volttron':
                # They're asking about the VOLTTRON platform specifically
                from chat_app.volttron_commands import is_volttron_running
                return is_volttron_running()
            elif likely_category == 'agents':
                # They're asking about agents specifically
                return self.call_function_tool("vctl_status", {})
            else:
                # Default to showing everything
                return self.call_function_tool("vctl_status", {})
        
        # No clear context - ask for clarification with helpful options
        from chat_app.volttron_commands import is_volttron_running, vctl_status
        
        # Quick check if VOLTTRON is running to provide better context
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
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "provider": self.model_name.split(":")[0] if ":" in self.model_name else "unknown",
            "model_id": self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
        }
        
