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
        import time
        all_results = []
        for model_id in selected_model_ids:
            state_before = self.model_manager.get_state(model_id)
            
            start_time = time.time()
            first_chunk_time = None
            think_start_time = None
            think_end_time = None
            content_start_time = None
            
            full_content = ""
            thinking = ""
            in_thinking = False
            
            model_entry = {
                "model_id": model_id,
                "state_before_run": state_before,
                "parameters": params or {},
                "result": None,
                "error": None,
                "timing": {}
            }

            try:
                async for chunk in self.client.generate_stream(model_id, prompt, system_prompt, params):
                    if not first_chunk_time:
                        first_chunk_time = time.time()
                    
                    if "error" in chunk:
                        model_entry["error"] = chunk
                        self.model_manager.mark_failure(model_id)
                        break
                    
                    # Store usage if present (usually in the last chunk with stream_options)
                    if "usage" in chunk:
                        model_entry["timing"]["usage"] = chunk["usage"]

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                        
                    delta = choices[0].get("delta", {})
                    content_chunk = delta.get("content", "")
                    
                    if content_chunk:
                        full_content += content_chunk
                        
                        # Timing and logic for thinking vs content
                        if "<think>" in content_chunk:
                            in_thinking = True
                            think_start_time = time.time()
                        
                        if "</think>" in content_chunk:
                            in_thinking = False
                            think_end_time = time.time()
                            content_start_time = time.time()
                        
                        if not in_thinking and not content_start_time and content_chunk.strip():
                            content_start_time = time.time()

                end_time = time.time()
                
                if not model_entry["error"]:
                    # Post-process thinking and content
                    think_match = re.search(r'<think>(.*?)</think>', full_content, re.DOTALL)
                    if think_match:
                        thinking = think_match.group(1).strip()
                        content = re.sub(r'<think>.*?</think>', '', full_content, flags=re.DOTALL).strip()
                    else:
                        content = full_content.strip()

                    model_entry["timing"] = {
                        "load_time": (first_chunk_time - start_time) if first_chunk_time else 0,
                        "think_time": (think_end_time - think_start_time) if (think_end_time and think_start_time) else 0,
                        "content_time": (end_time - (content_start_time or first_chunk_time)) if first_chunk_time else 0,
                        "total_time": end_time - start_time
                    }

                    model_entry["result"] = {
                        "content": content,
                        "thinking": thinking,
                        "model_name": model_id
                    }
            except Exception as e:
                model_entry["error"] = {"error": "Processing error", "detail": str(e)}
                self.model_manager.mark_failure(model_id)

            all_results.append(model_entry)
            yield model_entry
            
        self.storage.save_comparison(prompt, all_results, system_prompt, params)

    async def get_available_models(self) -> List[Dict[str, Any]]:
        return await self.client.list_models()
