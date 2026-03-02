"""AI Service for enhanced analysis."""

import os
from dataclasses import dataclass
from typing import Any, Optional

from ..models import AnalysisResult, DirectoryInfo
from .providers import AIProvider, DeepSeekProvider, OpenAIProvider


@dataclass
class AIConfig:
    """Configuration for AI providers."""
    default_provider: str = "deepseek"
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com"


class AIService:
    """
    AI Service for enhanced directory analysis.
    
    Provides AI-powered analysis when rule-based analysis
    is insufficient.
    """
    
    def __init__(self, config: Optional[AIConfig] = None):
        """
        Initialize AI service.
        
        Args:
            config: AI configuration (default: from environment)
        """
        if config is None:
            config = AIConfig(
                default_provider=os.getenv("AI_DEFAULT_PROVIDER", "deepseek"),
                deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
                deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
            )
        
        self._config = config
        self._providers: dict[str, AIProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers."""
        if self._config.deepseek_api_key:
            self._providers["deepseek"] = DeepSeekProvider(
                api_key=self._config.deepseek_api_key,
                model=self._config.deepseek_model,
            )
        
        if self._config.openai_api_key:
            self._providers["openai"] = OpenAIProvider(
                api_key=self._config.openai_api_key,
                model=self._config.openai_model,
                base_url=self._config.openai_base_url,
            )
    
    @property
    def available(self) -> bool:
        """Check if any AI provider is available."""
        return len(self._providers) > 0
    
    def get_provider(self, name: Optional[str] = None) -> AIProvider:
        """Get a specific provider or default."""
        if name and name in self._providers:
            return self._providers[name]
        
        if self._config.default_provider in self._providers:
            return self._providers[self._config.default_provider]
        
        if self._providers:
            return next(iter(self._providers.values()))
        
        raise ValueError("No AI providers configured")
    
    async def analyze(
        self,
        directories: list[DirectoryInfo],
        user_context: Optional[str] = None,
        target_drive: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Analyze directories using AI.
        
        Args:
            directories: Directories to analyze
            user_context: User context (e.g., "Python developer")
            target_drive: Target drive for migration
            provider: Specific provider to use
            
        Returns:
            Analysis results
        """
        ai_provider = self.get_provider(provider)
        
        # Prepare data for AI
        dir_data = [
            {
                "path": d.path,
                "size_mb": d.size_mb,
                "link_type": d.link_type.value,
                "file_types": d.file_types,
            }
            for d in directories[:50]  # Limit for API
        ]
        
        result = await ai_provider.analyze(
            directories=dir_data,
            user_context=user_context,
            target_drive=target_drive,
        )
        
        return result
    
    async def get_available_providers(self) -> list[dict[str, Any]]:
        """Get list of available providers."""
        result = []
        for name, provider in self._providers.items():
            available = await provider.is_available()
            result.append({
                "name": name,
                "available": available,
                "model": provider.model,
            })
        return result
