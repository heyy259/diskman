"""DeepSeek AI provider."""

import json
from typing import Any, Optional

import httpx

from .base import AIProvider, AIAnalysisResult


class DeepSeekProvider(AIProvider):
    """DeepSeek AI provider."""
    
    name = "deepseek"
    base_url = "https://api.deepseek.com"
    
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: Optional[str] = None,
    ):
        super().__init__(api_key, model)
        if base_url:
            self.base_url = base_url
    
    async def analyze(
        self,
        directories: list[dict[str, Any]],
        user_context: Optional[str] = None,
        target_drive: Optional[str] = None,
    ) -> dict[str, Any]:
        """Analyze using DeepSeek API."""
        prompt = self._build_prompt(directories, user_context, target_drive)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a disk space management expert. Respond only with valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                result = json.loads(content.strip())
                return {
                    "recommendations": result.get("recommendations", []),
                    "summary": result.get("summary", ""),
                    "total_releasable_mb": result.get("total_releasable_mb", 0),
                    "provider": self.name,
                }
            except json.JSONDecodeError:
                # Return raw response if JSON parsing fails
                return {
                    "recommendations": [],
                    "summary": content,
                    "total_releasable_mb": 0,
                    "provider": self.name,
                    "error": "Failed to parse AI response as JSON",
                }
    
    async def is_available(self) -> bool:
        """Check if DeepSeek API is available."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception:
            return False
