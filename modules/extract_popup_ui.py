import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk  # Import sv_ttk for theme
import modules.utils.archive_utils as archive_utils
import threading
import os  # Import os to handle file paths

class ArchiveExtractorPopup:
    def __init__(self, archives, parent, main_app):
        self.archives = archives  # This should be a list of paths only
        self.is_canceled = False  # Flag to check if extraction is canceled
        self.user_closed = False
        self.main_app = main_app  # Reference to the main application

        # Create a new window for extraction
        self.popup = tk.Toplevel(parent)
        self.popup.title("Matching Folder")
        sv_ttk.set_theme("dark")  # Set the theme using sv_ttk
        
        # Center the popup on the screen
        self.popup.geometry("800x600+{}+{}".format(
            parent.winfo_rootx() + parent.winfo_width() // 2 - 200,
            parent.winfo_rooty() + parent.winfo_height() // 2 - 150
        ))
        
        # Set agar main window tidak dapat diakses
        self.popup.transient(parent)
        self.popup.grab_set()

        # Set minimum size for the popup
        self.popup.minsize(400, 300)

        # Create a container frame for the UI elements
        self.container = ttk.Frame(self.popup)
        self.container.pack(padx=16, pady=16, fill='both', expand=True)

        # Create a custom style for the Progressbar
        style = ttk.Style()
        style.configure("TProgressbar", thickness=30, orient='horizontal') 

        # Create UI elements
        self.label = ttk.Label(self.container, text="Extracting archives...", font=("Arial", 12, "bold"))
        self.label.pack(padx=(10, 20), pady=(5, 10), fill='x', anchor='w')

        # Create a progress bar that fills the width of the container
        self.progress = ttk.Progressbar(self.container, orient="horizontal", mode="determinate", maximum=len(self.archives), style="TProgressbar")
        self.progress.pack(padx=(10, 20), pady=(5, 10), fill='x', expand=False)

        self.status_message = ttk.Label(self.container, text="Waiting for extraction...", wraplength=300, anchor='w')
        self.status_message.pack(padx=(10, 20), pady=(5, 10), fill='x', anchor='w')
        
        self.info_message = ttk.Label(self.container, text="Note: Success extraction archives moved to /.extracted folder.", wraplength=300, anchor='w')
        self.info_message.forget()

        # Create a Treeview to display successful extractions
        self.successful_extractions = ttk.Treeview(self.container, columns=("Status", "Archive Name"), show='headings', height=10)
        self.successful_extractions.column("Status", width=100, anchor=tk.W)  
        self.successful_extractions.heading("Status", text="Status")
        self.successful_extractions.column("Archive Name", width=500, anchor=tk.W) 
        self.successful_extractions.heading("Archive Name", text="Archive Name")
        self.successful_extractions.pack(padx=(10, 20), pady=(5, 10), fill='both', expand=True)

        self.cancel_button = ttk.Button(self.container, text="Cancel", command=self.cancel_extraction)
        self.cancel_button.pack(padx=(10, 20), pady=(5, 10), fill='x', expand=False)

        self.confirm_button = ttk.Button(self.container, text="Confirm", command=self.close_popup)
        self.confirm_button.pack(padx=(10, 20), pady=(5, 10), fill='x', expand=False)
        self.confirm_button.pack_forget()  # Hide the confirm button initially

        self.start_extraction()  # Start the extraction process

    def start_extraction(self):
        """Start the extraction process in a separate thread."""
        self.is_canceled = False
        self.progress["value"] = 0

        # Start the extraction in a new thread
        threading.Thread(target=self.extract_archives, daemon=True).start()

    def extract_archives(self):
        """Extract all archives and update the progress bar."""
        total_success = 0
        total_already = 0
        total_failed = 0

        for index, path in enumerate(self.archives, start=1):
            if self.is_canceled:
                messagebox.showinfo("Cancelled", "Extraction has been cancelled.")
                self.close_popup()  # Close the popup if canceled
                return

            # Extract the archive name from the path
            archive_name = os.path.basename(path)  # Get the file name from the path

            self.label.config(text=f"Extracting... ({index}/{len(self.archives)})")
            self.progress["value"] = index
            self.status_message.config(text=f"Status: Extracting '{archive_name}'...")
            self.popup.update_idletasks()  # Update the UI

            try:
                extract_process = archive_utils.extract_archive(path)
                if extract_process == "FAILED":
                    self.status_message.config(text=f"Failed to extract '{archive_name}'.")
                    self.successful_extractions.insert("", tk.END, values=("Failed", archive_name))
                    total_failed += 1
                    self.popup.update_idletasks()  # Update the UI
                    self.main_app.refresh_available_archives()
                    self.main_app.refresh_available_source_folders()
                    continue
                if extract_process == "ALREADY":
                    self.status_message.config(text=f"SKIPPED: Already extracted '{archive_name}'.")
                    self.successful_extractions.insert("", tk.END, values=("Skipped", archive_name))
                    total_already += 1
                    self.popup.update_idletasks()  # Update the UI
                    self.main_app.refresh_available_archives()
                    self.main_app.refresh_available_source_folders()
                    continue
                elif extract_process == "SUCCESS":
                    self.status_message.config(text=f"Successfully extracted '{archive_name}'.")
                    self.successful_extractions.insert("", tk.END, values=("Success", archive_name))
                    total_success += 1
                    self.popup.update_idletasks()  # Update the UI
                    self.main_app.refresh_available_archives()
                    self.main_app.refresh_available_source_folders()
                else:
                    self.status_message.config(text=f"Failed to extract '{archive_name}'.")
                    self.successful_extractions.insert("", tk.END, values=("Failed", archive_name))
                    total_failed += 1
                    self.popup.update_idletasks()  # Update the UI
                    self.main_app.refresh_available_archives()
                    self.main_app.refresh_available_source_folders()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract '{archive_name}': {e}")

        if not self.is_canceled:
            # Update label to show completion message
            self.label.config(text="Completed Extraction", foreground="light green")
            self.status_message.config(text=f"Total Success: {total_success}, Already Extracted: {total_already}, Failed: {total_failed}.")
            self.info_message.pack(padx=(10, 20), pady=(5, 10), fill='x', anchor='w')
            self.cancel_button.pack_forget()  # Hide the cancel button
            self.confirm_button.pack(pady=(10, 5))  # Show the confirm button
            self.popup.update_idletasks()  # Update the UI

    def cancel_extraction(self):
        """Cancel the extraction process."""
        self.is_canceled = True
        self.label.config(text="Cancelling...")
        self.status_message.config(text="Status: Cancelling...")

    def close_popup(self):
        """Close the popup window."""
        self.main_app.refresh_available_archives()
        self.main_app.refresh_available_source_folders()
        self.user_closed = True
        self.popup.destroy()

