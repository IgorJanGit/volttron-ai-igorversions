import argparse
import os
from typing import Optional
from dotenv import load_dotenv
import uvicorn

from .app import create_app

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="VOLTTRON AI Chat Application")
    parser.add_argument(
        "--model",
        type=str,
        help="AI model to use (e.g., openai:gpt-3.5-turbo, anthropic:claude-3-haiku-20240307)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    load_dotenv()
    args = parse_args()
    
    model = args.model or os.getenv("AI_MODEL")
    host = args.host or os.getenv("HOST", "127.0.0.1")
    port = args.port or int(os.getenv("PORT", "8000"))
    
    if not model:
        print("Error: No AI model specified. Use --model argument or set AI_MODEL in .env file")
        print("Example: python -m chat_app --model openai:gpt-3.5-turbo")
        return 1
    
    app = create_app(model)
    
    print(f"Starting chat app with model: {model}")
    print(f"Server will be available at: http://{host}:{port}")
    
    uvicorn.run(
        "chat_app.app:app",
        host=host,
        port=port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()