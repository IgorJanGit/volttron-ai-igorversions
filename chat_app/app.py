from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os

from .ai_service import AIService
from .volttron_commands import start_volttron, stop_volttron

# Global app instance
app = None

class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    user: str = "user"

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    model: str

def create_app(model_name: str) -> FastAPI:
    """Create and configure the FastAPI application."""
    global app
    
    app = FastAPI(
        title="VOLTTRON AI Chat",
        description="A chat application powered by AI models",
        version="1.0.0"
    )
    
    # Initialize AI service
    ai_service = AIService(model_name)
    
    # Store AI service in app state
    app.state.ai_service = ai_service
    app.state.model_name = model_name
    
    # Setup templates
    import os
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = Jinja2Templates(directory=template_dir)
    
    @app.get("/", response_class=HTMLResponse)
    async def chat_interface(request: Request):
        """Serve the chat interface."""
        return templates.TemplateResponse("chat.html", {
            "request": request, 
            "model_name": model_name
        })
    
    @app.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(chat_message: ChatMessage):
        """Handle chat messages."""
        try:
            response = await ai_service.generate_response(chat_message.message)
            return ChatResponse(response=response, model=model_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "model": model_name}
    
    @app.get("/models")
    async def get_available_models():
        """Get information about available models."""
        return {
            "current_model": model_name,
            "supported_providers": [
                "openai (e.g., openai:gpt-3.5-turbo, openai:gpt-4)",
                "anthropic (e.g., anthropic:claude-3-haiku-20240307)",
                "groq (e.g., groq:mixtral-8x7b-32768)"
            ]
        }
    
    @app.post("/volttron/start")
    async def start_volttron_endpoint():
        """Start VOLTTRON platform."""
        try:
            result = start_volttron()
            return {"status": "success", "message": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error starting VOLTTRON: {str(e)}")
    
    @app.post("/volttron/stop")
    async def stop_volttron_endpoint():
        """Stop VOLTTRON platform."""
        try:
            result = stop_volttron()
            return {"status": "success", "message": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error stopping VOLTTRON: {str(e)}")
    
    return app