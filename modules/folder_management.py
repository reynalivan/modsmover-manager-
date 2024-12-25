import os
from modules.utils.folder_utils import (
    check_directory_exists,
    list_folders_in_directory,
    move_folder,
    rename_folder
)
from modules.utils.logging_utils import log_message
from tkinter import filedialog, messagebox

def list_available_game_folders(readytomoves_folder_path):
    """List all available source folders in the 'readytomoves' directory."""

    if not isinstance(readytomoves_folder_path, str):
        log_message("SOURCE_FOLDER_ROOT must be a string.")
        return None

    folders = list_folders_in_directory(readytomoves_folder_path)
    return folders


def list_available_source_folders(game_folder_selected):
    """List all available source folders in the selected game folder."""

    if not isinstance(game_folder_selected, str):
        log_message("GAME_FOLDER_SELECTED must be a string.")
        return None
    
    folder_name_list = list_folders_in_directory(game_folder_selected)
    # create new variable with add new folder name to list source_folders with (folder_name, folder_path)
    source_folders_with_path = []
    for folder_name in folder_name_list:
        folder_path_join = os.path.join(game_folder_selected, folder_name)
        source_folders_with_path.append((folder_name, folder_path_join))

    # Filter out folders with names ending in .extracted and .temp
    source_folders_with_path = [
        (folder_name, folder_path) for folder_name, folder_path in source_folders_with_path
        if not (folder_name.endswith('.extracted') or folder_name.endswith('.temp'))
    ]
    return source_folders_with_path

def browse_for_source_folder():
    selected_source_folder = filedialog.askdirectory(title="Select Source Folder")
    selected_source_name = os.path.basename(selected_source_folder)
    log_message(f"User selected source folder: {selected_source_folder}")
    if check_directory_exists(selected_source_folder) is False:
        log_message(f"Source folder {selected_source_folder} does not exist.")
        messagebox.showerror("Error", "{selected_source_folder} does not exist.")
        return

    # Memastikan bahwa selected_source_folder adalah string
    if not isinstance(selected_source_folder, str):
        selected_source_folder = str(selected_source_folder) 

    return selected_source_folder, selected_source_name


def check_and_determine_destination_folder(destination_path, selected_source_name):
    # Mengubah selected_source_name menjadi huruf kecil untuk pencarian case insensitive
    selected_source_name_lower = selected_source_name.lower()

    # Mencari nilai berdasarkan kunci dengan case insensitive
    for key in destination_path:
        if key.lower() == selected_source_name_lower:
            predefined_folder = destination_path[key]
            log_message(f"Using predefined value {predefined_folder}")
            if predefined_folder == "Not Set":
                log_message(f"Key '{selected_source_name}' is not set in '{destination_path}'")
                return None
            return predefined_folder

    log_message(f"Key '{selected_source_name}' not found in '{destination_path}'")

    return None


def process_folder(folders_to_move_mapping, destination_folder):
    """Process folders based on mapping data."""
    source_path_list = [result.source_path for result in folders_to_move_mapping]
    destination_foldername_list = [result.destination_name for result in folders_to_move_mapping]

    # Rename folders that do not have the 'DISABLED' prefix
    renamed_source_path_list = add_prefix_disabled_folders(source_path_list)

    # Move folders to their destination
    summary = {'moved': [], 'failed': [], 'duplicates': []}

    for renamed_source_path, destination_foldername in zip(renamed_source_path_list, destination_foldername_list):
        destination_path = os.path.join(destination_folder, destination_foldername)
        base_folder_name = os.path.basename(renamed_source_path)
        full_destination_path = os.path.join(destination_path, base_folder_name)
        if move_folder(renamed_source_path, full_destination_path):
            summary['moved'].append((renamed_source_path, full_destination_path))
            log_message(f"Successfully moved '{renamed_source_path}' to '{full_destination_path}'.")
        else:
            if os.path.exists(full_destination_path):
                summary['duplicates'].append((renamed_source_path, full_destination_path))
            else:
                summary['failed'].append((renamed_source_path, full_destination_path))
                log_message(f"Failed to move '{renamed_source_path}' to '{full_destination_path}'.")
    return summary


def add_prefix_disabled_folders(source_path_list):
    """Rename folders and add 'DISABLED' prefix if it doesn't already have it."""
    renamed_source_path_list = []  # List untuk menyimpan folder yang telah diubah namanya
    for source_path in source_path_list:
        if not check_directory_exists(source_path):
            log_message(f"Folder '{source_path}' does not exist.")
            messagebox.showerror("Error", f"Folder '{source_path}' may modified or deleted.")
            # Stop the process if folder does not exist
            return None
        
        # Set source_name from source folder name in source_path
        source_name = os.path.basename(source_path)
        
        # Add prefix 'DISABLED' to the folder name
        if source_name.startswith("DISABLED "):
            log_message(f"Folder '{source_name}' has already 'DISABLED' prefix.")
            renamed_source_path_list.append(source_path)  # Tidak ada perubahan, tambahkan path asli
            continue
        elif source_name.startswith("DISABLED_"):
            source_name_new = f"DISABLED {source_name[9:]}"  # Menghapus 'DISABLED_' dan menambahkan spasi
        elif source_name.startswith("DISABLED-"):
            source_name_new = f"DISABLED {source_name[9:]}"  # Menghapus 'DISABLED-' dan menambahkan spasi
        elif source_name.lower().startswith("disabled "):
            source_name_new = f"DISABLED {source_name[9:]}"  # Menghapus 'disabled ' dan menambahkan spasi
        else:
            source_name_new = f"DISABLED {source_name}"  # Tambahkan 'DISABLED ' jika tidak ada prefix

        # Create new source path with the new folder name
        source_path_new = os.path.join(os.path.dirname(source_path), source_name_new)

        if rename_folder(source_path, source_path_new):
            log_message(f"Renamed folder '{source_path}' to '{source_name_new}'.")
            renamed_source_path_list.append(source_path_new) 
        else:
            log_message(f"Folder '{source_path}' already has 'DISABLED' prefix or failed to rename.")
            renamed_source_path_list.append(source_path) 

    return renamed_source_path_list


if __name__ == "__main__":
    # This will be set or passed as needed in main.py
    pass
