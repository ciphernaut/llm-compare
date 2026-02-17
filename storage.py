import json
import datetime
import uuid
import os
from typing import Dict, Any, List, Optional

class ComparisonStorage:
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def save_comparison(self, 
                        prompt: str, 
                        models_results: List[Dict[str, Any]], 
                        system_prompt: Optional[str] = None,
                        global_params: Dict[str, Any] = None) -> str:
        
        comparison_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        data = {
            "comparison_id": comparison_id,
            "timestamp": timestamp,
            "prompt": {
                "system": system_prompt,
                "user": prompt
            },
            "global_parameters": global_params or {},
            "results": models_results
        }
        
        filename = f"comparison_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{comparison_id[:8]}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        return filepath
