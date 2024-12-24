from tkinter import filedialog, messagebox
import os
import tkinter as tk  # Import tkinter here
import modules.folder_management as folder_management  # For folder operations
from modules.extract_popup_ui import ArchiveExtractorPopup 
from modules.matching_popup_ui import MatchingPopup
from modules.matching_result_ui import MatchingResultPopup
from modules.utils.logging_utils import log_message                                    
import modules.folder_matching as folder_matching  # For matching folders
from modules.settings_ui import SettingsUI

def on_source_folder_selected(self, selected_items, event):
    """Update the rename text box with the selected folder name."""
    if selected_items:
        self.list_source_selected_path = []

        for item in selected_items:
             # Get the values of the selected item
            values = self.source_folder_listbox.item(item, 'values')
            folder_name = values[1]  # Get the archive name only 
            folder_path = next((path for name, path in self.available_source_folders_list if name == folder_name), None)

            if not folder_path or folder_name == "No source folder found":
                self.rename_button.pack_forget()
                self.open_source_folder_button.pack_forget()
            else:
                log_message(f"Selected folder: {folder_name}")
                self.list_source_selected_path = os.path.join(self.game_folder_selected_path, folder_name)
                self.rename_text_box.delete(0, tk.END)  # Clear the text box
                self.rename_text_box.insert(0, folder_name)  # Insert the selected folder name
                self.open_source_folder_button.pack(side=tk.LEFT, padx=(10, 0))
                
           

def browse_source_folder(self):
    """Open a dialog to select a source folder and update the text box."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        self.text_box_source_folder.config(state='normal')
        self.text_box_source_folder.delete(0, tk.END)
        self.text_box_source_folder.insert(0, folder_selected)
        self.text_box_source_folder.config(state='readonly')

def browse_destination_folder(self):
    """Open a dialog to select a destination folder and update the text box."""
    folder_path_selected = filedialog.askdirectory()
    if folder_path_selected:
        self.text_box_destination_folder.config(state='normal')
        self.text_box_destination_folder.delete(0, tk.END)
        self.text_box_destination_folder.insert(0, folder_path_selected)
        self.text_box_destination_folder.config(state='readonly')
        self.destination_folder = folder_path_selected

        # Check if the key exists in DESTINATION_PATH
        if self.config_utils.key_exists_in_destination_path(self.game_folder_selected):
            # Directly update ConfigUtils on key self.game_folder_selected in DESTINATION_PATH with new path from folder_path_selected
            self.config_utils.update_destination_path(self.game_folder_selected, folder_path_selected)
            log_message(f"Destination folder updated to: {folder_path_selected}")
        else:
            # If the key does not exist, you can choose to log or handle it as needed
            self.config_utils.add_destination_path(self.game_folder_selected, folder_path_selected)
            log_message(f"Key '{self.game_folder_selected}' not found in DESTINATION_PATH. No update performed.")

        log_message(f"Destination folder: {folder_path_selected}")

def open_folder(folder_path):
    """Open the specified folder in the file explorer."""
    if os.path.exists(folder_path):
        os.startfile(folder_path)  # Open the folder in the file explorer
    else:
        messagebox.showwarning("Warning", "Folder not found!")

def rename_selected(self, selected_index):
    """Rename the selected folder based on the input in the rename text box."""
    if not selected_index:
        messagebox.showwarning("Warning", "No source folder selected!")
        return

    # Get the current folder name and the new name from the text box
    item = self.source_folder_listbox.item(selected_index)
    current_folder_name = item['values'][1]  # Get the current folder name
    new_name = self.rename_text_box.get().strip()  # Get the new name and strip whitespace

    if not new_name:
        messagebox.showwarning("Warning", "New folder name cannot be empty!")
        return

    # Check if the directory exists
    current_folder_path = os.path.join(self.game_folder_selected_path, current_folder_name)
    if not os.path.exists(current_folder_path):
        messagebox.showwarning("Warning", "The folder may have been modified or moved. Please check again.")
        return

    # Check if the new name already exists
    existing_folders = [folder_name for folder_name, _ in self.available_source_folders_list]
    if new_name in existing_folders:
        messagebox.showwarning("Warning", f"Name already exists: '{new_name}'")
        self.rename_button.pack_forget()  # Hide the Apply button if the name exists
        return
    
    # Confirm the rename action
    confirmation = messagebox.askyesno("Confirm Rename", f"Are you sure you want to rename '{current_folder_name}' to '{new_name}'?")
    if confirmation:
        # Perform the rename operationcls
        new_folder_path = os.path.join(self.game_folder_selected_path, new_name)
        try:
            os.rename(current_folder_path, new_folder_path)  # Rename the folder
            messagebox.showinfo("Success", f"Renamed '{current_folder_name}' to '{new_name}'")
            self.rename_button.pack_forget()
            self.refresh_available_source_folders()  # Refresh the list of source folders
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while renaming the folder: {str(e)}")

def on_rename_text_change(self, event):
    """Handle changes in the rename text box to check for existing names."""
    new_name = self.rename_text_box.get().strip()
    existing_folders = [folder_name for folder_name, _ in self.available_source_folders_list]

    if new_name in existing_folders:
        self.rename_button.pack_forget()  # Hide the Apply button if the name exists
    else:
        self.rename_button.pack(side=tk.LEFT, padx=(10, 0))

def process_folder_actions(self, folder_selected_path, source_folders_list, destination_folder):
    """Process the folder at the specified destination."""
    
    if not folder_selected_path:
        messagebox.showwarning("Warning", "Folder path not selected!")
        return
      
    if not destination_folder:
        messagebox.showwarning("Warning", "Destination folder on STEP 3 not selected!")
        return
    
    if not source_folders_list:
        messagebox.showwarning("Warning", "No source folders available!")
        return
    
    # Perform processing logic here
    log_message(
        f"\n \n"
        f"#################################\n"
        f"get_matching_data value\n\n"
        f"selected_source_folder= '{folder_selected_path}', \n"
        f"available_source_folders_list= {self.available_source_folders_list}"
        f"destination_folder= '{destination_folder}', \n"
        f"alias_data= '{self.alias_data}', \n"
        f"similarity_threshold= '{self.similarity_threshold}', \n"
        f"extensions_check= '{self.extensions_check}',\n"
        f"skipworld_list='{self.skipworld_list}', \n"
        f"ignore_numbers_status='{self.ignore_numbers_status}'\n"
        f"#################################"
        f"\n \n"
    )

    get_matching_data = folder_matching.process_match_to_categorized(
        folder_selected_path,
        self.available_source_folders_list,
        destination_folder,
        self.alias_data,
        self.similarity_threshold,
        self.extensions_check,
        self.skipworld_list,
        self.ignore_numbers_status
    )        

    log_message(
        f"\n \n"
        f" ////////////////////////////////////////"
        f" {get_matching_data}"
        f" ////////////////////////////////////////"
        f"\n \n"
        )
    
    # Pastikan get_matching_data tidak None sebelum melanjutkan
    if get_matching_data:
    
        # Data mapping based on confidence level
        high_confidence_mapping = [
            result for result in get_matching_data if result.category == 'HIGH'
        ]
        medium_confidence_mapping = [
            result for result in get_matching_data if result.category == 'MEDIUM'
        ]
        low_confidence_mapping = [
            result for result in get_matching_data if result.category == 'LOW'
        ]

        # initiate total summary in every step
        total_summary = {}
        
        # Steps 1: High confidence
        if high_confidence_mapping:
            # Displays matching results
            high_confirm = MatchingPopup("high_confidence", high_confidence_mapping, self.root, self)
            
            # Wait until popup is closed
            self.root.wait_window(high_confirm.popup)

            # Handle user actions based on the button clicked
            if high_confirm.user_response:
                high_summary = folder_management.process_folder(high_confidence_mapping, self.destination_folder)
                self.refresh_available_source_folders() 

                # if folder_management.process_folder return none
                if high_summary:
                    total_summary.update(high_summary)
                else:
                    # stop processing if no summary is returned
                    log_message("Can't process high confidence folder")
                    return None
            else:
                log_message("User chose to skip the action.")
        else:
            log_message("No data with high confidence found. Skipping to medium confidence.")
            
        # Steps 2: Medium confidence
        if medium_confidence_mapping:
            # Displays matching results
            medium_confirm = MatchingPopup("medium_confidence", medium_confidence_mapping, self.root, self)
            
            # Wait until popup is closed
            self.root.wait_window(medium_confirm.popup)

            # Handle user actions based on the button clicked
            if medium_confirm.user_response:
                medium_summary = folder_management.process_folder(medium_confidence_mapping, self.destination_folder)
                self.refresh_available_source_folders() 

                if medium_summary:
                    total_summary.update(medium_summary)
                else:
                    # stop processing if no summary is returned
                    log_message("Can't process medium confidence folder")
                    return None
            else:
                log_message("User chose to skip the medium confidence folders.")
        else:
            log_message("No data with medium confidence found. Skipping to low confidence.")

        # Steps 3: Low confidence
        if low_confidence_mapping:
            # Displays matching results
            low_confirm = MatchingPopup("low_confidence", low_confidence_mapping, self.root, self)
            
            # Wait until popup is closed
            self.root.wait_window(low_confirm.popup)
        else:
            log_message("No data with low confidence found.")

        # Steps 4: Display total summary
        if total_summary:
            result_popup = MatchingResultPopup(total_summary, self.root)
            self.root.wait_window(result_popup.popup)
        else:
            log_message("No data to process.")
            messagebox.showinfo("Info", "No data to process.")

 
    else:
        log_message("No valid get_matching_data found. Please check the source and destination folders.")
        messagebox.showerror("Error", "No valid data found. Please check the source and destination folders.")

def on_browse_button_click(self):
    """Handle the event when the browse button is clicked to select a source folder."""
    source_folder_path_selected, source_folder_name_selected  = folder_management.browse_for_source_folder()
    self.source_folder_root = source_folder_path_selected
    self.game_folder_selected_path = source_folder_path_selected
    
    # Update the text box with the selected source folder root
    self.text_box_source_folder.config(state='normal')
    self.text_box_source_folder.delete(0, tk.END)
    self.text_box_source_folder.insert(0, self.source_folder_root)
    self.text_box_source_folder.config(state='readonly')

    log_message(
        f"self.source_folder_root: {self.source_folder_root}  \n"
        f"self.source_folder_selected: {self.game_folder_selected_path}"
    )
    self.refresh_available_archives()
    self.refresh_available_source_folders()


def on_archive_selected(self, selected_items):
    """Handle the event when an archive is selected from the list."""
    if selected_items:
        # Clear the previously selected paths
        self.selected_archive_paths = []

        for item in selected_items:
            # Get the values of the selected item
            values = self.available_archive_listbox.item(item, 'values')
            archive_name = values[1]  # Get the archive name only 

            # Get the archive path from self.available_archive_list using archive_name
            archive_path = next((path for name, path in self.available_archive_list if name == archive_name), None)
            
            # Check if archive_path is null or empty or archive_name is "No archive found"
            if not archive_path or archive_name == "No archive found":
                self.extract_selected_button.pack_forget()
            else:
                # Log the selected archive path
                log_message(f"Selected Archive Path: {archive_path}")
                self.selected_archive_paths.append(archive_path)  # Store the selected paths   
                
                # Show the button to extract the selected archive
                self.extract_selected_button.pack(side=tk.RIGHT, padx=5)
    else:
        if self.available_archive_listbox.get_children():
            log_message("No archive selected.")

def extract_archives(self, archive_paths): 
    """Initiate the extraction process for the selected archives."""
    # Check if archive_paths is empty
    if not archive_paths:
        log_message("No archive selected.")
        messagebox.showerror("Error", "Please select an archive to extract.")
        self.extract_selected_button.pack_forget()
        return  # Exit the function early since there's nothing to process

    # Check if any of the paths do not exist
    if any(not os.path.exists(path) for path in archive_paths):
        log_message("No valid archive selected or archives may have been moved/modified.")
        messagebox.showerror("Error", "No valid archive found. The file may have been moved or modified.")
        self.extract_selected_button.pack_forget()
        return  # Exit the function early since there's nothing to process

    # Proceed with extraction if all checks pass
    extractor_popup = ArchiveExtractorPopup(archive_paths, self.root, self)  # Pass the main app instance
    self.root.wait_window(extractor_popup)
    if extractor_popup.user_closed:
        self.refresh_available_archives()  # Refresh the available archives
    self.extract_selected_button.pack_forget()  # Hide the button after extraction

def open_settings(self):
    """Open the settings UI."""
    settings_popup = SettingsUI(self.root, self, self.config_utils, self.base_dir, self.config_path, self.dictionary_path, self.readytomoves_dir, firstinitial=False)
           
    if settings_popup.user_saved:
        self.reload_settings()  # Reload the settings after the popup is closed
