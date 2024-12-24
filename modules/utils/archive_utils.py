import os
import shutil
import patoolib
from modules.utils.logging_utils import log_message

def create_temp_dir(destination_dir: str) -> str:
    """Create a unique temporary directory with a suffix."""
    base_temp_dir = os.path.join(destination_dir, ".temp")
    temp_dir = base_temp_dir
    suffix = 1

    # Check if the temp directory already exists and create a new one with a suffix
    while os.path.exists(temp_dir):
        temp_dir = f"{base_temp_dir}{suffix}"
        suffix += 1

    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def validate_archive(archive_path: str) -> bool:
    """Check if the specified archive file exists and is not corrupted.
       Return True if valid, False otherwise."""
    if not os.path.isfile(archive_path):
        log_message(f"'{archive_path}' is not a valid file.")
        return False
    
    # Validate using patool for all formats
    try:
        patoolib.test_archive(archive_path)
        log_message(f"'{archive_path}' is valid.")
        return True
    except Exception as e:
        log_message(f"'{archive_path}' is not a valid archive file: {e}")
        return False

def extract_archive(archive_path: str, password: str = None) -> str:
    """Extract files from an archive and handle top-level items logic."""
    
    # Validate the archive before extraction
    if not validate_archive(archive_path):
        log_message(f"Extraction aborted for '{archive_path}' due to validation failure.")
        return "FAILED"

    archive_name = os.path.splitext(os.path.basename(archive_path))[0]
    destination_dir = os.path.dirname(archive_path)
    temp_dir = create_temp_dir(destination_dir)  # Create a unique temp directory
    log_message(f"Extracting '{archive_path}' temporarily from '{temp_dir}' to '{destination_dir}'...")

    # Extract the archive to the temporary directory
    try:
        patoolib.extract_archive(archive_path, outdir=temp_dir, password=password)
        log_message(f"Successfully extracted '{archive_path}' to '{temp_dir}'.")

        # Check the contents of the temporary directory
        items = os.listdir(temp_dir)

        # Initialize lists to hold image files and folders
        image_files = []
        folder_name = None

        for item in items:
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                folder_name = item  # Store the folder name if found
            elif item.lower().endswith(('.jpeg', '.jpg', '.png', '.gif')):
                image_files.append(item)  # Collect image files

        # Check conditions
        if folder_name and image_files:
            # Move image files into the identified folder
            target_folder_path = os.path.join(temp_dir, folder_name)
            for image in image_files:
                shutil.move(os.path.join(temp_dir, image), target_folder_path)
            log_message(f"Moved image files to '{target_folder_path}'.")

            # Move the folder containing images to the destination directory
            shutil.move(target_folder_path, destination_dir)
            log_message(f"Moved '{folder_name}' to '{destination_dir}'.")

        elif len(items) == 1 and os.path.isdir(os.path.join(temp_dir, items[0])):
            # Only one top-level folder, move it to the destination directory
            single_folder = items[0]
            new_folder_path = os.path.join(destination_dir, single_folder)
            log_message(f"Target extraction path: {new_folder_path}.")

            # Check if the extraction path already exists
            if os.path.exists(new_folder_path):
                log_message(f"Single item found in '{temp_dir}'. Destination directory '{new_folder_path}' already exists.")
                return "ALREADY"  # Return if the folder already exists

            shutil.move(os.path.join(temp_dir, single_folder), destination_dir)
            log_message(f"Moved '{single_folder}' to '{destination_dir}'.")

        else:
            # Multiple items, create a new folder with the name of the archive
            new_folder_path = os.path.join(destination_dir, archive_name)
            log_message(f"Target extraction path: {new_folder_path}.")
            
            # Check if the extraction path already exists
            if os.path.exists(new_folder_path):
                log_message(f"Multiple items found in '{temp_dir}'. Destination directory '{new_folder_path}' already exists.")
                return "ALREADY"  # Return if the folder already exists

            os.makedirs(new_folder_path, exist_ok=True)

            # Move all items to the new folder
            for item in items:
                shutil.move(os.path.join(temp_dir, item), new_folder_path)
            log_message(f"Moved items to '{new_folder_path}'.")

        # Move the archive file to the extracted folder
        extracted_folder = os.path.join(destination_dir, ".extracted")
        os.makedirs(extracted_folder, exist_ok=True)

        # Define the destination path for the archive
        archive_destination_path = os.path.join(extracted_folder, os.path.basename(archive_path))

        # Overwrite if the file already exists
        if os.path.exists(archive_destination_path):
            os.remove(archive_destination_path)  # Remove the existing file

        shutil.move(archive_path, archive_destination_path)
        log_message(f"Moved archive '{archive_path}' to '{archive_destination_path}'.")

        return "SUCCESS"  # Return success if extraction is completed
    except Exception as e:
        log_message(f"Failed to extract '{archive_path}': {e}")
        return "FAILED"
    finally:
        # Clean up the temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def list_archive_files_in_directory(root_path):
    """List all archive files in the specified directory."""
    archive_files = []

    # Supported archive formats by libarchive
    supported_formats = (
        '.7z', '.ace', '.adf', '.alz', '.ape', '.a', '.arc', '.arj', 
        '.bz2', '.bz3', '.cab', '.chm', '.Z', '.cpio', '.deb', 
        '.dms', '.flac', '.gz', '.iso', '.lrz', '.lha', '.lzh', 
        '.lz', '.lzma', '.lzo', '.rpm', '.rar', '.rz', '.shn', 
        '.tar', '.udf', '.xz', '.zip', '.zoo', '.zst'
    )


    try:
        for file_name in os.listdir(root_path):
            file_path = os.path.join(root_path, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith(supported_formats):
                archive_files.append((file_name, file_path))

        log_message(f"Archive files found in '{root_path}': {archive_files}")
    except Exception as e:
        log_message(f"Error while listing archive files in '{root_path}': {e}")

    return archive_files

def delete_archive(archive_path):
    """Delete the specified archive file."""
    try:
        if os.path.isfile(archive_path):
            os.remove(archive_path)
            log_message(f"Deleted archive file: {archive_path}")
        else:
            log_message(f"Archive file '{archive_path}' does not exist.")
    except Exception as e:
        log_message(f"Error deleting archive file '{archive_path}': {e}")

def move_archive(source_path, destination_path):
    """Move the specified archive file to a new location."""
    try:
        if os.path.isfile(source_path):
            shutil.move(source_path, destination_path)
            log_message(f"Moved archive file from '{source_path}' to '{destination_path}'")
        else:
            log_message(f"Source archive file '{source_path}' does not exist.")
    except Exception as e:
        log_message(f"Error moving archive file from '{source_path}' to '{destination_path}': {e}")
