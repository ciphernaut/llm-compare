# LLM Comparison Tool

A multi-interface tool for comparing responses from various LLMs hosted locally on an [LM Studio](https://lmstudio.ai/) server. Features both a Terminal User Interface (TUI) and a native GNOME GUI.

## Features

- **Dual Interfaces**: 
  - **TUI**: Fast, terminal-based experience using Textual.
  - **GNOME GUI**: Modern, native Linux experience using GTK4 and Libadwaita.
- **VRAM Efficient**: Processes models sequentially to manage GPU resources effectively.
- **Performance Metrics**:
  - **Load Time**: Time taken to load the model and receive the first token.
  - **Think Time**: Time spent in the model's "thinking" phase (e.g., DeepSeek R1).
  - **Content Time**: Time spent generating the final response.
- **Token Analytics**: Captures Prompt, Completion, and Total token counts per run.
- **Smart Model States**:
  - `AUTO`: Included by default.
  - `ON`: Sticky inclusion.
  - `OFF`: Sticky exclusion.
  - `AUTO-OFF`: Automatically disabled if a run fails (prevents repetitive timeouts).
- **DeepSeek Support**: Automatically extracts and displays `<think>` blocks separately.
- **Real-time Previews**: View results as they stream in.
- **Persistent Storage**: Saves all comparisons to timestamped JSON files in the `results/` directory.

## Installation

1. **Prerequisites**:
   - Python 3.10+
   - LM Studio running with the Local Server enabled (default `http://localhost:1234`).
   - For GUI: GTK4 and Libadwaita (standard on modern GNOME-based distros).

2. **Dependencies**:
   ```bash
   pip install httpx textual openai
   ```
   *Note: For the GNOME GUI, you may also need `PyGObject` (usually available via system package manager as `python3-gi`).*

## Usage

### Terminal Interface (TUI)
```bash
python ui.py
```

### GNOME Interface (GUI)
```bash
python gui.py
```

### General Workflow
1. **Refresh Models**: Sync with your LM Studio instance.
2. **Select Models**: Use checkboxes/switches to choose participants.
3. **Enter Prompt**: Type your query or providing an absolute path to a text file.
4. **Run**: Click "Run Comparison" to start the sequential batch.

## Project Structure

- `ui.py`: The Textual-based terminal interface.
- `gui.py`: The GTK4/Libadwaita-based native GNOME interface.
- `main.py`: Core orchestrator involving streaming and timing logic.
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
      "timing": {
        "load_time": 1.23,
        "think_time": 5.45,
        "content_time": 10.12,
        "total_time": 16.8
      },
      "usage": {
        "prompt_tokens": 50,
        "completion_tokens": 200,
        "total_tokens": 250
      },
      "result": {
        "content": "Final answer...",
        "thinking": "Chain of thought..."
      }
    }
  ]
}
```
