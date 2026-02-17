import httpx
from typing import List, Dict, Any, Optional

class LMStudioClient:
    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(300.0) # Long timeout for LLM generation

    async def list_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from LM Studio."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/models")
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except Exception as e:
                print(f"Error fetching models: {e}")
                return []

    async def generate(self, model_id: str, prompt: str, system_prompt: Optional[str] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a completion for the given model and prompt."""
        params = params or {}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1024),
            "stream": False
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}", "detail": e.response.text}
            except Exception as e:
                return {"error": "Connection error", "detail": str(e)}
    async def generate_stream(self, model_id: str, prompt: str, system_prompt: Optional[str] = None, params: Dict[str, Any] = None):
        """Generate a streaming completion for the given model and prompt."""
        params = params or {}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1024),
            "stream": True,
            "stream_options": {"include_usage": True}
        }

        import json
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", f"{self.base_url}/chat/completions", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                yield json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                yield {"error": "Stream error", "detail": str(e)}
