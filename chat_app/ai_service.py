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
    start_volttron, stop_volttron, check_volttron_status, read_volttron_log,
    vctl_status, vctl_status_detailed, vctl_list_agents, vctl_start_agent, vctl_stop_agent, vctl_health,
    show_formatting_test, get_detailed_installation_help, get_volttron_next_steps,
    vctl_install_platform_driver, install_fake_driver_library, create_fake_driver_config,
    store_fake_driver_config, setup_fake_driver_monitoring, subscribe_to_fake_data,
    show_recent_logs, check_volttron_installation, kill_existing_volttron_processes,
    vctl_uninstall_agent, vctl_uninstall_all_listeners, vctl_install_listener_agent,
    vctl_install_agent, list_available_agents, verify_agent_uninstalled
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
        return vctl_list_agents()

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
    def install_fake_driver_library_tool() -> str:
        """Install the fake driver library for testing."""
        return install_fake_driver_library()

    @agent.tool_plain
    def create_fake_driver_config_tool() -> str:
        """Create configuration for a fake driver."""
        return create_fake_driver_config()

    @agent.tool_plain
    def store_fake_driver_config_tool() -> str:
        """Store the fake driver configuration."""
        return store_fake_driver_config()

    @agent.tool_plain
    def setup_fake_driver_monitoring_tool() -> str:
        """Setup monitoring for the fake driver."""
        return setup_fake_driver_monitoring()

    @agent.tool_plain
    def subscribe_to_fake_data_tool() -> str:
        """Subscribe to fake driver data."""
        return subscribe_to_fake_data()

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
        if 'fake driver library' in title or 'install fake driver library' in title or 'pypi' in description:
            self.fake_driver_setup_state = "library_installed"
            return install_fake_driver_library()
        elif 'config' in title and ('create' in title or 'directory' in title or 'files' in title):
            self.fake_driver_setup_state = "config_created"
            return create_fake_driver_config()
        elif 'fake driver config' in title or 'create the fake driver config' in title:
            self.fake_driver_setup_state = "config_created"
            return create_fake_driver_config()
        elif 'current agents' in title or 'what\'s running' in title or 'show' in title and 'agents' in title:
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
        elif 'listener agent' in title or 'monitoring' in title:
            self.fake_driver_setup_state = "monitoring_setup"
            return setup_fake_driver_monitoring()
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
            self.fake_driver_setup_state = "config_created"
            return create_fake_driver_config()  # This handles directory creation
        elif 'fake.config file' in title or 'generate the fake.config' in title:
            self.fake_driver_setup_state = "config_stored"
            return store_fake_driver_config()  # This handles storing config
        elif 'fake.csv registry' in title or 'registry file' in title:
            self.fake_driver_setup_state = "monitoring_setup"
            return setup_fake_driver_monitoring()  # This completes the setup
        else:
            # More specific matching for the fake driver setup steps
            if any(word in title for word in ['install', 'library', 'fake']):
                self.fake_driver_setup_state = "library_installed"
                return install_fake_driver_library()
            elif any(word in title for word in ['create', 'config', 'directory']):
                self.fake_driver_setup_state = "config_created"
                return create_fake_driver_config()
            elif any(word in title for word in ['store', 'save', 'registry']):
                self.fake_driver_setup_state = "config_stored"
                return store_fake_driver_config()
            else:
                # Default response when we can't match
                return f"🎯 Executing option {option_num}: **{option['title']}**\n\n{option['description']}\n\nLet me know if you'd like me to help with this specific task!"
    
    def _execute_next_step(self) -> str:
        """Execute the next logical step based on current fake driver setup state."""
        
        if self.fake_driver_setup_state == "not_started":
            self.fake_driver_setup_state = "platform_driver_ready"
            return vctl_install_platform_driver()
        elif self.fake_driver_setup_state == "platform_driver_ready":
            self.fake_driver_setup_state = "library_installed"
            return install_fake_driver_library()
        elif self.fake_driver_setup_state == "library_installed":
            self.fake_driver_setup_state = "config_created"
            return create_fake_driver_config()
        elif self.fake_driver_setup_state == "config_created":
            self.fake_driver_setup_state = "config_stored"
            return store_fake_driver_config()
        elif self.fake_driver_setup_state == "config_stored":
            self.fake_driver_setup_state = "monitoring_setup"
            return setup_fake_driver_monitoring()
        elif self.fake_driver_setup_state == "monitoring_setup":
            return "🎉 **Fake driver setup is complete!** Your fake sensors are running and being monitored!\n\nWhat would you like to do next?\n1. **Check VOLTTRON status** - See how everything is running\n2. **View agent list** - See all your active agents\n3. **Check logs** - See recent activity"
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
        def install_fake_driver_library_tool() -> str:
            """Install the fake driver library for testing and development."""
            return install_fake_driver_library()
        
        @self.agent.tool_plain
        def create_fake_driver_config_tool() -> str:
            """Create configuration for fake driver devices."""
            return create_fake_driver_config()
        
        @self.agent.tool_plain
        def store_fake_driver_config_tool() -> str:
            """Store the fake driver configuration in VOLTTRON."""
            return store_fake_driver_config()
        
        @self.agent.tool_plain
        def setup_fake_driver_monitoring_tool() -> str:
            """Set up monitoring for fake driver data."""
            return setup_fake_driver_monitoring()
        
        @self.agent.tool_plain
        def subscribe_to_fake_data_tool() -> str:
            """Subscribe to fake sensor data for monitoring."""
            return subscribe_to_fake_data()
        
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
            "You are VOLTTRON AI Assistant, an intelligent assistant for VOLTTRON platform operations. "
            "You have access to comprehensive VOLTTRON management tools through function calls using the @agent.tool_plain decorator pattern. "
            "\n\nCOMPREHENSIVE TOOL CAPABILITIES:\n"
            "🏗️ PLATFORM CONTROL:\n"
            "- start_volttron_tool: Start the VOLTTRON platform\n"
            "- stop_volttron_tool: Stop the VOLTTRON platform\n"
            "- check_volttron_installation_tool: Verify VOLTTRON installation\n"
            "- kill_existing_processes_tool: Clean up existing VOLTTRON processes\n"
            "\n🔍 STATUS & MONITORING:\n"
            "- check_volttron_status_tool: Check platform status with logs\n"
            "- get_vctl_status_tool: Get detailed vctl status\n"
            "- vctl_status_detailed_tool: Get comprehensive status information\n"
            "- vctl_health_tool: Check platform health\n"
            "- show_recent_logs_tool: Show recent VOLTTRON logs\n"
            "\n🤖 AGENT MANAGEMENT:\n"
            "- list_agents_tool: List all installed agents\n"
            "- list_available_agents_tool: Show available agents for installation\n"
            "- install_agent_tool: Install agents by name\n"
            "- start_agent_tool: Start agents by UUID\n"
            "- stop_agent_tool: Stop agents by UUID\n"
            "- uninstall_agent_tool: Completely uninstall agents\n"
            "- verify_agent_uninstalled_tool: Verify agent removal\n"
            "\n🔧 SPECIALIZED INSTALLATIONS:\n"
            "- install_platform_driver_tool: Install platform driver\n"
            "- install_listener_agent_tool: Install listener agent\n"
            "- uninstall_all_listeners_tool: Remove all listener agents\n"
            "\n🧪 DEVELOPMENT & TESTING:\n"
            "- install_fake_driver_library_tool: Install fake driver for testing\n"
            "- create_fake_driver_config_tool: Create fake driver configuration\n"
            "- store_fake_driver_config_tool: Store fake driver config\n"
            "- setup_fake_driver_monitoring_tool: Set up fake data monitoring\n"
            "- subscribe_to_fake_data_tool: Subscribe to fake sensor data\n"
            "\n📚 HELP & GUIDANCE:\n"
            "- get_volttron_help_tool: Get detailed installation help\n"
            "- get_volttron_next_steps_tool: Get suggested next steps\n"
            "- show_formatting_test_tool: Test output formatting\n"
            "\n📋 USAGE GUIDELINES:\n"
            "✅ ALWAYS use the function tools to perform VOLTTRON operations\n"
            "✅ Execute commands rather than just providing instructions\n"
            "✅ Check actual status and provide real-time information\n"
            "✅ Use comprehensive verification tools when requested\n"
            "✅ Provide step-by-step guidance using actual tool execution\n"
            "\n🎯 PYDANTIC AI PATTERN:\n"
            "All tools are registered using @agent.tool_plain decorators for seamless AI integration. "
            "The AI automatically determines which tools to call based on user requests and provides "
            "comprehensive VOLTTRON platform management capabilities."
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
                r"check.*status": "vctl_status", 
                r"start.*volttron": "start_volttron",
                r"stop.*volttron": "stop_volttron",
                r"list.*agents": "vctl_list_agents",
                r"install.*driver": "install_fake_driver_library",
                r"install.*agent": "vctl_install_listener_agent",
                r"show.*logs": "show_recent_logs",
                r"health.*check": "vctl_health"
            }
            
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
                            executed_commands.append(f"\n📋 {function_name}:\n{result}")
                    except Exception as e:
                        executed_commands.append(f"\n❌ Error executing {function_name}: {e}")
            
            # Append command results to AI response
            if executed_commands:
                ai_response += "\n\n🤖 **Command Execution Results:**" + "".join(executed_commands)
            
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
        
        # Status commands
        if message_lower in ['status', 'vctl status', 'agent status', 'check status']:
            return self.call_function_tool("vctl_status", {})
        elif message_lower in ['volttron status', 'platform status', 'check volttron']:
            return self.call_function_tool("check_volttron_status", {})
        
        # Start/Stop commands
        elif message_lower in ['start volttron', 'start platform']:
            return self.call_function_tool("start_volttron", {})
        elif message_lower in ['stop volttron', 'stop platform']:
            return self.call_function_tool("stop_volttron", {})
        
        # Install commands
        elif message_lower in ['install listener', 'install listener agent']:
            return self.call_function_tool("vctl_install_listener_agent", {})
        
        # List commands
        elif message_lower in ['list agents', 'available agents', 'what agents']:
            return self.call_function_tool("list_available_agents", {})
        
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
        
        # Pattern matching for start/stop agent commands
        start_patterns = [
            r'start\s+(\w+)',
            r'start\s+agent\s+(\w+)'
        ]
        
        for pattern in start_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                if agent_id and agent_id not in ['agent', 'volttron', 'platform']:
                    return self.call_function_tool("vctl_start_agent", {"agent_uuid_or_tag": agent_id})
        
        stop_patterns = [
            r'stop\s+(\w+)',
            r'stop\s+agent\s+(\w+)'
        ]
        
        for pattern in stop_patterns:
            match = re.search(pattern, message_lower)
            if match:
                agent_id = match.group(1)
                if agent_id and agent_id not in ['agent', 'volttron', 'platform']:
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
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "provider": self.model_name.split(":")[0] if ":" in self.model_name else "unknown",
            "model_id": self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
        }
        
