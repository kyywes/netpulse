import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from netpulse import NetPulse
from netpulsetheme import apply_dark_theme

class NetPulseGUI:
    def __init__(self, root):
        self.root = root
        self.core = NetPulse()
        self.ping_process = None
        apply_dark_theme(self.root)
        self._build_interface()

    def _build_interface(self):
        self.command_var = tk.StringVar()
        self.param_var = tk.StringVar()
        self.status_var = tk.StringVar()

        ttk.Label(self.root, text="NetPulse - Network Toolkit", font=("Segoe UI", 14, "bold")).pack(pady=8)

        cmd_frame = ttk.Frame(self.root)
        cmd_frame.pack(pady=5)

        ttk.Label(cmd_frame, text="Comando:").pack(side="left", padx=5)
        self.command_box = ttk.Combobox(cmd_frame, textvariable=self.command_var, width=20)
        self.command_box['values'] = ["Ping", "Traceroute", "NSLookup", "Subnet Info", "Scan Network"]
        self.command_box.current(0)
        self.command_box.pack(side="left")

        ttk.Label(cmd_frame, text="Parametro:").pack(side="left", padx=5)
        self.param_entry = ttk.Entry(cmd_frame, textvariable=self.param_var, width=40)
        self.param_entry.pack(side="left", padx=5)
        self.param_entry.bind("<Return>", lambda e: self._start_execution())

        act_frame = ttk.Frame(self.root)
        act_frame.pack(pady=5)

        ttk.Button(act_frame, text="Esegui", command=self._start_execution).pack(side="left", padx=5)
        ttk.Button(act_frame, text="Interrompi", command=self._stop_ping).pack(side="left", padx=5)
        ttk.Button(act_frame, text="Esporta", command=self._export_output).pack(side="left", padx=5)
        ttk.Button(act_frame, text="Pulisci", command=self._clear_output).pack(side="left", padx=5)

        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

        self.output_text = tk.Text(self.root, wrap="word", height=20, bg="#2d2d2d",
                                   fg="#dcdcdc", insertbackground="white",
                                   font=("Consolas", 10), relief="flat")
        self.output_text.tag_config("success", foreground="#4CAF50")
        self.output_text.tag_config("error", foreground="#FF5252")
        self.output_text.tag_config("info", foreground="#9E9E9E")
        self.output_text.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(fill="x", side="bottom")
        self.status_var.set("Pronto.")

    def _start_execution(self):
        threading.Thread(target=self._execute_command, daemon=True).start()

    def _execute_command(self):
        cmd = self.command_var.get()
        arg = self.param_var.get().strip()
        self._clear_output()
        self._set_status(f"{cmd} in esecuzione su {arg}...")
        self.progress.start()

        if not arg:
            messagebox.showerror("Errore", "Parametro mancante.")
            self._set_status("Errore.")
            self.progress.stop()
            return

        try:
            if cmd == "Ping":
                continuous = "-t" in arg
                host = arg.replace("-t", "").strip()
                self.ping_process = self.core.ping(host, continuous)
                if self.ping_process:
                    threading.Thread(target=self._read_ping_output, daemon=True).start()
            else:
                func = {
                    "Traceroute": self.core.traceroute,
                    "NSLookup": self.core.nslookup,
                    "Subnet Info": self.core.subnet_info,
                    "Scan Network": self.core.scan
                }.get(cmd)
                if func:
                    result = func(arg)
                    self.output_text.insert("1.0", result, "success")
                    self._set_status("Comando completato.")
        except Exception as e:
            self.output_text.insert("1.0", f"Errore: {e}", "error")
            self._set_status("Errore.")
        finally:
            self.progress.stop()

    def _read_ping_output(self):
        try:
            for line in self.ping_process.stdout:
                self.output_text.insert(tk.END, line, "info")
                self.output_text.see(tk.END)
        except Exception:
            pass

    def _stop_ping(self):
        if self.ping_process and self.ping_process.poll() is None:
            self.ping_process.terminate()
            self._set_status("Ping interrotto.")
        else:
            self._set_status("Nessun ping attivo.")

    def _clear_output(self):
        self.output_text.delete("1.0", tk.END)

    def _export_output(self):
        text = self.output_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Nessun contenuto", "Nessun output da esportare.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt")])
        if file:
            with open(file, "w") as f:
                f.write(text)
            self._set_status(f"Salvato in: {file}")

    def _set_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()