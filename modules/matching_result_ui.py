import tkinter as tk
from tkinter import ttk, messagebox
from modules.utils.folder_utils import move_folder
import sv_ttk  # Import sv_ttk for theme
import os

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
        self.display_results = ttk.Treeview(self.treeview_frame, columns=("Status", "From", "To"), show='headings', height=10)
        self.display_results.column("Status", width=20, anchor=tk.W)
        self.display_results.column("From", width=300, anchor=tk.W, stretch=True)
        self.display_results.column("To", width=300, anchor=tk.W, stretch=True)

        self.display_results.heading("Status", text="Status")
        self.display_results.heading("From", text="From")
        self.display_results.heading("To", text="To")
        self.display_results.pack(side=tk.LEFT, fill='both', expand=True)

        # Bind right click event to treeview
        self.display_results.bind("<Button-3>", self.show_context_menu)
        
        # Create context menu
        self.context_menu = tk.Menu(self.popup, tearoff=0)
        self.context_menu.add_command(label="Open Destination", command=self.open_destination)
        self.context_menu.add_command(label="Revert Folder", command=self.revert_folder)

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
        # Add data to the table with 3 columns
        for source, dest in self.total_summary.get('moved', []):
            self.display_results.insert("", "end", values=("Moved", source, dest))
        
        for source, dest in self.total_summary.get('failed', []):
            self.display_results.insert("", "end", values=("Failed", source, dest))
        
        for source, dest in self.total_summary.get('duplicates', []):
            self.display_results.insert("", "end", values=("Duplicate", source, dest))

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

    def show_context_menu(self, event):
        """Show context menu on right click"""
        # Get item under cursor
        item = self.display_results.identify_row(event.y)
        if item:
            # Get status value from the selected item
            status = self.display_results.item(item)['values'][0]
            if status == "Moved":
                # Select the item and show menu only for "Moved" status
                self.display_results.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)


    def open_destination(self):
        """Open destination folder of selected item"""
        selected = self.display_results.selection()
        if selected:
            item = selected[0]
            dest_path = self.display_results.item(item)['values'][2]  # Get 'To' column value
            if os.path.exists(dest_path):
                os.startfile(dest_path)
            else:
                messagebox.showerror("Error", "Destination folder not found")

    def revert_folder(self):
        """Move folder back to original location"""
        selected = self.display_results.selection()
        if selected:
            item = selected[0]
            values = self.display_results.item(item)['values']
            source_path = values[1]  # 'From' column
            dest_path = values[2]    # 'To' column
            
            if os.path.exists(dest_path):
                if move_folder(dest_path, source_path):
                    # Update status in treeview
                    self.display_results.set(item, "Status", "Reverted")
                    messagebox.showinfo("Success", "Folder reverted successfully")
                else:
                    messagebox.showerror("Error", "Failed to revert folder")
            else:
                messagebox.showerror("Error", "Source folder not found")
                
    def close_popup(self):
        """Close the popup window."""
        self.popup.destroy()
