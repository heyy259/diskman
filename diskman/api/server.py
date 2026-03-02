"""FastAPI server for diskman."""

import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

from ..ai import AIService, AIConfig
from ..analysis import DirectoryAnalyzer
from ..models import DirectoryInfo


# Configuration
AI_CONFIG = AIConfig(
    default_provider=os.getenv("AI_DEFAULT_PROVIDER", "deepseek"),
    deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
    deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
)

API_KEYS = set(
    os.getenv("DISKMAN_API_KEYS", "").split(",")
) if os.getenv("DISKMAN_API_KEYS") else set()


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    app.state.ai_service = AIService(AI_CONFIG)
    app.state.analyzer = DirectoryAnalyzer()
    yield


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Diskman API",
        description="AI-ready disk space analysis and management",
        version="0.2.0",
        lifespan=lifespan,
    )
    
    # Register routes
    setup_routes(app)
    
    return app


def setup_routes(app: FastAPI):
    """Setup API routes."""
    
    def verify_api_key(api_key: Optional[str]) -> bool:
        if not API_KEYS:
            return True
        return api_key in API_KEYS
    
    @app.get("/health")
    async def health_check():
        """Health check."""
        return {"status": "ok", "version": "0.2.0"}
    
    @app.get("/providers")
    async def list_providers(x_api_key: Optional[str] = Header(None)):
        """List available AI providers."""
        if not verify_api_key(x_api_key):
            raise HTTPException(401, "Invalid API key")
        return await app.state.ai_service.get_available_providers()
    
    class AnalyzeRequest(BaseModel):
        """Request for analysis."""
        directories: list[dict[str, Any]]
        user_context: Optional[str] = None
        target_drive: Optional[str] = None
        provider: Optional[str] = None
    
    @app.post("/analyze")
    async def analyze(
        request: AnalyzeRequest,
        x_api_key: Optional[str] = Header(None),
    ):
        """Analyze directories using AI."""
        if not verify_api_key(x_api_key):
            raise HTTPException(401, "Invalid API key")
        
        if not app.state.ai_service.available:
            raise HTTPException(503, "No AI providers configured")
        
        try:
            # Convert to DirectoryInfo objects
            directories = [
                DirectoryInfo(
                    path=d["path"],
                    size_bytes=int(d.get("size_mb", 0) * 1024 * 1024),
                )
                for d in request.directories
            ]
            
            result = await app.state.ai_service.analyze(
                directories=directories,
                user_context=request.user_context,
                target_drive=request.target_drive,
                provider=request.provider,
            )
            return result
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, f"Analysis failed: {str(e)}")


def run_server(host: str = "0.0.0.0", port: int = 8765):
    """Run the API server."""
    import uvicorn
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
