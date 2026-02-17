import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import asyncio
import threading
import os
from main import LLMComparator
from model_manager import ModelState

class ModelRow(Adw.ActionRow):
    def __init__(self, model_id, state):
        super().__init__(title=model_id)
        self.model_id = model_id
        self.switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.switch.set_active(state in [ModelState.AUTO, ModelState.ON])
        self.add_suffix(self.switch)
        self.set_subtitle(f"State: {state.value}")

class ResultRow(Adw.ExpanderRow):
    def __init__(self, model_id):
        super().__init__(title=model_id)
        self.content_label = Gtk.Label(label="Waiting...", wrap=True, xalign=0, selectable=True)
        self.content_label.set_margin_start(12)
        self.content_label.set_margin_end(12)
        self.content_label.set_margin_top(6)
        self.content_label.set_margin_bottom(6)
        
        self.add_row(self.content_label)
        self.thinking_label = None

    def update(self, content, thinking=None):
        self.content_label.set_text(content)
        if thinking:
            if not self.thinking_label:
                self.thinking_label = Gtk.Label(label="", wrap=True, xalign=0, selectable=True)
                self.thinking_label.set_margin_start(12)
                self.thinking_label.set_margin_end(12)
                self.thinking_label.set_margin_bottom(12)
                # Apply monospace and different color for thinking
                self.thinking_label.add_css_class("dim-label")
                self.thinking_label.set_markup(f"<i>Thinking:</i>\n<tt>{GLib.markup_escape_text(thinking)}</tt>")
                self.add_row(self.thinking_label)
            else:
                self.thinking_label.set_markup(f"<i>Thinking:</i>\n<tt>{GLib.markup_escape_text(thinking)}</tt>")

class LLMComparatorApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='com.example.LLMComparator', **kwargs)
        self.comparator = LLMComparator()
        self.loop = asyncio.new_event_loop()
        self.worker_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.worker_thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def do_activate(self):
        builder = Gtk.Builder()
        # Minimal UI structure in code
        self.window = Adw.ApplicationWindow(application=self, title="LLM Comparator")
        self.window.set_default_size(800, 600)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.set_content(main_box)

        header = Adw.HeaderBar()
        main_box.append(header)

        # Setup Page
        self.stack = Gtk.Stack()
        main_box.append(self.stack)

        setup_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        setup_page.set_margin_start(24)
        setup_page.set_margin_end(24)
        setup_page.set_margin_top(24)
        setup_page.set_margin_bottom(24)
        self.stack.add_titled(setup_page, "setup", "Setup")

        # Configuration List
        config_group = Adw.PreferencesGroup(title="Configuration")
        setup_page.append(config_group)

        self.system_prompt_entry = Adw.EntryRow(title="System Prompt")
        self.system_prompt_entry.set_text("You are a helpful assistant")
        config_group.add(self.system_prompt_entry)

        self.user_prompt_entry = Adw.EntryRow(title="User Prompt")
        self.user_prompt_entry.set_text("Explain quantum computing in 2 sentences.")
        config_group.add(self.user_prompt_entry)

        # Model List Scrolled Window
        model_scroll = Gtk.ScrolledWindow()
        model_scroll.set_vexpand(True)
        model_scroll.set_propagate_natural_height(True)
        model_scroll.set_min_content_height(300)
        setup_page.append(model_scroll)

        self.model_group = Adw.PreferencesGroup(title="Available Models")
        model_scroll.set_child(self.model_group)
        
        self.model_rows = {}
        self.result_rows = {}

        # Run Button
        run_btn = Gtk.Button(label="Run Comparison", halign=Gtk.Align.CENTER)
        run_btn.add_css_class("suggested-action")
        run_btn.set_margin_top(24)
        run_btn.connect("clicked", self.on_run_clicked)
        setup_page.append(run_btn)

        # Results Page
        results_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        results_page.set_margin_start(12)
        results_page.set_margin_end(12)
        results_page.set_margin_top(12)
        results_page.set_margin_bottom(12)
        self.stack.add_titled(results_page, "results", "Results")

        # Status Badge/Header
        self.status_banner = Adw.Banner(title="Processing Comparisons...", visible=False)
        results_page.append(self.status_banner)

        # Scrolled Window for Results
        res_scroll = Gtk.ScrolledWindow()
        res_scroll.set_vexpand(True)
        results_page.append(res_scroll)

        self.results_group = Adw.PreferencesGroup(title="Comparison Results")
        res_scroll.set_child(self.results_group)

        # Footer with Back Button
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        back_btn = Gtk.Button(label="Back to Setup")
        back_btn.set_icon_name("go-previous-symbolic")
        back_btn.connect("clicked", lambda x: self.stack.set_visible_child_name("setup"))
        footer.append(back_btn)
        results_page.append(footer)

        self.window.present()
        self.load_models()

    def load_models(self):
        async def fetch():
            models = await self.comparator.get_available_models()
            GLib.idle_add(self.update_model_list, models)

        asyncio.run_coroutine_threadsafe(fetch(), self.loop)

    def update_model_list(self, models):
        for m in models:
            m_id = m["id"]
            state = self.comparator.model_manager.get_state(m_id)
            row = ModelRow(m_id, state)
            self.model_group.add(row)
            self.model_rows[m_id] = row

    def on_run_clicked(self, btn):
        prompt = self.user_prompt_entry.get_text()
        system_prompt = self.system_prompt_entry.get_text()
        selected_ids = [m_id for m_id, row in self.model_rows.items() if row.switch.get_active()]

        if not selected_ids:
            return

        # Clear old results safely by removing only the ResultRows
        for row in list(self.result_rows.values()):
            self.results_group.remove(row)

        self.result_rows = {}
        for m_id in selected_ids:
            row = ResultRow(m_id)
            self.results_group.add(row)
            self.result_rows[m_id] = row

        self.status_banner.set_visible(True)
        self.stack.set_visible_child_name("results")
        
        asyncio.run_coroutine_threadsafe(
            self.run_comparison(prompt, system_prompt, selected_ids), 
            self.loop
        )

    async def run_comparison(self, prompt, system_prompt, selected_ids):
        async for res in self.comparator.run_comparison(prompt, selected_ids, system_prompt):
            GLib.idle_add(self.update_result, res)
        GLib.idle_add(lambda: self.status_banner.set_visible(False))

    def update_result(self, res):
        m_id = res["model_id"]
        row = self.result_rows.get(m_id)
        if not row: return

        if res["error"]:
            row.update(f"Error: {res['error']['detail']}")
            row.set_subtitle("Failed")
        else:
            row.update(res["result"]["content"], res["result"]["thinking"])
            row.set_subtitle("Completed")

if __name__ == '__main__':
    app = LLMComparatorApp()
    app.run(None)
