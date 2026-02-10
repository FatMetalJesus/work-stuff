from __future__ import annotations

import os
import queue
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .case_manager import CaseManager
from .dependency_manager import DependencyManager
from .models import CaseRecord, Mode, RecoveryJob
from .recovery_engine import RECOVERY_PROFILES, RecoveryEngine


class OmniRecoverStudioApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Omni Recover Studio")
        self.root.geometry("1400x900")

        self.workspace = Path.home() / "OmniRecoverCases"
        self.case_manager = CaseManager(self.workspace)
        self.dependency_manager = DependencyManager()
        self.recovery_engine = RecoveryEngine()

        self.mode: Mode = "Beginner"
        self.current_case: CaseRecord | None = None
        self.jobs: dict[str, RecoveryJob] = {}
        self.log_queue: queue.Queue[str] = queue.Queue()

        self._build_layout()
        self._refresh_case_list()
        self._poll_log_queue()

    def _build_layout(self) -> None:
        topbar = ttk.Frame(self.root, padding=8)
        topbar.pack(fill="x")

        ttk.Label(topbar, text="Workspace:").pack(side="left")
        self.workspace_var = tk.StringVar(value=str(self.workspace))
        ttk.Entry(topbar, textvariable=self.workspace_var, width=60).pack(side="left", padx=6)
        ttk.Button(topbar, text="Browse", command=self._pick_workspace).pack(side="left")

        self.mode_var = tk.StringVar(value=self.mode)
        ttk.Label(topbar, text="Mode:").pack(side="left", padx=(16, 4))
        ttk.Combobox(topbar, textvariable=self.mode_var, values=["Beginner", "Expert"], width=12, state="readonly").pack(side="left")
        ttk.Button(topbar, text="Apply", command=self._apply_mode).pack(side="left", padx=4)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True)

        self.case_tab = ttk.Frame(self.tabs)
        self.recover_tab = ttk.Frame(self.tabs)
        self.deps_tab = ttk.Frame(self.tabs)
        self.live_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.case_tab, text="Cases")
        self.tabs.add(self.recover_tab, text="Recovery")
        self.tabs.add(self.deps_tab, text="Dependency Center")
        self.tabs.add(self.live_tab, text="Live Case View")

        self._build_case_tab()
        self._build_recover_tab()
        self._build_dep_tab()
        self._build_live_tab()

    def _build_case_tab(self) -> None:
        wrapper = ttk.Frame(self.case_tab, padding=10)
        wrapper.pack(fill="both", expand=True)

        left = ttk.Frame(wrapper)
        left.pack(side="left", fill="y")
        right = ttk.Frame(wrapper)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        ttk.Label(left, text="Cases").pack(anchor="w")
        self.case_list = tk.Listbox(left, width=40, height=28)
        self.case_list.pack(fill="y", pady=(4, 8))
        self.case_list.bind("<<ListboxSelect>>", lambda _e: self._select_case_from_list())

        create_row = ttk.Frame(left)
        create_row.pack(fill="x", pady=2)
        self.case_name_var = tk.StringVar()
        ttk.Entry(create_row, textvariable=self.case_name_var).pack(side="left", fill="x", expand=True)
        ttk.Button(create_row, text="Create", command=self._create_case).pack(side="left", padx=4)

        action_row = ttk.Frame(left)
        action_row.pack(fill="x", pady=2)
        ttk.Button(action_row, text="Import .zip", command=self._import_case).pack(side="left")
        ttk.Button(action_row, text="Export .zip", command=self._export_case).pack(side="left", padx=4)

        ttk.Label(right, text="Case Overview").pack(anchor="w")
        self.case_info = tk.Text(right, height=20, wrap="word")
        self.case_info.pack(fill="x", pady=(4, 10))

        ttk.Label(right, text="Job Log").pack(anchor="w")
        self.log_box = tk.Text(right, height=15, wrap="word")
        self.log_box.pack(fill="both", expand=True)

    def _build_recover_tab(self) -> None:
        wrapper = ttk.Frame(self.recover_tab, padding=10)
        wrapper.pack(fill="both", expand=True)

        form = ttk.LabelFrame(wrapper, text="Recovery Job Builder", padding=8)
        form.pack(fill="x")

        self.source_var = tk.StringVar()
        self.profile_var = tk.StringVar(value="Quick Recover")
        self.read_only_var = tk.BooleanVar(value=True)

        ttk.Label(form, text="Source Device/Image:").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.source_var, width=90).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(form, text="Browse", command=self._pick_source).grid(row=0, column=2)

        ttk.Label(form, text="Recovery Profile:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.profile_combo = ttk.Combobox(form, textvariable=self.profile_var, values=list(RECOVERY_PROFILES.keys()), state="readonly")
        self.profile_combo.grid(row=1, column=1, sticky="w", pady=(8, 0))

        ttk.Checkbutton(form, text="Read-only workflow", variable=self.read_only_var).grid(row=1, column=2, sticky="w", padx=4, pady=(8, 0))
        ttk.Button(form, text="Queue Job", command=self._queue_job).grid(row=2, column=1, sticky="w", pady=(8, 0))

        form.columnconfigure(1, weight=1)

        expert = ttk.LabelFrame(wrapper, text="Expert Command Preview", padding=8)
        expert.pack(fill="x", pady=(10, 0))
        self.command_preview = tk.Text(expert, height=6, wrap="word")
        self.command_preview.pack(fill="x")
        ttk.Button(expert, text="Generate Preview", command=self._preview_command).pack(anchor="w", pady=(6, 0))

        jobs_frame = ttk.LabelFrame(wrapper, text="Job Queue", padding=8)
        jobs_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.jobs_tree = ttk.Treeview(jobs_frame, columns=("id", "profile", "status", "progress"), show="headings")
        for col in ("id", "profile", "status", "progress"):
            self.jobs_tree.heading(col, text=col.upper())
        self.jobs_tree.pack(fill="both", expand=True)

    def _build_dep_tab(self) -> None:
        wrapper = ttk.Frame(self.deps_tab, padding=10)
        wrapper.pack(fill="both", expand=True)

        self.dep_guidance = tk.StringVar(value=self.dependency_manager.platform_guidance())
        ttk.Label(wrapper, textvariable=self.dep_guidance, wraplength=900).pack(anchor="w", pady=(0, 8))

        self.dep_tree = ttk.Treeview(wrapper, columns=("tool", "status", "hint"), show="headings")
        self.dep_tree.heading("tool", text="Tool")
        self.dep_tree.heading("status", text="Found")
        self.dep_tree.heading("hint", text="Install Guidance")
        self.dep_tree.pack(fill="both", expand=True)

        actions = ttk.Frame(wrapper)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Scan Dependencies", command=self._refresh_dependencies).pack(side="left")
        ttk.Button(actions, text="Install Missing Python Packages", command=self._install_python_bundle).pack(side="left", padx=6)

        self.dep_output = tk.Text(wrapper, height=14)
        self.dep_output.pack(fill="both", expand=True, pady=(8, 0))

        self._refresh_dependencies()

    def _build_live_tab(self) -> None:
        wrapper = ttk.Frame(self.live_tab, padding=10)
        wrapper.pack(fill="both", expand=True)

        ttk.Label(wrapper, text="Live evidence view auto-refreshes every 3 seconds.").pack(anchor="w")
        self.live_tree = ttk.Treeview(wrapper, columns=("path", "size"), show="headings")
        self.live_tree.heading("path", text="Relative Path")
        self.live_tree.heading("size", text="Bytes")
        self.live_tree.pack(fill="both", expand=True, pady=(6, 0))

        ttk.Button(wrapper, text="Refresh Now", command=self._refresh_live_view).pack(anchor="w", pady=(6, 0))
        self._schedule_live_refresh()

    def _pick_workspace(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.workspace)
        if not selected:
            return
        self.workspace = Path(selected)
        self.workspace_var.set(str(self.workspace))
        self.case_manager = CaseManager(self.workspace)
        self._refresh_case_list()

    def _apply_mode(self) -> None:
        self.mode = self.mode_var.get()  # type: ignore[assignment]
        if self.mode == "Beginner":
            self.command_preview.configure(state="disabled")
        else:
            self.command_preview.configure(state="normal")
        self._log(f"Mode changed to {self.mode}")

    def _create_case(self) -> None:
        name = self.case_name_var.get().strip()
        if not name:
            return
        try:
            record = self.case_manager.create_case(name)
        except Exception as exc:
            messagebox.showerror("Could not create case", str(exc))
            return
        self.current_case = record
        self.case_name_var.set("")
        self._refresh_case_list()
        self._render_case_info(record)

    def _select_case_from_list(self) -> None:
        idx = self.case_list.curselection()
        if not idx:
            return
        name = self.case_list.get(idx[0])
        self.current_case = self.case_manager.open_case(name)
        self._render_case_info(self.current_case)
        self._refresh_live_view()

    def _refresh_case_list(self) -> None:
        self.case_list.delete(0, tk.END)
        for record in self.case_manager.list_cases():
            self.case_list.insert(tk.END, record.name)

    def _render_case_info(self, record: CaseRecord) -> None:
        self.case_info.delete("1.0", tk.END)
        self.case_info.insert(
            tk.END,
            (
                f"Case: {record.name}\n"
                f"Path: {record.base_path}\n"
                f"Created: {record.created_at.isoformat()}\n"
                f"Updated: {record.updated_at.isoformat()}\n\n"
                "Folders:\n"
                f"- evidence: {record.base_path / 'evidence'}\n"
                f"- output: {record.base_path / 'output'}\n"
                f"- reports: {record.base_path / 'reports'}\n"
                f"- logs: {record.base_path / 'logs'}\n"
                f"- imports: {record.base_path / 'imports'}\n"
            ),
        )

    def _import_case(self) -> None:
        archive = filedialog.askopenfilename(filetypes=[("Zip archive", "*.zip")])
        if not archive:
            return
        try:
            record = self.case_manager.import_case_archive(Path(archive))
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))
            return
        self.current_case = record
        self._refresh_case_list()
        self._render_case_info(record)
        self._log(f"Imported case archive {archive}")

    def _export_case(self) -> None:
        if not self.current_case:
            messagebox.showwarning("No case", "Select a case first")
            return
        target = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Zip archive", "*.zip")])
        if not target:
            return
        out = self.case_manager.export_case_archive(self.current_case, Path(target))
        self._log(f"Exported case to {out}")

    def _pick_source(self) -> None:
        source = filedialog.askopenfilename()
        if source:
            self.source_var.set(source)

    def _preview_command(self) -> None:
        if not self.current_case:
            messagebox.showwarning("No case", "Open or create a case first")
            return
        source = self.source_var.get().strip()
        if not source:
            messagebox.showwarning("Missing source", "Choose a source device or image")
            return
        output_dir = self.current_case.base_path / "output" / "preview"
        job = self.recovery_engine.build_job(self.current_case.name, source, self.profile_var.get(), output_dir)
        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert(tk.END, job.command)

    def _queue_job(self) -> None:
        if not self.current_case:
            messagebox.showwarning("No case", "Open or create a case first")
            return
        source = self.source_var.get().strip()
        if not source:
            messagebox.showwarning("Missing source", "Choose a source device or image")
            return
        profile = self.profile_var.get()
        output_dir = self.current_case.base_path / "output" / f"job_{int(time.time())}"
        job = self.recovery_engine.build_job(self.current_case.name, source, profile, output_dir)
        self.jobs[job.job_id] = job
        self.jobs_tree.insert("", tk.END, iid=job.job_id, values=(job.job_id, profile, job.status, f"{job.progress}%"))

        runner = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        runner.start()

    def _run_job(self, job: RecoveryJob) -> None:
        job.status = "Running"
        self._update_job_row(job)
        self._log(f"[{job.job_id}] Running: {job.command}")

        if os.name == "nt":
            cmd = ["cmd", "/c", job.command]
        else:
            cmd = ["bash", "-lc", job.command]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        if proc.stdout is not None:
            for line in proc.stdout:
                self._log(f"[{job.job_id}] {line.strip()}")

        code = proc.wait()
        job.progress = 100
        if code == 0:
            job.status = "Completed"
        else:
            job.status = "Failed"
        self._update_job_row(job)
        self._log(f"[{job.job_id}] finished with status={job.status}")

    def _update_job_row(self, job: RecoveryJob) -> None:
        self.root.after(
            0,
            lambda: self.jobs_tree.item(
                job.job_id,
                values=(job.job_id, job.profile, job.status, f"{job.progress}%"),
            ),
        )

    def _refresh_dependencies(self) -> None:
        for child in self.dep_tree.get_children():
            self.dep_tree.delete(child)
        for dep, found in self.dependency_manager.detect():
            self.dep_tree.insert("", tk.END, values=(dep.name, "Yes" if found else "No", dep.install_hint))

    def _install_python_bundle(self) -> None:
        self.dep_output.delete("1.0", tk.END)
        self.dep_output.insert(tk.END, "Installing optional Python packages...\n")

        def _worker() -> None:
            result = self.dependency_manager.install_python_bundle()
            self.log_queue.put("[deps] pip install finished")
            self.root.after(0, lambda: self.dep_output.insert(tk.END, result.stdout + "\n" + result.stderr))
            self.root.after(0, self._refresh_dependencies)

        threading.Thread(target=_worker, daemon=True).start()

    def _refresh_live_view(self) -> None:
        for child in self.live_tree.get_children():
            self.live_tree.delete(child)
        if not self.current_case:
            return

        base = self.current_case.base_path
        for file_path in base.rglob("*"):
            if file_path.is_file():
                rel = file_path.relative_to(base)
                size = file_path.stat().st_size
                self.live_tree.insert("", tk.END, values=(str(rel), size))

    def _schedule_live_refresh(self) -> None:
        self._refresh_live_view()
        self.root.after(3000, self._schedule_live_refresh)

    def _log(self, message: str) -> None:
        self.log_queue.put(message)

    def _poll_log_queue(self) -> None:
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_box.insert(tk.END, msg + "\n")
                self.log_box.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self._poll_log_queue)
