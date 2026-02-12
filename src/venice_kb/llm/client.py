"""OpenAI-compatible client for LLM operations."""

from openai import AsyncOpenAI
from venice_kb.config import LLM_BASE_URL, LLM_MODEL, VENICE_API_KEY
from venice_kb.utils.logging import logger


class LLMClient:
    """OpenAI-compatible LLM client for Venice API."""
    
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        """Initialize LLM client.
        
        Args:
            api_key: API key (uses VENICE_API_KEY if not provided)
            base_url: Base URL (uses LLM_BASE_URL if not provided)
            model: Model name (uses LLM_MODEL if not provided)
        """
        self.api_key = api_key or VENICE_API_KEY
        self.base_url = base_url or LLM_BASE_URL
        self.model = model or LLM_MODEL
        
        if not self.api_key:
            logger.warning("No API key provided - LLM features will be disabled")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
    
    async def complete(self, prompt: str, system: str | None = None, max_tokens: int = 1000) -> str | None:
        """Generate a completion.
        
        Args:
            prompt: User prompt
            system: Optional system message
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if client not available
        """
        if not self.client:
            logger.warning("LLM client not available")
            return None
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            return None
    
    async def summarize_diff(self, old_content: str, new_content: str, title: str) -> str | None:
        """Summarize differences between two versions.
        
        Args:
            old_content: Old version content
            new_content: New version content
            title: Page title
            
        Returns:
            Summary of changes or None
        """
        system = "You are an expert at analyzing documentation changes and identifying breaking changes, new features, and important updates."
        
        prompt = f"""Summarize what changed between these two versions of the '{title}' documentation page.
Focus on:
- API-breaking changes (removed endpoints, changed schemas, new required parameters)
- New features or endpoints
- Deprecations
- Behavior changes

Old version:
{old_content[:2000]}

New version:
{new_content[:2000]}

Provide a concise 2-3 sentence summary."""
        
        return await self.complete(prompt, system, max_tokens=200)


# Global client instance
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
