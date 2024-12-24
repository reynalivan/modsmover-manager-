import tkinter as tk
from tkinter import ttk
import sv_ttk  # Import sv_ttk for theme

class MatchingResultPopup:
    def __init__(self, total_summary, parent):
        self.total_summary = total_summary
        self.popup = tk.Toplevel(parent)
        self.popup.title("Processing Results")
        sv_ttk.set_theme("dark")  # Set the theme using sv_ttk

        # Center the popup on the screen
        self.popup.update_idletasks()
        width = 960
        height = 600
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.popup.geometry(f"{width}x{height}+{x}+{y}")

        # Set agar main window tidak dapat diakses
        self.popup.transient(parent)
        self.popup.grab_set()

        # Set minimum size for the popup
        self.popup.minsize(400, 300)

        # Create a container frame for the UI elements
        self.container = ttk.Frame(self.popup)
        self.container.pack(padx=16, pady=16, fill='both', expand=True)

        # Display a summary of the results
        self.display_summary()

        # Create a frame for the Treeview and scrollbar
        self.treeview_frame = ttk.Frame(self.container)
        self.treeview_frame.pack(padx=(16, 20), pady=(16, 16), fill='both', expand=True)

        # Create a Treeview to display processing results
        self.display_results = ttk.Treeview(self.treeview_frame, columns=("Status", "Folders"), show='headings', height=10)
        self.display_results.column("Status", width=20, anchor=tk.W)
        self.display_results.column("Folders", width=300, anchor=tk.W, stretch=True)

        self.display_results.heading("Status", text="Status")
        self.display_results.heading("Folders", text="Folders")
        self.display_results.pack(side=tk.LEFT, fill='both', expand=True)

        # Create a scrollbar for the Treeview
        self.scrollbar = ttk.Scrollbar(self.treeview_frame, orient="vertical", command=self.display_results.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill='y')
        self.display_results.configure(yscrollcommand=self.scrollbar.set)

        # Add data to the table
        self.add_data_to_table()

        # Add Confirm button
        self.confirm_button = ttk.Button(self.container, text="Confirm", style="Accent.TButton", command=self.close_popup)
        self.confirm_button.pack(padx=(10, 20), pady=(5, 10), fill='x', expand=False)

    def add_data_to_table(self):
        # Add data to the table
        for folder in self.total_summary.get('moved', []):
            self.display_results.insert("", "end", values=("Moved", folder))
        for folder in self.total_summary.get('failed', []):
            self.display_results.insert("", "end", values=("Failed", folder))
        for folder in self.total_summary.get('duplicates', []):
            self.display_results.insert("", "end", values=( "Duplicate", folder))

    def display_summary(self):
        # Display a summary of the results
        count = len(self.total_summary.get('moved', [])) + len(self.total_summary.get('failed', [])) + len(self.total_summary.get('duplicates', []))
        summary_message = (
            f"Successfully moved: {len(self.total_summary.get('moved', []))}\n"
            f"Failed to move: {len(self.total_summary.get('failed', []))}\n"
            f"Duplicates skipped: {len(self.total_summary.get('duplicates', []))}"
        )
        title_label = ttk.Label(self.container, text=f"Total {count} folders have been processed.", font=("Segoe UI", 12, "bold"))
        title_label.pack(padx=(10, 10), pady=(5, 10), anchor='w')

        self.summary_label = ttk.Label(self.container, text=summary_message, anchor='w')
        self.summary_label.pack(padx=(10, 20), pady=(5, 10), fill='x', anchor='w')

    def close_popup(self):
        """Close the popup window."""
        self.popup.destroy()
