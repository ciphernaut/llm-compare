# LLM Comparison Tool

A Python-based Terminal User Interface (TUI) for comparing responses from various LLMs hosted locally on an [LM Studio](https://lmstudio.ai/) server.

## Features

- **Interactive TUI**: Easily select models, input system prompts, and user prompts (text or file-based).
- **VRAM Efficient**: Processes models sequentially to avoid GPU memory overflows.
- **Smart Model States**:
  - `AUTO`: Included in comparison by default.
  - `ON`: Sticky inclusion.
  - `OFF`: Sticky exclusion.
  - `AUTO-OFF`: Automatically disabled if a run fails (prevents repetitive timeouts).
- **DeepSeek Support**: Automatically extracts and displays `<think>` blocks separately.
- **Real-time Previews**: View results as they arrive without waiting for the entire batch.
- **Persistent Logs**: Saves every comparison to a timestamped JSON file in the `results/` directory.

## Installation

1. **Prerequisites**:
   - Python 3.10+
   - LM Studio running with the Local Server enabled (default `http://localhost:1234`).

2. **Dependencies**:
   ```bash
   pip install httpx textual openai
   ```

## Usage

### Terminal Interface (TUI)
1. Start the TUI:
   ```bash
   python ui.py
   ```

### GNOME Interface (GUI)
1. Start the native GNOME app:
   ```bash
   python gui.py
   ```
   *Note: Requires GTK4 and Libadwaita installed on the host system.*
2. **Refresh Models**: Click the button to sync with your LM Studio instance.
3. **Select Models**: Use the checkboxes to choose participants.
4. **Enter Prompt**: Type your query or provide an absolute path to a text file.
5. **Run**: Click "Run Comparison" and watch the logs for real-time results.

## Project Structure

- `ui.py`: The Textual-based user interface.
- `main.py`: Orchestration logic and response processing.
- `api_client.py`: Async client for LM Studio's OpenAI-compatible API.
- `model_manager.py`: Manages model states and persistence (`model_states.json`).
- `storage.py`: Handles JSON serialization of results.

## Data Schema

Results are saved as:
```json
{
  "comparison_id": "...",
  "timestamp": "...",
  "prompt": { "system": "...", "user": "..." },
  "results": [
    {
      "model_id": "...",
      "result": {
        "content": "Final answer...",
        "thinking": "Chain of thought...",
        "usage": { ... }
      }
    }
  ]
}
```
