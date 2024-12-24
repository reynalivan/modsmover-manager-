import os
import shutil
from modules.utils.logging_utils import log_message

def check_directory_exists(path):
    if not isinstance(path, str):
        log_message(f"Provided path is not a string: {path}")
        return False
    return os.path.isdir(path)

def list_folders_in_directory(path):
    """List all folders in a specified directory."""
    try:
        folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
        log_message(f"Found folders in '{path}': {folders}")
        return folders
    except Exception as e:
        log_message(f"Error listing folders in '{path}': {e}")
        return []

def move_folder(source, destination):
    """Move a folder from the source path to the destination path."""
    if not os.path.isdir(source):
        log_message(f"Source folder '{source}' does not exist.")
        return False

    try:
        # Pindahkan folder ke tujuan
        shutil.move(source, destination)
        log_message(f"Moved folder from '{source}' to '{destination}'.")
        return True
    except Exception as e:
        log_message(f"Failed to move folder from '{source}' to '{destination}': {e}")
        return False

def rename_folder(old_name, new_name):
    """Rename a folder."""
    if not os.path.isdir(old_name):
        log_message(f"Folder '{old_name}' does not exist.")
        return False

    try:
        os.rename(old_name, new_name)
        log_message(f"Renamed folder from '{old_name}' to '{new_name}'.")
        return True
    except Exception as e:
        log_message(f"Failed to rename folder from '{old_name}' to '{new_name}': {e}")
        return False

# Example usage
if __name__ == "__main__":

    # Example function calls
    list_folders_in_directory('some_directory')
    move_folder('old_folder', 'new_folder')
    rename_folder('new_folder', 'renamed_folder')
