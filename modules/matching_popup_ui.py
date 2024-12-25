import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk  # Import sv_ttk for theme
import os  # Import os to handle file paths
from modules.utils.logging_utils import log_message

class MatchingPopup:
    def __init__(self, confidence_level, confidence_data, parent, main_app):
        self.confidence_level = confidence_level  # This should be a list of paths only
        self.confidence_data = confidence_data  # Flag to check if extraction is canceled
        self.main_app = main_app  # Reference to the main application
        self.user_response = False
        self.skipped_list = []

        # Make Toplevel as popup
        self.popup = tk.Toplevel(parent)
        self.popup.title("Matching Output")
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
        
        # Set the main window to be inaccessible
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
        self.display_confidence_message(confidence_level)

        # Create a frame for the Treeview and scrollbar
        self.treeview_frame = ttk.Frame(self.container)
        self.treeview_frame.pack(padx=(16, 20), pady=(16, 16), fill='both', expand=True)

        # Create a Treeview to display successful extractions
        self.display_matching_results = ttk.Treeview(self.treeview_frame, columns=("No", "Source Folder", "Destination Folder", "Confidence", "Reason"), show='headings', height=10)
        self.display_matching_results.column("No", width=30, anchor=tk.W)  
        self.display_matching_results.column("Source Folder", width=300, anchor=tk.W, stretch=True)
        self.display_matching_results.column("Destination Folder", width=180, anchor=tk.W)
        self.display_matching_results.column("Confidence", width=80, anchor=tk.W)
        self.display_matching_results.column("Reason", width=180, anchor=tk.W)

        self.display_matching_results.heading("No", text="No")
        self.display_matching_results.heading("Source Folder", text="Source Folder")
        self.display_matching_results.heading("Destination Folder", text="Destination Folder")
        self.display_matching_results.heading("Confidence", text="Confidence")
        self.display_matching_results.heading("Reason", text="Reason")
        self.display_matching_results.pack(side=tk.LEFT, fill='both', expand=True)

        # Create right-click menu
        self.right_click_menu = tk.Menu(self.popup, tearoff=0)
        self.right_click_menu.add_command(label="Skip this file", command=self.skip_selected_item)

        # Bind right-click event
        self.display_matching_results.bind("<Button-3>", self.show_right_click_menu)

        # Create a scrollbar for the Treeview
        self.scrollbar = ttk.Scrollbar(self.treeview_frame, orient="vertical", command=self.display_matching_results.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill='y')

        self.cancel_button = ttk.Button(self.container, text="Skip", command=self.skip_action)
        self.cancel_button.pack(padx=(10, 20), pady=(5, 10), fill='x', expand=False)

        self.confirm_button = ttk.Button(self.container, text="Confirm", command=self.confirm_action, style="Accent.TButton")
        self.confirm_button.forget()

        # Pack the Confirm button only if the confidence level is not low
        if confidence_level != "low_confidence":
            self.confirm_button.pack(padx=(10, 20), pady=(5, 10), fill='x', expand=False)

        self.add_data_to_table(self.confidence_data)  # Start the extraction process

    def display_confidence_message(self, confidence_level):
        confidence_titles = {
            "high_confidence": "High Confidence Result",
            "medium_confidence": "Medium Confidence Result",
            "low_confidence": "Low Confidence Result"
        }

        confidence_messages = {
            "high_confidence": (
                "Everything looks good click 'Confirm' to process the folders.\n"
                "Otherwise, If you see discrepancies in Step 2, feel free to skip."
            ),
            "medium_confidence": (
                "There are some uncertainties. Click 'Confirm' to continue processing.\n"
                "You can skip if you find dont match folder and try again in Step 2."
            ),
            "low_confidence": (
                "Caution!: Confidence is low. You can only skip this action.\n"
                "Please rename any folders that don't match."
            )
        }

        # Set the title and message based on the confidence level
        title = confidence_titles.get(confidence_level, "Unknown Confidence Level")
        self.label = ttk.Label(self.container, text=title, font=("Arial", 12, "bold"))
        self.label.pack(padx=(10, 20), pady=(5, 10), fill='x', anchor='w')

        # Get the appropriate message for the confidence level
        message = confidence_messages.get(confidence_level, "No message available.")
        self.status_message = ttk.Label(
            self.container,
            text=message,
            anchor='w'
        )
        self.status_message.pack(padx=(10, 20), pady=(5, 10), fill='x', anchor='w')

    def add_data_to_table(self,matching_results):
        # Menambahkan data ke tabel
        for index, result in enumerate(matching_results, start=1):
            source_folder_name = os.path.basename(result.source_path)
            # Menambahkan nilai ke tabel
            self.display_matching_results.insert("", "end", values=(index, source_folder_name, result.destination_name, f"{float(result.confidence):.2f}%", result.reason))
        self.display_matching_results.pack(padx=(10, 20), pady=(5, 10), fill='both', expand=True)
    
    def show_right_click_menu(self, event):
        """Show the right-click menu at cursor position"""
        try:
            selected_item = self.display_matching_results.identify_row(event.y)
            if selected_item:
                self.display_matching_results.selection_set(selected_item)
                self.right_click_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.right_click_menu.grab_release()

    def skip_selected_item(self):
        """Remove selected item from list after confirmation"""
        selected_item = self.display_matching_results.selection()
        if selected_item:
            item_values = self.display_matching_results.item(selected_item)['values']
            source_folder_name = item_values[1]  # Get just the source folder name
            
            confirmation = messagebox.askyesno(
                "Confirm Skip",
                f"Are you sure you want to skip '{source_folder_name}'?"
            )
            
            if confirmation:
                # Remove from treeview
                self.display_matching_results.delete(selected_item)
                
                # Add source folder name to skipped list
                self.skipped_list.append(source_folder_name)
                log_message(f"Skipped file from matching list: {source_folder_name}")


    def confirm_action(self):
        """Handle the confirm action."""
        self.user_response = True  # Set response to True when confirmed
        self.popup.destroy()  # Close the popup

    def skip_action(self):
        """Cancel the extraction process."""
        self.user_response = False  # Set response to False when canceled
        self.label.config(text="Cancelling...")
        self.status_message.config(text="Status: Cancelling...")
        self.popup.destroy()  # Close the popup
