from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Button, Static, RichLog, Checkbox
from textual.containers import Container, Horizontal, Vertical
from textual import work
import asyncio
import os
from main import LLMComparator
from model_manager import ModelState

class ModelItem(ListItem):
    def __init__(self, model_data: dict, initial_state: ModelState):
        super().__init__()
        self.model_data = model_data
        self.model_id = model_data["id"]
        self.current_state = initial_state

    def compose(self) -> ComposeResult:
        # Sanitize model_id for use in CSS/widget IDs (only allow a-z, A-Z, 0-9, _, -)
        import re
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', self.model_id)
        yield Horizontal(
            Checkbox(value=(self.current_state in [ModelState.AUTO, ModelState.ON])),
            Label(f"{self.model_id}", classes="model-name"),
            Label(f"({self.current_state.value})", classes="state-label"),
            id=f"item-{safe_id}"
        )

class LLMStudioTUI(App):
    CSS = """
    Screen {
        background: #1e1e2e;
    }
    #main-container {
        padding: 1;
    }
    .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
        color: #89b4fa;
    }
    #model-list {
        height: 12;
        border: solid #45475a;
        margin-bottom: 1;
    }
    ListItem {
        height: auto;
        padding: 0;
    }
    #model-list Horizontal {
        height: 3;
        align: left middle;
    }
    .model-name {
        width: 1fr;
        content-align: left middle;
    }
    #prompt-input {
        margin-bottom: 1;
    }
    #log {
        height: 1fr;
        border: solid #45475a;
        background: #181825;
    }
    .state-label {
        margin-left: 1;
        width: 10;
        color: #f38ba8;
    }
    Checkbox {
        width: auto;
        margin-right: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.comparator = LLMComparator()
        self.models = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Vertical(
                Label("Available Models", classes="section-title"),
                ListView(id="model-list"),
                Label("System Prompt", classes="section-title"),
                Input(placeholder="You are a helpful assistant...", id="system-prompt"),
                Label("User Prompt", classes="section-title"),
                Input(placeholder="Enter prompt or file path...", id="prompt-input"),
                Horizontal(
                    Button("Run Comparison", variant="primary", id="run-btn"),
                    Button("Refresh Models", id="refresh-btn"),
                ),
                RichLog(id="log", highlight=True, markup=True),
                id="main-container"
            )
        )
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_models()

    async def refresh_models(self):
        log = self.query_one("#log", RichLog)
        log.write("Fetching models from LM Studio...")
        self.models = await self.comparator.get_available_models()
        model_list = self.query_one("#model-list", ListView)
        model_list.clear()
        
        for m in self.models:
            state = self.comparator.model_manager.get_state(m["id"])
            model_list.append(ModelItem(m, state))
        
        log.write(f"Found {len(self.models)} models.")

    @work(exclusive=True)
    async def run_comparison_task(self, prompt: str, system_prompt: str, selected_ids: list):
        log = self.query_one("#log", RichLog)
        log.write(f"[bold cyan]Starting comparison for {len(selected_ids)} models...[/]")
        
        async for res in self.comparator.run_comparison(prompt, selected_ids, system_prompt):
            m_id = res["model_id"]
            if res["error"]:
                log.write(f"[red]Error with {m_id}: {res['error']['detail']}[/]")
            else:
                log.write(f"[green]SUCCESS: {m_id}[/]")
                t = res.get("timing", {})
                usage = res.get("usage", {})
                log.write(f"[dim]Load: {t.get('load_time', 0):.2f}s | Think: {t.get('think_time', 0):.2f}s | Content: {t.get('content_time', 0):.2f}s[/]")
                if usage:
                    log.write(f"[dim]Tokens: P:{usage.get('prompt_tokens', 0)} C:{usage.get('completion_tokens', 0)} T:{usage.get('total_tokens', 0)}[/]")
                if res["result"]["thinking"]:
                    log.write(f"[italic blue]Thinking:[/]")
                    log.write(res["result"]["thinking"][:300] + "...")
                log.write(f"--- Response Preview ---")
                log.write(res["result"]["content"][:300] + "...")
                log.write("-" * 20)
        
        log.write("[bold green]All finished. Results saved to /results folder.[/]")
        await self.refresh_models()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-btn":
            await self.refresh_models()
        elif event.button.id == "run-btn":
            prompt = self.query_one("#prompt-input", Input).value
            system_prompt = self.query_one("#system-prompt", Input).value
            
            # Handle file path if prompt is a file
            if os.path.exists(prompt):
                try:
                    with open(prompt, 'r') as f:
                        prompt = f.read()
                except Exception as e:
                    self.query_one("#log", RichLog).write(f"[red]Failed to read file: {e}[/]")
                    return

            if not prompt:
                self.query_one("#log", RichLog).write("[yellow]Please enter a prompt.[/]")
                return

            model_list = self.query_one("#model-list", ListView)
            selected_ids = []
            for item in model_list.children:
                checkbox = item.query_one(Checkbox)
                if checkbox.value:
                    selected_ids.append(item.model_id)

            if not selected_ids:
                self.query_one("#log", RichLog).write("[yellow]Please select at least one model.[/]")
                return

            self.run_comparison_task(prompt, system_prompt, selected_ids)

if __name__ == "__main__":
    app = LLMStudioTUI()
    app.run()
