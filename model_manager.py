import json
import os
from enum import Enum
from typing import Dict, Any, List

class ModelState(str, Enum):
    AUTO = "AUTO"
    ON = "ON"
    OFF = "OFF"
    AUTO_OFF = "AUTO-OFF"

class ModelManager:
    def __init__(self, config_path: str = "model_states.json"):
        self.config_path = config_path
        self.states: Dict[str, str] = self._load_states()

    def _load_states(self) -> Dict[str, str]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_states(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.states, f, indent=2)

    def get_state(self, model_id: str) -> ModelState:
        return ModelState(self.states.get(model_id, ModelState.AUTO))

    def set_state(self, model_id: str, state: ModelState):
        self.states[model_id] = state.value
        self.save_states()

    def mark_failure(self, model_id: str):
        """Transition AUTO to AUTO-OFF on failure. Sticky states remain unchanged."""
        current = self.get_state(model_id)
        if current == ModelState.AUTO:
            self.set_state(model_id, ModelState.AUTO_OFF)

    def get_participating_models(self, available_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter models based on their states."""
        participating = []
        for model in available_models:
            model_id = model["id"]
            state = self.get_state(model_id)
            if state in [ModelState.AUTO, ModelState.ON]:
                participating.append(model)
        return participating
