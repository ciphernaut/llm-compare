import asyncio
from typing import List, Dict, Any, Optional
from api_client import LMStudioClient
from model_manager import ModelManager, ModelState
from storage import ComparisonStorage

class LLMComparator:
    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.client = LMStudioClient(base_url)
        self.model_manager = ModelManager()
        self.storage = ComparisonStorage()

    async def run_comparison(self, 
                             prompt: str, 
                             selected_model_ids: List[str], 
                             system_prompt: Optional[str] = None, 
                             params: Dict[str, Any] = None):
        import re
        all_results = []
        for model_id in selected_model_ids:
            # Record state before run
            state_before = self.model_manager.get_state(model_id)
            
            response = await self.client.generate(model_id, prompt, system_prompt, params)
            
            model_entry = {
                "model_id": model_id,
                "state_before_run": state_before,
                "parameters": params or {},
                "result": None,
                "error": None
            }
            
            if "error" in response:
                model_entry["error"] = response
                self.model_manager.mark_failure(model_id)
            else:
                content = response["choices"][0]["message"]["content"]
                
                # Extract thinking blocks (DeepSeek style)
                thinking = ""
                think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
                if think_match:
                    thinking = think_match.group(1).strip()
                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

                model_entry["result"] = {
                    "content": content,
                    "thinking": thinking,
                    "usage": response.get("usage", {}),
                    "model_name": response.get("model", model_id)
                }
            
            all_results.append(model_entry)
            yield model_entry # Yield individual results for real-time UI updates
            
        # Final save of all results
        self.storage.save_comparison(prompt, all_results, system_prompt, params)

    async def get_available_models(self) -> List[Dict[str, Any]]:
        return await self.client.list_models()
