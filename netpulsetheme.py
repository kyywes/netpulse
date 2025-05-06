from tkinter import ttk

def apply_dark_theme(root):
    style = ttk.Style()
    style.theme_use('clam')

    bg = "#1e1e1e"
    fg = "#ffffff"
    accent = "#3c3f41"

    style.configure(".", background=bg, foreground=fg, fieldbackground=accent)
    style.configure("TEntry", fieldbackground=accent)
    style.configure("TCombobox", fieldbackground=accent, foreground=fg)
    style.configure("TButton", padding=5)
    style.configure("TLabel", padding=5)
    style.configure("TFrame", background=bg)
    style.configure("Horizontal.TProgressbar", background="#4CAF50")

    root.configure(bg=bg)