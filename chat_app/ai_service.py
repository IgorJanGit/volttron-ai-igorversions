from pydantic_ai import Agent
from typing import Optional
import os

class AIService:
    """Service for handling AI model interactions using Pydantic-AI."""
    
    def __init__(self, model_name: str):
        """Initialize the AI service with a specific model."""
        self.model_name = model_name
        self.agent = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the Pydantic-AI agent with the specified model."""
        try:
            # Create agent with the specified model
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
        if not self.agent:
            raise RuntimeError("AI agent not properly initialized")
        
        try:
            # Run the agent with the user's message
            result = await self.agent.run(message)
            return result.output
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