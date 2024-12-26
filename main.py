import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import sv_ttk 
import os
import sys

# Set environment variable for UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
from modules.ui_functions import *  # Import all functions from ui_functions.py
import modules.utils.archive_utils as archive_utils
import modules.utils.config_utils as ConfigUtils  # For reading configuration settings

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)  # Main.exe location
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Location of main.py when debugging

CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
DICTIONARY_PATH = os.path.join(BASE_DIR, 'dictionary.json')
READYTOMOVES_DIR = os.path.join(BASE_DIR, 'readytomoves')

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Mods Mover Manager")
        self.base_dir = BASE_DIR
        self.config_path = CONFIG_PATH
        self.dictionary_path = DICTIONARY_PATH
        self.readytomoves_dir = READYTOMOVES_DIR

        # Set the theme to dark
        sv_ttk.set_theme("dark")

        # Create header frame with game selection combobox
        self.header_frame = ttk.Frame(root)
        self.header_frame.pack(padx=(10, 10), pady=(5, 10), fill='x')

        # Add label to header frame 
        header_label = ttk.Label(self.header_frame, text="Folder:", font=("Segoe UI", 12, "bold"))
        header_label.pack(side=tk.LEFT, padx=(10, 10), pady=(0, 0))
        
        # Create combobox for available game folders
        self.available_game_folder_combobox = ttk.Combobox(self.header_frame, state='readonly')
        self.available_game_folder_combobox.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10), fill='x', expand=True)
        
        # Bind the selection event to update the content
        # self.available_game_folder_combobox bind comboselected update_content
        self.available_game_folder_combobox.bind("<<ComboboxSelected>>", lambda event: self.update_content())

        # Inside your App class, after creating the combobox
        settings_button = ttk.Button(self.header_frame, text="Settings", command=lambda: open_settings(self))
        settings_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))

        # Create container for main content
        self.container = ttk.Frame(root)
        self.container.pack(padx=(10, 10), pady=(0, 0), fill='both', expand=True)

        # Initialize ConfigUtils class
        self.config_utils = ConfigUtils.ConfigUtils(self.base_dir, self.config_path, self.dictionary_path)

        check_config = self.config_utils.check_config()
        if check_config is False:
            # change header_label with text "Waiting"
            header_label.config(text="Waiting to setup the settings")
            self.available_game_folder_combobox.pack_forget()
            settings_button.pack_forget()
            self.container.pack_forget()
            log_message("Config file not found. First Initialization.")
            messagebox.showinfo("Welcome!", "You need to set the settings first and click Save All.")
            settings_popup = SettingsUI(self.root, self, self.config_utils, self.base_dir, self.config_path, self.dictionary_path, self.readytomoves_dir, firstinitial=True)
            self.root.wait_window(settings_popup.popup)
            if settings_popup.user_saved == True:
                header_label.config(text="Folder:")
                self.available_game_folder_combobox.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10), fill='x', expand=True)
                settings_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.container.pack(padx=(10, 10), pady=(0, 0), fill='both', expand=True)
                self.reload_settings()
            else:
                messagebox.showerror("Canceled", "First Initialization, you need to set the settings first.")
                self.root.destroy()
            return
        else:
            # Load the configuration settings
            self.reload_settings()


    def reload_settings(self):
        """Reload the configuration and update the UI."""
        config = self.config_utils.load_config()
        dictionary_data = self.config_utils.load_dictionary()

        # Load configuration and dictionary values
        self.destination_path_list = config['DESTINATION_PATH']
        self.similarity_threshold = config['SIMILARITY_THRESHOLD']
        self.extensions_check = config['EXTENSIONS_CHECK']
        self.alias_data = dictionary_data['ALIAS']
        self.settings_data = dictionary_data['SETTINGS']

        # Log the settings data
        log_message(f"Settings Data: {self.settings_data}")

        # Convert and split settings
        self.ignore_numbers_status = self.settings_data.get('ignore_numbers', 'false').strip().lower() == 'true'
        self.skipworld_list = [item.strip() for item in self.settings_data.get('skipworld', '').split(',') if item.strip()]
        
        # Setup source folder
        self.source_folder_root = self.readytomoves_dir
        self.available_game_folders_list = folder_management.list_available_game_folders(self.source_folder_root)

        if self.available_game_folders_list is None:
            # Create game folders based on destination paths
            game_folders_to_create = list(self.destination_path_list.keys())
            
            # Create each game folder and update the list
            self.available_game_folders_list = []
            for game_name in game_folders_to_create:
                game_path = os.path.join(self.source_folder_root, game_name)
                folder_management.create_directory(game_path)
                self.available_game_folders_list.append(game_name)
        
        # Always add "Manual" option to the combobox
        self.available_game_folders_list.append("Manual")

        # Clear existing UI elements in the container
        for widget in self.container.winfo_children():
            widget.destroy()

        # Update the combobox with available game folders
        self.available_game_folder_combobox['values'] = self.available_game_folders_list
        self.available_game_folder_combobox.current(0)

        # Set selected game folder from combobox
        self.game_folder_selected = self.available_game_folder_combobox.get()

        # Refresh the UI content
        self.update_content()


    def update_content(self):
        """Update the content based on the selected folder."""
        # Clear the content frame
        for widget in self.container.winfo_children():
            widget.destroy()

        self.game_folder_selected = self.available_game_folder_combobox.get()
        self.source_folder_root = self.readytomoves_dir

        # Log the selected folder paths
        log_message(
            f"self.source_folder_root: {self.source_folder_root}  \n"
            f"self.game_folder_selected: {self.game_folder_selected}"
        )
    
        self.game_folder_selected_path = os.path.join(self.source_folder_root, self.game_folder_selected)
        log_message(f"selected_game_folder_path: {self.game_folder_selected_path}")
     
        if self.game_folder_selected == "Manual":
            # Frame for Source Folder Selection (only in Manual mode)
            self.create_manual_source_folder_selection()
        else:
            # Label for Path Location in other folders
            self.create_path_location_display()

        # Separator
        ttk.Separator(self.container, orient='horizontal').pack(fill='x', padx=(10, 10), pady=(10, 10))

        # Step 1 - Extract Available Archive
        self.create_extract_archive_section()

        # Step 2 - Review Your Source Folder
        self.create_source_folder_review_section()

        # Step 3 - Confirm if You're Ready to Move
        self.create_destination_folder_confirmation()

    def create_manual_source_folder_selection(self):
        """Create UI elements for manual source folder selection."""
        source_folder_frame = ttk.Frame(self.container)
        source_folder_frame.pack(padx=(10, 10), fill='x')

        self.source_folder_label = ttk.Label(source_folder_frame, text="Select Source Folder:")
        self.source_folder_label.pack(side=tk.LEFT)

        self.text_box_source_folder = ttk.Entry(source_folder_frame)
        self.text_box_source_folder.pack(side=tk.LEFT, padx=(5, 0), fill='x', expand=True)

        # Browse button for manual folder selection
        self.browse_button = ttk.Button(source_folder_frame, text="Browse", command=lambda: on_browse_button_click(self))
        self.browse_button.pack(side=tk.LEFT, padx=(5, 0))

    def create_path_location_display(self):
        """Create UI elements to display the path location of the selected folder."""
        path_location_frame = ttk.Frame(self.container)
        path_location_frame.pack(padx=(10, 10), fill='x')

        path_location_label = ttk.Label(path_location_frame, text="Path:")
        path_location_label.pack(side=tk.LEFT)

        self.path_location_label = ttk.Label(path_location_frame, text=self.game_folder_selected_path, relief="solid", width=30)
        self.path_location_label.pack(side=tk.LEFT, padx=(10, 10), fill='x', expand=True)

        self.refresh_button = ttk.Button(path_location_frame, text="Refresh", command=lambda: refresAllList(self))
        self.refresh_button.pack(side=tk.LEFT, padx=(10, 0))
        
        self.open_folder_button = ttk.Button(path_location_frame, text="Open", command=lambda: open_folder(self.game_folder_selected_path))
        self.open_folder_button.pack(side=tk.LEFT, padx=(10, 0))


    def create_extract_archive_section(self):
        """Create UI elements for extracting available archives."""
        step1_label = ttk.Label(self.container, text="STEP 1 - Extract Available Archive", font=("Segoe UI", 12, "bold"))
        step1_label.pack(padx=(10, 10), pady=(5, 10), anchor='w')

        self.available_archive_label = ttk.Label(self.container, text="Available Archive", padding=(0, 5))
        self.available_archive_label.pack(anchor='w', padx=(10, 10))

        # Scrollable frame for available archives
        self.available_archive_frame = ttk.Frame(self.container)
        self.available_archive_frame.pack(padx=(10, 10), pady=(0, 0), fill='x')

        # Listbox for available archives
        self.available_archive_listbox = ttk.Treeview(self.available_archive_frame, columns=("No", "Archive Name"), show='headings', height=5)
        self.available_archive_listbox.column("No", width=30, anchor=tk.W)  
        self.available_archive_listbox.heading("No", text="No")
        self.available_archive_listbox.column("Archive Name", width=500, anchor=tk.W) 
        self.available_archive_listbox.heading("Archive Name", text="Archive Name")
        self.available_archive_listbox.pack(side=tk.LEFT, fill='both', expand=True)

        self.scrollbar = ttk.Scrollbar(self.available_archive_frame, orient="vertical", command=self.available_archive_listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill='y')
        self.available_archive_listbox.configure(yscrollcommand=self.scrollbar.set)

        # Bind selection event for available archives
        self.available_archive_listbox.bind("<<TreeviewSelect>>", lambda event: on_archive_selected(self, self.available_archive_listbox.selection()))

        # Horizontal panel for Extract buttons
        extract_button_frame = ttk.Frame(self.container)
        extract_button_frame.pack(padx=(10, 10), pady=(5, 10), fill='x')

        # Extract Selected Button 
        self.extract_selected_button = ttk.Button(extract_button_frame, text="Extract Selected")
        self.extract_selected_button.configure(command=lambda: extract_archives(self, self.selected_archive_paths if isinstance(self.selected_archive_paths, list) else [self.selected_archive_paths]))
        self.extract_selected_button.pack_forget()

        # Extract All Button 
        self.extract_all_button = ttk.Button(extract_button_frame, text="Extract All", command=lambda: extract_archives(self, self.available_archive_paths_list))     
        self.extract_all_button.pack_forget()

        # Refresh available archives
        self.refresh_available_archives()

    def create_source_folder_review_section(self):
        """Create UI elements to review the source folder."""
        step2_label = ttk.Label(self.container, text="STEP 2 - Review Your Source Folder", font=("Segoe UI", 12, "bold"))
        step2_label.pack(padx=(10, 10), pady=(5, 10), anchor='w')

        self.source_folder_review_label = ttk.Label(self.container, text="List Source Folder", padding=(0, 5))
        self.source_folder_review_label.pack(padx=(10, 10), anchor='w')

        # Scrollable frame for source folder list
        self.source_folder_frame = ttk.Frame(self.container)
        self.source_folder_frame.pack(padx=(10, 10), pady=(0, 0), fill='both', expand=True)

        self.source_folder_listbox = ttk.Treeview(self.source_folder_frame, columns=("No", "Folder Name"), show='headings', height=5)
        self.source_folder_listbox.column("No", width=30, anchor=tk.W)  
        self.source_folder_listbox.heading("No", text="No")
        self.source_folder_listbox.column("Folder Name", width=500, anchor=tk.W)  
        self.source_folder_listbox.heading("Folder Name", text="Folder Name")
        self.source_folder_listbox.pack(side=tk.LEFT, fill='both', expand=True)

        # Bind selection event to update rename text box
        self.source_folder_listbox.bind("<<TreeviewSelect>>", lambda event: on_source_folder_selected(self, self.source_folder_listbox.selection(), event))

        self.scrollbar_source = ttk.Scrollbar(self.source_folder_frame, orient="vertical", command=self.source_folder_listbox.yview)
        self.scrollbar_source.pack(side=tk.RIGHT, fill='y')
        self.source_folder_listbox.configure(yscrollcommand=self.scrollbar_source.set)

        # Horizontal layout for Rename
        self.create_rename_section()
        self.refresh_available_source_folders()

    def create_rename_section(self):
        """Create UI elements for renaming selected folders."""
        rename_frame = ttk.Frame(self.container)
        rename_frame.pack(padx=(10, 10), pady=(5, 10), fill='x')

        self.rename_label = ttk.Label(rename_frame, text="Rename:")
        self.rename_label.pack(side=tk.LEFT)

        self.rename_text_box = ttk.Entry(rename_frame)
        self.rename_text_box.pack(side=tk.LEFT, padx=(10, 10), pady=(5, 10), fill='x', expand=True)
        self.rename_text_box.bind("<KeyRelease>", lambda event: on_rename_text_change(self, event))
        
        self.open_source_folder_button = ttk.Button(rename_frame, text="Open Folder", command=lambda: open_folder(self.list_source_selected_path))
        self.open_source_folder_button.pack_forget()
        self.rename_button = ttk.Button(rename_frame, text="Apply", command=lambda: rename_selected(self, self.source_folder_listbox.selection()))
        self.rename_button.pack_forget()

        # Separator
        ttk.Separator(self.container, orient='horizontal').pack(fill='x', padx=(10, 10), pady=(5, 10))

    def create_destination_folder_confirmation(self):
        """Create UI elements to confirm the destination folder."""
        self.destination_folder = folder_management.check_and_determine_destination_folder(self.destination_path_list, self.game_folder_selected)
        log_message(f"destination_folder: {self.destination_folder}")

        step3_label = ttk.Label(self.container, text="STEP 3 - Confirm if You're Ready to Move", font=("Segoe UI", 12, "bold"))
        step3_label.pack(padx=(10, 10), pady=(5, 10), anchor='w')

        # Horizontal layout for Destination Folder
        destination_frame = ttk.Frame(self.container)
        destination_frame.pack(padx=(10, 10), pady=(5, 10), fill='x')

        self.destination_folder_label = ttk.Label(destination_frame, text="Destination:")
        self.destination_folder_label.pack(side=tk.LEFT)

        # Setup destination folder entry
        self.text_box_destination_folder = ttk.Entry(destination_frame)
        self.text_box_destination_folder.config(state='normal')
        self.text_box_destination_folder.delete(0, tk.END)
        self.text_box_destination_folder.insert(0, self.destination_folder if self.destination_folder else "Click Browse to select a folder")
        self.text_box_destination_folder.config(state='readonly')
        self.text_box_destination_folder.pack(side=tk.LEFT, padx=(5, 0), fill='x', expand=True)

        # Browse button for destination folder
        self.browse_destination_button = ttk.Button(destination_frame, text="Browse", command=lambda: browse_destination_folder(self))
        self.browse_destination_button.pack(side=tk.LEFT, padx=(5, 0))

        # Process Folder button
        self.process_folder_button = ttk.Button(self.container, text="Process Folder", command=lambda: process_folder_actions(self, self.game_folder_selected_path, self.available_source_folders_list, self.destination_folder), style="Accent.TButton")
        self.process_folder_button.pack(padx=(10, 10), pady=(5, 10), fill='x')

    def refresh_available_archives(self):
        """Refresh the available archives Listbox."""
        
        # Clear the current contents of the Listbox
        self.available_archive_listbox.delete(*self.available_archive_listbox.get_children())
        log_message("Cleared all children in available_archive_listbox")

        # List all available archives in the selected game folder
        self.available_archive_list = archive_utils.list_archive_files_in_directory(self.game_folder_selected_path)
        log_message("Repopulated available_archive_listbox")

        # If no archives found, display a message
        if not self.available_archive_list:
            self.available_archive_listbox.insert("", "end", values=("-", "No archive found"))
            self.extract_all_button.pack_forget()
        else:
            self.extract_all_button.pack(side=tk.RIGHT, padx=5)
            for index, (name, path) in enumerate(self.available_archive_list, start=1):
                # Add number and name to available_archive_listbox
                self.available_archive_listbox.insert("", "end", values=(index, name))

        # Update the list of selected archive paths
        self.available_archive_paths_list = [path for name, path in self.available_archive_list]
        self.selected_archive_paths = []
        self.extract_selected_button.pack_forget()

    def refresh_available_source_folders(self):
        """Refresh the available source folder Listbox."""

        # Clear the current contents of the Listbox
        self.source_folder_listbox.delete(*self.source_folder_listbox.get_children())
        log_message("Cleared all children in source_folder_listbox")

        # List all available source folders in the selected game folder
        self.available_source_folders_list = folder_management.list_available_source_folders(self.game_folder_selected_path)
        log_message("Repopulated source_folder_listbox")

        # If no source folders found, display a message
        if not self.available_source_folders_list:
            self.source_folder_listbox.insert("", "end", values=("-", "No source folder found"))
            self.open_source_folder_button.pack_forget()
            self.rename_button.pack_forget()
        else:
            # Populate source folder list
            for index, (folder_name, folder_path) in enumerate(self.available_source_folders_list, start=1):
                self.source_folder_listbox.insert("", "end", values=(index, folder_name))
      

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
