from pydantic_ai import Agent
from typing import Optional
import os
import openai
from .volttron_commands import start_volttron, stop_volttron, check_volttron_status, read_volttron_log

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
            if ai_webapp_url and ai_api_key:
                # Use custom OpenAI-compatible API (like PNNL)
                self.custom_client = openai.OpenAI(
                    api_key=ai_api_key,
                    base_url=ai_webapp_url
                )
                # Extract just the model name without provider prefix
                self.custom_model = self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
            else:
                # Use default provider logic (OpenAI, Anthropic, etc.) with pydantic-ai
                self.agent = Agent(
                    self.model_name,
                    system_prompt=(
                        "You are a helpful AI assistant in a chat application. "
                        "Provide clear, concise, and helpful responses to user questions. "
                        "Be friendly and conversational while maintaining accuracy."
                    )
                )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI model '{self.model_name}': {str(e)}")
    
    async def generate_response(self, message: str) -> str:
        """Generate a response to the user's message."""
        try:
            if self.custom_client:
                # Use custom OpenAI-compatible API with VOLTTRON control capabilities
                response = self.custom_client.chat.completions.create(
                    model=self.custom_model,
                    messages=[
                        {"role": "system", "content": """You are a helpful AI assistant that can control VOLTTRON platform. 

You have access to these functions:
- start_volttron(): Starts the VOLTTRON platform
- stop_volttron(): Stops the VOLTTRON platform  
- check_volttron_status(): Checks VOLTTRON status and shows recent logs
- read_volttron_log(): Shows recent VOLTTRON log entries

When users ask to start, run, launch, activate, or turn on VOLTTRON (or "the platform"), call start_volttron().
When users ask to stop, shutdown, halt, kill, or turn off VOLTTRON, call stop_volttron().
When users ask about status, want to check VOLTTRON, or ask "how is VOLTTRON doing", call check_volttron_status().
When users ask about logs, want to see what happened, or ask for output, call read_volttron_log().

If you determine the user wants a VOLTTRON command, respond with exactly one of:
- EXECUTE_START_VOLTTRON
- EXECUTE_STOP_VOLTTRON  
- EXECUTE_STATUS_VOLTTRON
- EXECUTE_LOG_VOLTTRON

Otherwise, provide helpful conversational responses."""},
                        {"role": "user", "content": message}
                    ]
                )
                ai_response = response.choices[0].message.content or "No response received"
                
                # Check if AI wants to execute a VOLTTRON command
                if "EXECUTE_START_VOLTTRON" in ai_response:
                    result = start_volttron()
                    return f"✅ {result}"
                elif "EXECUTE_STOP_VOLTTRON" in ai_response:
                    result = stop_volttron()
                    return f"✅ {result}"
                elif "EXECUTE_STATUS_VOLTTRON" in ai_response:
                    result = check_volttron_status()
                    return f"📊 {result}"
                elif "EXECUTE_LOG_VOLTTRON" in ai_response:
                    result = read_volttron_log(10)
                    return f"📝 Recent VOLTTRON Log:\n{result}"
                else:
                    return ai_response
                
            elif self.agent:
                # Use pydantic-ai agent for standard providers
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