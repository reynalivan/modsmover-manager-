import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk  # Import sv_ttk for theme


class LoadingDialog:
    def __init__(self, parent):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Processing")
        sv_ttk.set_theme("dark")  # Set the theme using sv_ttk

        # Center the popup on the screen
        self.popup.update_idletasks()
        width = 300
        height = 120
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.popup.geometry(f"{width}x{height}+{x}+{y}")

        # Set agar main window tidak dapat diakses
        self.popup.transient(parent)
        self.popup.grab_set()

        # Create a container frame for the UI elements
        self.container = ttk.Frame(self.popup)
        self.container.pack(padx=16, pady=16, fill='both', expand=True)
        
        # Add progress bar and label
        self.progress_label = ttk.Label(self.container, text="Processing folder matches...")
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.container, mode='indeterminate')
        self.progress_bar.pack(pady=10, padx=20, fill='x')
        self.progress_bar.start()

                
    def close_popup(self):
        """Close the popup window."""
        self.popup.destroy()
