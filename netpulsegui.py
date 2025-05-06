import tkinter as tk
from tkinter import ttk, filedialog
import threading
import json
from netpulse import NetPulse
from netpulsetheme import apply_dark_theme

class NetPulseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NetPulse - Network Toolkit")
        self.root.geometry("640x400")
        self.netpulse = NetPulse()

        apply_dark_theme(self.root)

        self.command_var = tk.StringVar(value="Ping")
        self.param_var = tk.StringVar()

        self._build_ui()
        self.thread = None
        self.running = False

    def _build_ui(self):
        top_frame = tk.Frame(self.root, bg="#1e1e1e")
        top_frame.pack(pady=10)

        ttk.Label(top_frame, text="Comando:").grid(row=0, column=0, padx=5)
        self.command_menu = ttk.Combobox(top_frame, textvariable=self.command_var,
                                         values=["Ping", "Traceroute", "Nslookup", "Subnet Info", "Network Scan"],
                                         width=20)
        self.command_menu.grid(row=0, column=1)

        ttk.Label(top_frame, text="Parametro:").grid(row=0, column=2, padx=5)
        self.param_entry = ttk.Entry(top_frame, textvariable=self.param_var, width=30)
        self.param_entry.grid(row=0, column=3)

        button_frame = tk.Frame(self.root, bg="#1e1e1e")
        button_frame.pack()

        ttk.Button(button_frame, text="Esegui", command=self._start_command).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Interrompi", command=self._stop_command).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Esporta", command=self._export_output).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Pulisci", command=self._clear_output).grid(row=0, column=3, padx=5)

        self.output_text = tk.Text(self.root, height=15, wrap="word", bg="#1e1e1e", fg="#dcdcdc", insertbackground="white")
        self.output_text.pack(padx=10, pady=10, fill="both", expand=True)
        self.output_text.tag_config("success", foreground="#98c379")
        self.output_text.tag_config("error", foreground="#e06c75")

        self.status_label = tk.Label(self.root, text="Pronto.", anchor="w", bg="#1e1e1e", fg="#cccccc")
        self.status_label.pack(fill="x", padx=10, pady=(0,5))

        self.root.bind('<Return>', lambda event: self._start_command())

    def _start_command(self):
        if self.running:
            return
        self._clear_output()
        self.status_label.config(text="In esecuzione...")
        self.thread = threading.Thread(target=self._execute_command)
        self.thread.start()

    def _stop_command(self):
        self.running = False
        self.status_label.config(text="Esecuzione interrotta.")

    def _execute_command(self):
        self.running = True
        cmd = self.command_var.get().lower()
        param = self.param_var.get().strip()

        result = ""
        try:
            if cmd == "ping":
                ip = param.split()[0]
                result = json.dumps(self.netpulse.ping(ip), indent=2)
            elif cmd == "traceroute":
                result = json.dumps(self.netpulse.traceroute(param), indent=2)
            elif cmd == "nslookup":
                result = json.dumps(self.netpulse.nslookup(param), indent=2)
            elif cmd == "subnet info":
                ip, mask = param.split()
                result = json.dumps(self.netpulse.calc_subnet_info(f"{ip} {mask}"), indent=2)
            elif cmd == "network scan":
                result = json.dumps(self.netpulse.scan_network(param), indent=2)
            else:
                result = "Comando non riconosciuto."
        except Exception as e:
            result = f"Errore: {str(e)}"

        self.output_text.after(0, self._pretty_print_output, result)
        self.status_label.config(text="Comando completato.")
        self.running = False

    def _pretty_print_output(self, data):
        if self._is_json(data):
            self.output_text.insert("1.0", self._format_as_human_text(data), "success")
        else:
            self.output_text.insert("1.0", data, "error" if "Errore" in data else "success")

    def _is_json(self, string):
        try:
            json.loads(string)
            return True
        except:
            return False

    def _format_as_human_text(self, json_data: str) -> str:
        try:
            parsed = json.loads(json_data)
            lines = []

            mapping = {
                "ip_address": "IP Address",
                "subnet_mask": "Subnet Mask",
                "wildcard_mask": "Wildcard Mask",
                "cidr_notation": "CIDR Notation",
                "network_address": "Network Address",
                "broadcast_address": "Broadcast Address",
                "first_usable": "First Usable IP",
                "last_usable": "Last Usable IP",
                "usable_host_count": "Usable Hosts",
                "ip_class": "IP Class",
                "is_private": "Private Range"
            }

            for key, label in mapping.items():
                if key in parsed:
                    value = parsed[key]
                    if isinstance(value, bool):
                        value = "Yes" if value else "No"
                    lines.append(f"{label:<20}: {value}")
            return "\n".join(lines)
        except Exception:
            return json_data

    def _clear_output(self):
        self.output_text.delete("1.0", "end")

    def _export_output(self):
        content = self.output_text.get("1.0", "end").strip()
        if content:
            path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text Files", "*.txt")])
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)