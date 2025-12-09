from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import subprocess

from .ai_service import AIService

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
    
    ai_service = AIService(model_name)
    app.state.ai_service = ai_service
    app.state.model_name = model_name
    
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
    
    @app.get("/favicon.ico")
    async def favicon():
        """
        Favicon endpoint - returns 404 by default.
        
        Note: The browser automatically requests /favicon.ico for the tab icon.
        This 404 response is purely cosmetic and does not affect functionality.
        You can safely ignore "GET /favicon.ico HTTP/1.1 404" in logs.
        """
        raise HTTPException(status_code=404, detail="No favicon configured")
    
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
        volttron_version = "Unknown"
        
        possible_pips = [
            os.path.expanduser("~/volttron-v11-py311/bin/pip"),
            os.path.expanduser("~/volttron-fresh/venv-fresh/bin/pip"),
        ]
        
        for pip_path in possible_pips:
            if os.path.exists(pip_path):
                try:
                    for package in ["volttron-core", "volttron"]:
                        result = subprocess.run(
                            [pip_path, "show", package],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if result.returncode == 0 and result.stdout:
                            for line in result.stdout.split("\n"):
                                if line.startswith("Version:"):
                                    volttron_version = line.split(":", 1)[1].strip()
                                    break
                            
                            if volttron_version != "Unknown":
                                break
                    
                    if volttron_version != "Unknown":
                        break
                except Exception:
                    continue
        
        return {
            "status": "healthy",
            "volttron": volttron_version,
            "model": model_name
        }
    
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
    
    return app