import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from netpulse import NetPulse
from netpulsetheme import apply_dark_theme

class NetPulseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NetPulse - Network Toolkit")
        self.root.geometry("800x500")
        apply_dark_theme(self.root)

        self.netpulse = NetPulse()
        self.command_var = tk.StringVar()
        self.param_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Pronto.")

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root)
        frame.pack(pady=10)

        ttk.Label(frame, text="Comando:").grid(row=0, column=0, padx=5)
        self.command_box = ttk.Combobox(frame, textvariable=self.command_var, width=20)
        self.command_box['values'] = ["Ping", "Traceroute", "Nslookup", "Subnet Info", "Network Scan"]
        self.command_box.current(0)
        self.command_box.grid(row=0, column=1)

        ttk.Label(frame, text="Parametro:").grid(row=0, column=2, padx=5)
        self.param_entry = ttk.Entry(frame, textvariable=self.param_var, width=40)
        self.param_entry.grid(row=0, column=3)
        self.param_entry.bind("<Return>", lambda e: self._start_command())

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=5)

        ttk.Button(button_frame, text="Esegui", command=self._start_command).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Interrompi", command=self._clear_output).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Esporta", command=self._export_output).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Pulisci", command=self._clear_output).pack(side="left", padx=5)

        self.output_text = tk.Text(self.root, wrap="word", bg="#2d2d2d", fg="#dcdcdc", insertbackground="white",
                                   font=("Consolas", 10))
        self.output_text.pack(expand=True, fill="both", padx=10, pady=5)

        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")

    def _start_command(self):
        threading.Thread(target=self._execute_command, daemon=True).start()

    def _execute_command(self):
        cmd = self.command_var.get().lower()
        param = self.param_var.get().strip()
        self._clear_output()
        self.status_var.set("In esecuzione...")

        try:
            if cmd == "ping":
                result = self.netpulse.ping(param)
            elif cmd == "traceroute":
                result = self.netpulse.traceroute(param)
            elif cmd == "nslookup":
                result = self.netpulse.nslookup(param)
            elif cmd == "subnet info":
                ip, mask = param.split()
                result = self.netpulse.calc_subnet_info(ip, mask)
            elif cmd == "network scan":
                result = {"hosts": self.netpulse.scan_network(param)}
            else:
                result = {"error": "Comando non valido"}

            output = self.netpulse.format_output(result)
            self.output_text.insert("1.0", output)
            self.status_var.set("Comando completato.")
        except Exception as e:
            self.output_text.insert("1.0", f"Errore: {str(e)}")
            self.status_var.set("Errore durante l'esecuzione.")

    def _clear_output(self):
        self.output_text.delete("1.0", tk.END)

    def _export_output(self):
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("Esporta", "Nessun contenuto da esportare.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.status_var.set(f"Output esportato in: {path}")