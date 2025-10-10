from pydantic_ai import Agent
from typing import Optional
import os
import openai
from .volttron_commands import start_volttron, stop_volttron, check_volttron_status, read_volttron_log, get_vctl_status

class AIService:
    """Service for handling AI model interactions using Pydantic-AI."""
    
    def __init__(self, model_name: str):
        """Initialize the AI service with a specific model."""
        self.model_name = model_name
        self.agent = None
        self.custom_client = None
        self._setup_agent()
    
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
                from pydantic_ai.models.openai import OpenAIChatModel
                from pydantic_ai.providers.ollama import OllamaProvider
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
                # Use default provider logic (OpenAI, Anthropic, etc.) with pydantic-ai
                self.agent = Agent(
                    self.model_name,
                    system_prompt=self._get_volttron_system_prompt()
                )
                self._register_volttron_tools()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI model '{self.model_name}': {str(e)}")
    
    def _create_agent_with_tools(self):
        """Create an agent for custom client usage with tools."""
        agent = Agent(
            self.model_name,
            system_prompt=self._get_volttron_system_prompt()
        )
        self._register_volttron_tools_on_agent(agent)
        return agent
    
    def _register_volttron_tools(self):
        """Register VOLTTRON control tools with the agent."""
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
            return get_vctl_status()
        
        @self.agent.tool_plain
        def read_volttron_log_tool(num_lines: int = 10) -> str:
            """Read recent VOLTTRON log entries.
            
            Args:
                num_lines: Number of recent log lines to read (default: 10)
            """
            return read_volttron_log(num_lines)
    
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
        def get_vctl_status_tool() -> str:
            """Get VOLTTRON platform status using vctl status command."""
            return get_vctl_status()
        
        @agent.tool_plain
        def read_volttron_log_tool(num_lines: int = 10) -> str:
            """Read recent VOLTTRON log entries.
            
            Args:
                num_lines: Number of recent log lines to read (default: 10)
            """
            return read_volttron_log(num_lines)
    
    def _get_volttron_system_prompt(self) -> str:
        """Get the unified VOLTTRON system prompt for all AI models."""
        return """You are a helpful AI assistant that can control the VOLTTRON platform.

You have access to these tools:
- start_volttron_tool(): Start the VOLTTRON platform
- stop_volttron_tool(): Stop the VOLTTRON platform  
- check_volttron_status_tool(): Check VOLTTRON platform status and show recent logs
- get_vctl_status_tool(): Get VOLTTRON platform status using vctl status command
- read_volttron_log_tool(num_lines): Read recent VOLTTRON log entries

When users ask to start, run, launch, activate, or turn on VOLTTRON (or "the platform"), use start_volttron_tool().
When users ask to stop, shutdown, halt, kill, or turn off VOLTTRON, use stop_volttron_tool().
When users ask about status, want to check VOLTTRON, or ask "how is VOLTTRON doing", use check_volttron_status_tool().
When users specifically ask for "vctl status" or want the official platform status, use get_vctl_status_tool().
When users ask about logs, want to see what happened, or ask for output, use read_volttron_log_tool().

Use the appropriate tools to perform VOLTTRON operations when requested. For general conversation, respond normally without using tools."""
    
    async def generate_response(self, message: str) -> str:
        """Generate a response to the user's message."""
        try:
            if self.custom_client and not self.agent:
                # Legacy custom client without tools (fallback)
                response = self.custom_client.chat.completions.create(
                    model=self.custom_model,
                    messages=[
                        {"role": "system", "content": self._get_volttron_system_prompt()},
                        {"role": "user", "content": message}
                    ]
                )
                return response.choices[0].message.content or "No response received"
            elif self.agent:
                # Use pydantic-ai agent with tools for all models
                result = await self.agent.run(message)
                return result.output
            else:
                return "Error: No AI service initialized"
        except Exception as e:
            # Provide a user-friendly error message
            error_msg = str(e)
            if "api key" in error_msg.lower():
                return "Error: Missing or invalid API key. Please check your environment configuration."
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return "Error: API quota exceeded or rate limit reached. Please try again later."
            elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                return f"Error: Model '{self.model_name}' not found or not accessible."
            else:
                return f"Error: Unable to generate response. {error_msg}"
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "provider": self.model_name.split(":")[0] if ":" in self.model_name else "unknown",
            "model_id": self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
        }