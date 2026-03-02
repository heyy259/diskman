"""HTTP client for diskman API."""

import os
from typing import Any, Optional

import httpx


class APIClient:
    """HTTP client for diskman API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize client.
        
        Args:
            base_url: API base URL (default: from environment)
            api_key: API key (default: from environment)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("DISKMAN_API_URL", "http://localhost:8765")
        self.api_key = api_key or os.getenv("DISKMAN_API_KEY")
        self.timeout = timeout
    
    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    async def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_providers(self) -> list[dict[str, Any]]:
        """Get available AI providers."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/providers",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()
    
    async def analyze(
        self,
        directories: list[dict[str, Any]],
        user_context: Optional[str] = None,
        target_drive: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Analyze directories using AI.
        
        Args:
            directories: List of directory info
            user_context: User context
            target_drive: Target drive for migration
            provider: Specific AI provider to use
            
        Returns:
            Analysis result
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/analyze",
                headers=self._get_headers(),
                json={
                    "directories": directories,
                    "user_context": user_context,
                    "target_drive": target_drive,
                    "provider": provider,
                },
            )
            response.raise_for_status()
            return response.json()
