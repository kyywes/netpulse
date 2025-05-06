import tkinter as tk
from netpulsegui import NetPulseGUI
import requests, os, sys, subprocess

def check_for_updates(current_version):
    print("Controllo aggiornamenti...")
    url = "https://raw.githubusercontent.com/kyywes/netpulse/main/release.json"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        release = r.json()
        if release["version"] > current_version:
            print(f"Aggiornamento disponibile: {release['version']} → {current_version}")
            for f in release["files"]:
                name, file_url = f["name"], f["url"]
                print(f"Aggiorno: {name}")
                content = requests.get(file_url).text
                with open(name, "w", encoding="utf-8") as out:
                    out.write(content)
            print("NetPulse aggiornato. Riavvio automatico...")
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit(0)
        else:
            print("NetPulse is up to date.")
    except Exception as e:
        print(f"Nessun aggiornamento disponibile: {e}")

if __name__ == "__main__":
    check_for_updates("1.2.0")
    root = tk.Tk()
    app = NetPulseGUI(root)
    root.mainloop()