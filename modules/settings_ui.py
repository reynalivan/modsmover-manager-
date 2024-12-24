import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sv_ttk 
import os
import re
from modules.utils.logging_utils import log_message

class SettingsUI:
    def __init__(self, parent, main_app, config_utils, BASE_DIR, CONFIG_PATH, DICTIONARY_PATH, READYTOMOVES_DIR, firstinitial=False):
        self.base_dir = BASE_DIR
        self.config_path = CONFIG_PATH
        self.dictionary_path = DICTIONARY_PATH
        self.readytomoves_dir = READYTOMOVES_DIR
        self.user_saved = False
        self.main_app = main_app
        
        # Make Toplevel as popup
        self.popup = tk.Toplevel(parent)
        self.popup.title("Settings")
        sv_ttk.set_theme("dark")

        # Center the popup on the screen
        self.popup.update_idletasks()
        width = 960
        height = 800
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.popup.geometry(f"{width}x{height}+{x}+{y}")

        # Set the main window to be inaccessible
        self.popup.transient(parent)
        self.popup.grab_set()

        # Initialize configuration utilities
        self.config_utils = config_utils
        self.config = self.config_utils.load_config()
        self.dictionary_data = self.config_utils.load_dictionary()

        # Create a frame for the header
        header_frame = ttk.Frame(self.popup)
        header_frame.pack(padx=10, pady=10, fill='x')

        # Title label
        title_label = ttk.Label(header_frame, text="Settings", font=("Segoe UI", 16, "bold"))
        title_label.pack(side=tk.LEFT)

        # Create a notebook for tabs
        self.notebook = ttk.Notebook(self.popup)
        self.notebook.pack(padx=10, pady=10, fill='both', expand=True)

        # Create tabs
        self.create_destinations_tab()
        self.create_matching_config_tab()
        self.create_dictionary_config_tab()

        # Save button at the bottom
        save_button = ttk.Button(self.popup, text="Save Settings", command=self.save_all, style="Accent.TButton")
        save_button.pack(padx=10, pady=10, fill='x')

        if firstinitial:
            XXMI_confirm = messagebox.askyesno("First Time Setup", "Do you use to have XXMI Launcher?", parent=self.popup)
            if XXMI_confirm:
                self.auto_detect_game_folders()
            else:
                messagebox.showinfo("First Time Setup", "You can add the game manually by clicking 'Add Manual' button. Then, you can save the settings by clicking 'Save Settings' button.", parent=self.popup)

    def create_destinations_tab(self):
        """Create UI for managing game destinations."""
        frame = ttk.Frame(self.notebook)
        frame.pack(fill='x', padx=(10, 10), pady=(10, 10))

        self.notebook.add(frame, text="Destinations")

        # Auto Detect Section
        auto_detect_frame = ttk.Frame(frame)
        auto_detect_frame.pack(padx=10, pady=(12, 5), fill='x', anchor='w')

        ttk.Label(auto_detect_frame, text="XXMI Location (Auto Detect):").pack(side=tk.LEFT, padx=(5, 5))
        self.auto_detect_path_label = ttk.Label(auto_detect_frame, text="Not set", relief="solid", width=30)
        self.auto_detect_path_label.pack(side=tk.LEFT, padx=(5, 5), fill='x', expand=True)
        auto_detect_button = ttk.Button(auto_detect_frame, text="Browse", command=self.auto_detect_game_folders)
        auto_detect_button.pack(side=tk.LEFT, padx=(5, 0))

        # Treeview for destinations
        self.destination_list = ttk.Treeview(frame, columns=("Mods Name", "Destination Path"), show='headings')
        self.destination_list.heading("Mods Name", text="Mods Game Name")
        self.destination_list.heading("Destination Path", text="Destination Path")
        self.destination_list.pack(fill='both', expand=True, anchor='w', padx=10, pady=(12, 5))

        # Populate treeview with existing data
        # Set to track game names that have been added from self.config
        added_games_lowercase = set()

        # Check if self.config exists
        if self.config:
            # Check if DESTINATION_PATH exists and is a dictionary
            destination_path = self.config.get("DESTINATION_PATH", {})
            if isinstance(destination_path, dict):
                for game, path in destination_path.items():
                    # Add to treeview and set
                    self.destination_list.insert("", "end", values=(game, path))
                    log_message(f"Added folder {game} to destination list from config.")
                    added_games_lowercase.add(game.lower())  # Add game to the set
            else:
                log_message("DESTINATION_PATH is not a valid dictionary.")
        else:
            log_message("Configuration is not loaded or is empty.")


        # Check self.readytomoves_dir for folder subfolder list
        if os.path.exists(self.readytomoves_dir):
            for folder in os.listdir(self.readytomoves_dir):
                if os.path.isdir(os.path.join(self.readytomoves_dir, folder)):
                    # Only add if the folder is not already in the set
                    if folder.lower() not in added_games_lowercase:
                        self.destination_list.insert("", "end", values=(folder, "Not Set"))
                        log_message(f"Added folder {folder} to destination list from new found folder on reaytomoves.")


        self.destination_list.bind("<Double-1>", self.on_game_double_click)
        self.destination_list.bind("<Button-3>", self.show_destination_context_menu)

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=(10, 10), pady=(5, 10))
        ttk.Label(frame, text="Add Manual:").pack(anchor='w', padx=10, pady=(12, 5))

        # Footer for creating new destination
        add_frame = ttk.Frame(frame)
        add_frame.pack(pady=10, padx=10, fill='x', anchor='w')

        # Game Name Entry
        ttk.Label(add_frame, text="Game Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_game_name_entry = ttk.Entry(add_frame, width=15)
        self.new_game_name_entry.pack(side=tk.LEFT, padx=(5, 10), fill='x', expand=True)

        # Destination Path Entry
        ttk.Label(add_frame, text="Destination Path:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_destination_path_entry = ttk.Entry(add_frame, width=30)
        self.new_destination_path_entry.pack(side=tk.LEFT, padx=(5, 0), fill='x', expand=True)
        self.new_destination_path_entry.bind("<Button-1>", self.browse_destination_path)

        add_new_button = ttk.Button(add_frame, text="Add New", command=self.add_new_destination)
        add_new_button.pack(side=tk.LEFT, padx=(5, 10))

    def browse_destination_path(self, event):
        """Open a file dialog to select a destination path."""
        folder_path = filedialog.askdirectory(title="Select Destination Folder")
        if folder_path:
        # Replace forward slashes with backslashes
            folder_path = folder_path.replace('/', '\\')
            self.new_destination_path_entry.delete(0, tk.END)
            self.new_destination_path_entry.insert(0, folder_path)


    def auto_detect_game_folders(self):
        """Auto-detect game folders from XXMI Launcher location."""
        if not hasattr(self, 'launcher_path') or not self.selected_launcher_path:
            self.selected_launcher_path = filedialog.askdirectory(title="Select XXMI Launcher Location")
        if not self.selected_launcher_path:
            return
        
        predetect_folders_list = ["WWMI", "ZZMI", "GIMI", "SRMI"]
        found_folders = []

        for predetect_folder in predetect_folders_list:
            predetect_folder_path = os.path.join(self.selected_launcher_path, predetect_folder)
            if os.path.isdir(predetect_folder_path):
                # Check if items are already on destination_list and replace with new path
                for item in self.destination_list.get_children():
                    if self.destination_list.item(item, "values")[0].lower() == predetect_folder.lower():
                        # Delete duplicate item
                        self.destination_list.delete(item)
                # Detect if found folder_path + /mods/SkinSelectImpact exists
                mods_path = os.path.join(predetect_folder_path, "mods")
                # Detect if found folder_path + /mods
                skinselectimpact_path = os.path.join(mods_path, "SkinSelectImpact")
                if os.path.isdir(skinselectimpact_path):
                    found_folders.append(predetect_folder)
                    log_message(f"Found SkinSelectImpact Folder: {predetect_folder} - {skinselectimpact_path}")
                    self.destination_list.insert("", "end", values=(predetect_folder, skinselectimpact_path.replace('\\', '/')))
                elif os.path.isdir(mods_path):
                    found_folders.append(predetect_folder)
                    log_message(f"Found Mods Folder: {predetect_folder} - {mods_path}")
                    self.destination_list.insert("", "end", values=(predetect_folder, mods_path.replace('\\', '/')))
                else:
                    log_message(f"Found Folder: {predetect_folder} but does not contain mods folder, Skipped.")
            else:
                log_message(f"Folder not found: {predetect_folder}")

        if not found_folders:
            self.auto_detect_path_label.config(text="Not set")
            messagebox.showinfo("Not Found", "No game folders found. You can add them manually.", parent=self.popup) 
        else:
            self.auto_detect_path_label.config(text=self.selected_launcher_path)
            messagebox.showinfo("Found Folders", f"Found: {', '.join(found_folders)}", parent=self.popup)


    def on_game_double_click(self, event):
        """Handle double-click on treeview to edit game settings."""
        selected_item = self.destination_list.focus()
        if not selected_item:
            return

        values = self.destination_list.item(selected_item, "values")
        self.edit_game_entry(values[0], values[1], selected_item)
    
    def show_destination_context_menu(self, event):
        """Show context menu for destination treeview."""
        context_menu = tk.Menu(self.popup, tearoff=0)
        context_menu.add_command(label="Edit", command=lambda: self.on_game_double_click(event))
        context_menu.add_command(label="Delete", command=lambda: self.delete_destination(event))
        context_menu.post(event.x_root, event.y_root)

    def delete_destination(self, event):
        """Delete selected destination."""
        selected_item = self.destination_list.focus()
        if selected_item:
            # delete folder in self.readytomoves_dir / selected_item items [0] value
            folder_path = self.readytomoves_dir + "\\" + self.destination_list.item(selected_item, "values")[0]
            log_message(f"Deleting folder: {folder_path}")
            if os.path.isdir(folder_path):
                os.rmdir(folder_path)
            self.destination_list.delete(selected_item)
            

    def edit_game_entry(self, game_name, destination_path, item_id):
        """Open a dialog to edit game entry."""
        edit_window = tk.Toplevel(self.popup)
        edit_window.title("Edit Game Entry")

        # Make the window topmost
        edit_window.attributes('-topmost', True)

        # Disable the main window
        edit_window.transient(self.popup)
        edit_window.grab_set()
        
        # Center the dialog
        edit_window.geometry("360x200+{}+{}".format(
            self.popup.winfo_rootx() + self.popup.winfo_width() // 2 - 200,
            self.popup.winfo_rooty() + self.popup.winfo_height() // 2 - 150
        ))

        # Create and pack the labels and entries
        ttk.Label(edit_window, text="Mods Game Name:").pack(padx=10, pady=5, anchor='w')
        game_name_entry = ttk.Entry(edit_window)
        game_name_entry.insert(0, game_name)
        game_name_entry.pack(padx=10, pady=5, fill='x')

        ttk.Label(edit_window, text="Destination Path:").pack(padx=10, pady=5, anchor='w')
        destination_path_entry = ttk.Entry(edit_window)
        destination_path_entry.bind("<Button-1>", lambda event:browse_destination_path_edit())
        destination_path_entry.insert(0, destination_path)
        destination_path_entry.pack(padx=10, pady=5, fill='x')

        def update_entry():
            new_game_name = game_name_entry.get()
            # validation destination_path_entry is path or not
            if not os.path.isdir(destination_path_entry.get()):
                messagebox.showwarning("Input Error", "Destination Path must be a valid path.", parent=edit_window)
                return
            new_destination_path = destination_path_entry.get()
            self.destination_list.item(item_id, values=(new_game_name, new_destination_path))
            edit_window.destroy()
        
        def browse_destination_path_edit():
            """Open a file dialog to select a destination path."""
            folder_path = filedialog.askdirectory(parent=edit_window, title="Select Destination Folder")
            if folder_path:
            # Replace forward slashes with backslashes
                destination_path_entry.delete(0, tk.END)
                destination_path_entry.insert(0, folder_path)

        ttk.Button(edit_window, text="Update", command=update_entry, style="Accent.TButton").pack(pady=10, padx=5, fill='x')


    def add_new_destination(self):
        """Add a new destination to the treeview."""
        game_name = self.new_game_name_entry.get().strip()
        destination_path = self.new_destination_path_entry.get().strip()

        if not game_name or not destination_path:
            messagebox.showwarning("Input Error", "Both fields must be filled.")
            return

        existing_games = {self.destination_list.item(item, "values")[0] for item in self.destination_list.get_children()}
        if game_name in existing_games:
            messagebox.showwarning("Duplicate Entry", f"{game_name} already exists in the list.")
            return

        self.destination_list.insert("", "end", values=(game_name, destination_path))
        self.new_game_name_entry.delete(0, tk.END)
        self.new_destination_path_entry.delete(0, tk.END)

    def create_matching_config_tab(self):
        """Create UI for managing ignore numbers, skipwords, and aliases."""
        frame = ttk.Frame(self.notebook)
        frame.pack(fill='x', padx=(10, 10), pady=(10, 10))
        
        self.notebook.add(frame, text="Matching Config")

        # Matching Threshold
        ttk.Label(frame, text="Matching Threshold:").pack(anchor='w', padx=10, pady=(12, 5))

        # high confidence number config
        high_confidence_frame = ttk.Frame(frame)
        high_confidence_frame.pack(padx=10, pady=(5, 5), fill='x', anchor='w')

        ttk.Label(high_confidence_frame, text="High Confidence Number:").pack(side=tk.LEFT, padx=(5, 5))
        self.high_confidence_entry = ttk.Entry(high_confidence_frame, width=5)
        self.high_confidence_entry.pack(side=tk.LEFT, padx=(5, 10), fill='x', expand=True)
    
        # get high confidence 
        # Check if self.config exists
        if self.config:
            # Check if SIMILARITY_THRESHOLD exists and is a dictionary
            similarity_threshold = self.config.get("SIMILARITY_THRESHOLD", {})
            if isinstance(similarity_threshold, dict):
                high_confidence_value = similarity_threshold.get('HIGH_CONFIDENCE', '70')  # Default value if not found
                self.high_confidence_entry.insert(0, high_confidence_value)
            else:
                self.high_confidence_entry.insert(0, '70')  # Default value if SIMILARITY_THRESHOLD is not a valid dictionary
        else:
            self.high_confidence_entry.insert(0, '70')  # Default value if config is not loaded or is empty

        # medium confidence number config
        medium_confidence_frame = ttk.Frame(frame)
        medium_confidence_frame.pack(padx=10, pady=(5, 5), fill='x', anchor='w')

        ttk.Label(medium_confidence_frame, text="Medium Confidence Number:").pack(side=tk.LEFT, padx=(5, 5))
        self.medium_confidence_entry = ttk.Entry(medium_confidence_frame, width=5)
        self.medium_confidence_entry.pack(side=tk.LEFT, padx=(5, 10), fill='x', expand=True)
        
        # get medium confidence
        # Check if self.config exists
        if self.config:
            # Check if SIMILARITY_THRESHOLD exists and is a dictionary
            similarity_threshold = self.config.get("SIMILARITY_THRESHOLD", {})
            if isinstance(similarity_threshold, dict):
                medium_confidence_value = similarity_threshold.get('MEDIUM_CONFIDENCE', '40')  # Default value if not found
                self.medium_confidence_entry.insert(0, medium_confidence_value)
            else:
                self.medium_confidence_entry.insert(0, '40')  # Default value if SIMILARITY_THRESHOLD is not a valid dictionary
        else:
            self.medium_confidence_entry.insert(0, '40')  # Default value if config is not loaded or is empty

 
        # Extension Check
        ttk.Label(frame, text="Extension Check:").pack(anchor='w', padx=10, pady=(12, 5))
        self.extension_entry = ttk.Entry(frame)
        self.extension_entry.pack(fill='x', padx=10, pady=5)
        ttk.Label(frame, text="The following extension will be checked in matching criteria, separate with commas.", font=("Segoe UI", 8 )).pack(anchor='w', padx=10, pady=(0, 5)) 
        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=(10, 10), pady=(5, 10))
        
        # Check if self.config exists
        if self.config:
            # Check if EXTENSIONS_CHECK exists and is a list
            extensions_check = self.config.get('EXTENSIONS_CHECK', {}).get('extensions', '')
            # Ensure EXTENSIONS_CHECK is a list and not empty
            if isinstance(extensions_check, list) and extensions_check:
                extensions_value = ', '.join(extensions_check)  # Join the list into a string
            else:
                extensions_value = '.ini, .dds, .buf, .ib'  # Default value if EXTENSIONS_CHECK is not a valid list or is empty
        else:
            extensions_value = '.ini, .dds, .buf, .ib'  # Default value if config is not loaded or is empty

        # Insert the extensions value into the entry
        self.extension_entry.insert(0, extensions_value)

    def create_dictionary_config_tab(self):
        """Create UI for managing ignore numbers, skipwords, and aliases."""
        frame = ttk.Frame(self.notebook)
        frame.pack(fill='x', padx=(10, 10), pady=(10, 10))
        
        self.notebook.add(frame, text="Dictionary")

        # Skipwords
        ttk.Label(frame, text="Skipwords:").pack(anchor='w', padx=10, pady=(12, 5))
        self.skipword_entry = ttk.Entry(frame)
        self.skipword_entry.pack(fill='x', padx=10, pady=5)
        ttk.Label(frame, text="The following text will be ignored in matching criteria, separate with commas.", font=("Segoe UI", 8 )).pack(anchor='w', padx=10, pady=(0, 5)) #light text

        if self.dictionary_data:
            skipword = self.dictionary_data.get('SETTINGS', {}).get('skipword', '')
            if isinstance(skipword, str):
                self.skipword_entry.insert(0, skipword)
            else:
                self.skipword_entry.insert(0, 'DISABLED, download') # Default value if skipword is not a valid string
        else:
            self.skipword_entry.insert(0, 'DISABLED, download') # Default value if dictionary
            
        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=(10, 10), pady=(5, 10))

        # Ignore Numbers
        if self.dictionary_data:
            ignore_numbers = self.dictionary_data.get('SETTINGS', {}).get('ignore_numbers', '')
            if isinstance(ignore_numbers, str):
                self.ignore_numbers_var = tk.BooleanVar(value=(ignore_numbers.lower() == 'true'))
            else:
                self.ignore_numbers_var = tk.BooleanVar(value=True)
        else:
            self.ignore_numbers_var = tk.BooleanVar(value=True)
        ignore_numbers_checkbutton = ttk.Checkbutton(frame, text="Ignore Numbers", variable=self.ignore_numbers_var)
        ignore_numbers_checkbutton.pack(anchor='w', padx=10, pady=5)

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=(10, 10), pady=(5, 10))

        # Aliases
        ttk.Label(frame, text="Aliases:").pack(anchor='w', padx=10, pady=5)
        self.alias_treeview = ttk.Treeview(frame, columns=("Alias", "Target"), show='headings')
        self.alias_treeview.heading("Alias", text="Alias")
        self.alias_treeview.heading("Target", text="Target")
        self.alias_treeview.pack(fill='both', expand=True, padx=10, pady=5)

        # Populate treeview with existing aliases
        if self.dictionary_data:
            aliases = self.dictionary_data.get('ALIAS', {})
            if isinstance(aliases, dict):
                for alias, target in aliases.items():
                    self.alias_treeview.insert("", "end", values=(alias, target))
            else:
                self.alias_treeview.insert("", "end", values=(aliases, ''))
                print("ALIAS is not a valid dictionary.")
        else:
            self.alias_treeview.insert("", "end", values=('', ''))
            print("No dictionary data found or it is not valid.")

        self.alias_treeview.bind("<Double-1>", self.on_alias_double_click)
        self.alias_treeview.bind("<Button-3>", self.show_alias_context_menu)

        ttk.Label(frame, text="Create New Alias:").pack(anchor='w', padx=10, pady=5)
        
        # Footer for creating new alias
        footer_frame = ttk.Frame(frame)
        footer_frame.pack(pady=10, padx=10, fill='x', anchor='w')

        ttk.Label(footer_frame, text="Alias:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_alias_entry = ttk.Entry(footer_frame, width=30)
        self.new_alias_entry.pack(side=tk.LEFT, padx=(5, 10), fill='x', expand=True)

        ttk.Label(footer_frame, text="Target:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_target_entry = ttk.Entry(footer_frame, width=30)
        self.new_target_entry.pack(side=tk.LEFT, padx=(5, 10),  fill='x', expand=True)

        add_new_alias_button = ttk.Button(footer_frame, text="Add New", command=self.add_new_alias)
        add_new_alias_button.pack(side=tk.LEFT, padx=(5, 5))

   
    def on_alias_double_click(self, event):
        """Handle double-click on treeview to edit alias."""
        selected_item = self.alias_treeview.focus()
        if not selected_item:
            return

        alias, target = self.alias_treeview.item(selected_item, "values")
        self.edit_alias(alias, target, selected_item)

    def edit_alias(self, alias, target, item_id):
        """Open a dialog to edit alias."""
        edit_window = tk.Toplevel(self.popup)
        edit_window.title("Edit Alias")

        # Make the window topmost
        edit_window.attributes('-topmost', True)

        # Disable the main window
        edit_window.transient(self.popup)
        edit_window.grab_set()

        # Center the dialog
        edit_window.geometry("360x200+{}+{}".format(
            self.popup.winfo_rootx() + self.popup.winfo_width() // 2 - 180,
            self.popup.winfo_rooty() + self.popup.winfo_height() // 2 - 75
        ))

        # Create and pack the labels and entries
        ttk.Label(edit_window, text="Alias:").pack(padx=10, pady=5, anchor='w')
        alias_entry = ttk.Entry(edit_window)
        alias_entry.insert(0, alias)
        alias_entry.pack(padx=10, pady=5, fill='x')

        ttk.Label(edit_window, text="Target:").pack(padx=10, pady=5, anchor='w')
        target_entry = ttk.Entry(edit_window)
        target_entry.insert(0, target)
        target_entry.pack(padx=10, pady=5, fill='x')

        def update_entry():
            new_alias = alias_entry.get()
            new_target = target_entry.get()
            self.alias_treeview.item(item_id, values=(new_alias, new_target))
            edit_window.destroy()

        ttk.Button(edit_window, text="Update", command=update_entry, style="Accent.TButton").pack(pady=10, padx=5, fill='x')

        # Ensure the dialog is closed properly
        edit_window.protocol("WM_DELETE_WINDOW", lambda: (edit_window.destroy(), self.popup.deiconify()))

    def show_alias_context_menu(self, event):
        """Show context menu for alias treeview."""
        context_menu = tk.Menu(self.popup, tearoff=0)
        context_menu.add_command(label="Edit", command=lambda: self.on_alias_double_click(event))
        context_menu.add_command(label="Delete", command=lambda: self.delete_alias(event))
        context_menu.post(event.x_root, event.y_root)

    def delete_alias(self, event):
        """Delete selected alias."""
        selected_item = self.alias_treeview.focus()
        if selected_item:
            self.alias_treeview.delete(selected_item)
  
    def add_new_alias(self):
        """Add a new alias to the treeview."""
        alias = self.new_alias_entry.get().strip()
        target = self.new_target_entry.get().strip()

        if not alias or not target:
            messagebox.showwarning("Input Error", "Both fields must be filled.")
            return

        existing_aliases = {self.alias_treeview.item(item, "values")[0] for item in self.alias_treeview.get_children()}
        if alias in existing_aliases:
            messagebox.showwarning("Duplicate Entry", f"{alias} already exists in the list.")
            return

        self.alias_treeview.insert("", "end", values=(alias, target))
        self.new_alias_entry.delete(0, tk.END)
        self.new_target_entry.delete(0, tk.END)


    def save_combined_settings(self, parent):
        """Save combined settings to dictionary with validation."""

        # Config settings
        # ==============================

        # Save destination config
        xxmi_path = self.auto_detect_path_label.cget("text")
        if xxmi_path == "Not set" or xxmi_path is None:
            xxmi_path = ""
        elif not os.path.isdir(xxmi_path):
            messagebox.showerror("Error", "DESTINATION_CONFIG must be a valid path. Please correct it.")
            return False

        # Save destination path config
        destination_paths = {}
        for item in self.destination_list.get_children():
            name = self.destination_list.item(item, "values")[0]
            path = self.destination_list.item(item, "values")[1]
            if not os.path.isdir(path) and path != "Not Set":
                messagebox.showerror("Error", f"DESTINATION_PATH for {name} on {path} must be a valid path. Please correct it.")
                return False
            destination_paths[name] = path

        # Save similarity threshold
        try:
            high_confidence = int(self.high_confidence_entry.get())
            medium_confidence = int(self.medium_confidence_entry.get())

            if not (1 <= high_confidence <= 100):
                messagebox.showerror("Error", "HIGH_CONFIDENCE must be a number between 1 and 100.")
                return False

            if not (1 <= medium_confidence <= 100):
                messagebox.showerror("Error", "MEDIUM_CONFIDENCE must be a number between 1 and 100.")
                return False

            if high_confidence <= medium_confidence:
                messagebox.showerror("Error", "HIGH_CONFIDENCE must be greater than MEDIUM_CONFIDENCE.")
                return False

            high_confidence_str = str(high_confidence)
            medium_confidence_str = str(medium_confidence)

        except ValueError:
            messagebox.showerror("Error", "HIGH_CONFIDENCE and MEDIUM_CONFIDENCE must be valid numbers.")
            return False

        # Save extension check
        extensions = self.extension_entry.get().strip()
        is_valid_extensions, extensions_error = self.validate_extensions(extensions)
        if not is_valid_extensions:
            messagebox.showerror("Invalid Extensions", extensions_error)
            return False

        # Dictionary settings
        # ==============================

        # Save skipword
        skipwords = self.skipword_entry.get()

        # Save ignore numbers setting
        ignore_numbers = self.ignore_numbers_var.get()
        if ignore_numbers not in [True, False]:
            messagebox.showerror("Error", "IGNORE_NUMBERS must be either True or False.")
            return False

        ignore_numbers_str = str(ignore_numbers).lower()

        # Save aliases
        aliases = {self.alias_treeview.item(item, "values")[0]: self.alias_treeview.item(item, "values")[1] for item in self.alias_treeview.get_children()}
        # Filter aliases to be case-insensitive and unique
        unique_aliases = {}
        for alias, target in aliases.items():
            unique_aliases[alias.lower()] = target

        # Prepare config data
        config_data = {
            'DESTINATION_CONFIG': {
                'XXMI_path': xxmi_path,
            },
            'DESTINATION_PATH': destination_paths,
            'SIMILARITY_THRESHOLD': {
                'HIGH_CONFIDENCE': high_confidence_str,
                'MEDIUM_CONFIDENCE': medium_confidence_str,
            },
            'EXTENSIONS_CHECK': {
                'extensions': extensions,
            }
        }

        # Prepare dictionary data
        dictionary_data = {
            'ALIAS': unique_aliases,
            'SETTINGS': {
                'skipword': skipwords,
                'ignore_numbers': ignore_numbers_str,
            }
        }

        # Create folder on readytomoves_dir based on destination path name
        for game_name, path in destination_paths.items():
            folder_path = os.path.join(self.readytomoves_dir, game_name)
            os.makedirs(folder_path, exist_ok=True)

        log_message(
            f"\n\n"
            f"==============================\n"
            f"Saving settings\n"
            f"Config Data: \n{config_data} \n"
            f"Dictionary Data: \n {dictionary_data} \n"
            f"==============================\n"
            f"\n\n"
        )

        # Save the updated dictionary using ConfigUtils
        dictionary_save_success = self.config_utils.save_dictionary(dictionary_data)

        # Save the updated config using ConfigUtils
        config_save_success = self.config_utils.save_config(config_data)

        # Check if both saves were successful
        if dictionary_save_success and config_save_success:
            # Call the reload method on the main app
            parent.reload_settings()  # Assuming self.master is the App instance
            return True
        else:
            messagebox.showerror("Save Failed", "Failed to save settings. Please try again.")
            return False
    

    def save_all(self):
        """Save all settings."""
        save_status = self.save_combined_settings(self.main_app)
        if save_status is True:
            self.user_saved = True
            self.popup.destroy()
        else:
            self.user_saved = False

    def validate_extensions(self, extensions):
        """Validate extensions."""
        if not extensions:
            return False, "Extensions Check cannot be empty."

        # Split the extensions by comma and strip whitespace
        ext_list = [ext.strip() for ext in extensions.split(',') if ext.strip()]

        if not ext_list:
            return False, "Extensions Check must contain at least one valid extension."

        # Validate each extension
        for ext in ext_list:
            if not re.match(r'^\.[a-zA-Z0-9]+$', ext):
                return False, f"Invalid extension: '{ext}'. Extensions must start with a dot and contain alphanumeric characters."

        return True, ""

# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    settings_ui = SettingsUI(root)
    root.mainloop()
