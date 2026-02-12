from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import requests

from .client import IncidentIQClient
from .config import deobfuscate, load_config, obfuscate, save_config

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class IncidentIQDesktop(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("IncidentIQ Mass Assigner")
        self.geometry("1200x760")

        self.config_data = load_config()
        self.selected_person: dict | None = None
        self.people_results: list[dict] = []
        self.unassigned_assets: list[dict] = []

        self._build_header()
        self._build_tabs()
        self._hydrate_settings()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="Muskogee IncidentIQ Command Center",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left", padx=20, pady=12)

        self.status_label = ctk.CTkLabel(header, text="Ready", text_color="lightgreen")
        self.status_label.pack(side="right", padx=20)

    def _build_tabs(self) -> None:
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(expand=True, fill="both", padx=16, pady=16)

        self.tab_dashboard = self.tabs.add("Dashboard")
        self.tab_mass_assign = self.tabs.add("Mass Assign")
        self.tab_timeline = self.tabs.add("Timeline")
        self.tab_settings = self.tabs.add("Settings")

        self._build_dashboard_tab()
        self._build_mass_assign_tab()
        self._build_timeline_tab()
        self._build_settings_tab()

    def _build_dashboard_tab(self) -> None:
        frame = ctk.CTkFrame(self.tab_dashboard)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.dashboard_stats = ctk.CTkTextbox(frame)
        self.dashboard_stats.pack(fill="both", expand=True, padx=8, pady=8)
        self.dashboard_stats.insert(
            "1.0",
            "Welcome. Use Mass Assign to locate a staff member, load unassigned Chromebooks, and assign in one action.\n"
            "Then jump to Timeline to review their activity history.",
        )

    def _build_mass_assign_tab(self) -> None:
        top = ctk.CTkFrame(self.tab_mass_assign)
        top.pack(fill="x", padx=10, pady=10)

        self.person_search = ctk.CTkEntry(top, width=360, placeholder_text="Search teacher/staff by full name")
        self.person_search.pack(side="left", padx=8, pady=8)
        ctk.CTkButton(top, text="Search", command=self.search_people).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Load Unassigned Chromebooks", command=self.load_unassigned).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Mass Assign Selected", fg_color="#0b7a43", hover_color="#095b32", command=self.mass_assign).pack(side="left", padx=8)

        body = ctk.CTkFrame(self.tab_mass_assign)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ctk.CTkFrame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=6)
        ctk.CTkLabel(left, text="People").pack(anchor="w", padx=8, pady=(8, 2))
        self.people_listbox = tk.Listbox(left, exportselection=False)
        self.people_listbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.people_listbox.bind("<<ListboxSelect>>", self.on_person_select)

        right = ctk.CTkFrame(body)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        ctk.CTkLabel(right, text="Unassigned Chromebooks (select multiple)").pack(anchor="w", padx=8, pady=(8, 2))
        self.asset_listbox = tk.Listbox(right, selectmode=tk.MULTIPLE, exportselection=False)
        self.asset_listbox.pack(fill="both", expand=True, padx=8, pady=8)

    def _build_timeline_tab(self) -> None:
        toolbar = ctk.CTkFrame(self.tab_timeline)
        toolbar.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(toolbar, text="Refresh for selected person", command=self.load_timeline).pack(side="left", padx=8, pady=8)

        self.timeline_box = ctk.CTkTextbox(self.tab_timeline)
        self.timeline_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_settings_tab(self) -> None:
        card = ctk.CTkFrame(self.tab_settings)
        card.pack(fill="x", padx=10, pady=10)

        self.api_base_var = tk.StringVar(value=self.config_data.get("api_base_url", "https://muskogeeps.incidentiq.com/api/v1.0"))
        self.site_id_var = tk.StringVar(value=self.config_data.get("site_id", "7ed482b1-0288-452c-b3dd-2bcefe2fcd17"))
        self.api_key_var = tk.StringVar(value="")

        ctk.CTkLabel(card, text="API Base URL").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ctk.CTkEntry(card, textvariable=self.api_base_var, width=700).grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(card, text="Site ID").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        ctk.CTkEntry(card, textvariable=self.site_id_var, width=700).grid(row=1, column=1, padx=8, pady=8)

        ctk.CTkLabel(card, text="API Key").grid(row=2, column=0, sticky="w", padx=8, pady=8)
        ctk.CTkEntry(card, textvariable=self.api_key_var, width=700, show="*").grid(row=2, column=1, padx=8, pady=8)

        ctk.CTkButton(card, text="Save Settings", command=self.save_settings).grid(row=3, column=1, sticky="e", padx=8, pady=12)

    def _hydrate_settings(self) -> None:
        masked_key = self.config_data.get("api_key_obfuscated")
        if masked_key:
            try:
                self.api_key_var.set(deobfuscate(masked_key))
            except Exception:
                self.api_key_var.set("")

    def _client(self) -> IncidentIQClient:
        key = self.api_key_var.get().strip()
        if not key:
            raise ValueError("API key is missing. Add it in Settings.")
        return IncidentIQClient(base_url=self.api_base_var.get().strip(), api_key=key)

    def set_status(self, text: str, good: bool = True) -> None:
        self.status_label.configure(text=text, text_color="lightgreen" if good else "orange")

    def save_settings(self) -> None:
        data = {
            "api_base_url": self.api_base_var.get().strip(),
            "site_id": self.site_id_var.get().strip(),
            "api_key_obfuscated": obfuscate(self.api_key_var.get().strip()),
        }
        save_config(data)
        self.config_data = data
        self.set_status("Settings saved")
        messagebox.showinfo("Saved", "Settings saved. API key is obfuscated locally.")

    def _run_async(self, action, done):
        def worker():
            try:
                result = action()
                self.after(0, lambda: done(result, None))
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: done(None, exc))

        threading.Thread(target=worker, daemon=True).start()

    def search_people(self) -> None:
        term = self.person_search.get().strip()
        if not term:
            return
        self.set_status("Searching people...")

        def action():
            return self._client().search_people(term)

        def done(result, error):
            if error:
                self.set_status(f"Search failed: {error}", good=False)
                return
            self.people_results = result or []
            self.people_listbox.delete(0, tk.END)
            for person in self.people_results:
                self.people_listbox.insert(tk.END, person.get("fullName", "Unknown"))
            self.set_status(f"Loaded {len(self.people_results)} people")

        self._run_async(action, done)

    def on_person_select(self, _event=None) -> None:
        selected_idx = self.people_listbox.curselection()
        if not selected_idx:
            return
        self.selected_person = self.people_results[selected_idx[0]]
        self.set_status(f"Selected {self.selected_person.get('fullName', 'person')}")

    def load_unassigned(self) -> None:
        self.set_status("Loading unassigned Chromebooks...")

        def action():
            return self._client().get_unassigned_chromebooks()

        def done(result, error):
            if error:
                self.set_status(f"Load failed: {error}", good=False)
                return
            self.unassigned_assets = result or []
            self.asset_listbox.delete(0, tk.END)
            for asset in self.unassigned_assets:
                serial = asset.get("serialNumber", "(no serial)")
                model = asset.get("model", "Unknown model")
                self.asset_listbox.insert(tk.END, f"{serial} — {model}")
            self.set_status(f"Loaded {len(self.unassigned_assets)} Chromebooks")

        self._run_async(action, done)

    def mass_assign(self) -> None:
        if not self.selected_person:
            messagebox.showwarning("No Person", "Select a person first.")
            return

        idxs = self.asset_listbox.curselection()
        if not idxs:
            messagebox.showwarning("No Assets", "Select at least one Chromebook to assign.")
            return

        asset_ids = [self.unassigned_assets[i].get("id") for i in idxs if self.unassigned_assets[i].get("id")]
        person_name = self.selected_person.get("fullName", "Selected person")
        person_id = self.selected_person.get("id")

        if not person_id:
            messagebox.showerror("Missing ID", "Selected person is missing an ID from API response.")
            return

        self.set_status(f"Assigning {len(asset_ids)} Chromebook(s) to {person_name}...")

        def action():
            return self._client().mass_assign(person_id, asset_ids)

        def done(result, error):
            if error:
                self.set_status(f"Mass assign failed: {error}", good=False)
                if isinstance(error, requests.HTTPError) and error.response is not None:
                    messagebox.showerror("Mass Assign Failed", error.response.text)
                return
            self.set_status(f"Mass assign complete for {person_name}")
            self.dashboard_stats.insert(
                "end",
                f"\nAssigned {len(asset_ids)} Chromebook(s) to {person_name}. Response: {result}",
            )

        self._run_async(action, done)

    def load_timeline(self) -> None:
        if not self.selected_person:
            messagebox.showwarning("No Person", "Select a person in Mass Assign first.")
            return
        person = self.selected_person
        person_id = person.get("id")
        if not person_id:
            messagebox.showerror("Missing ID", "Selected person is missing an ID from API response.")
            return

        self.set_status("Loading timeline...")

        def action():
            return self._client().get_recent_timeline(person_id)

        def done(result, error):
            if error:
                self.set_status(f"Timeline failed: {error}", good=False)
                return
            self.timeline_box.delete("1.0", "end")
            self.timeline_box.insert("1.0", f"Timeline for {person.get('fullName', '')}\n\n")
            for item in result or []:
                created = item.get("createdOn", "")
                summary = item.get("description") or item.get("activityType") or "Activity"
                self.timeline_box.insert("end", f"{created} — {summary}\n")
            self.set_status(f"Loaded {len(result or [])} timeline item(s)")

        self._run_async(action, done)


def run() -> None:
    app = IncidentIQDesktop()
    app.mainloop()
