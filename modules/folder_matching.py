import os
from rapidfuzz import fuzz
from unidecode import unidecode
from dataclasses import dataclass
from modules.utils.folder_utils import list_folders_in_directory
from typing import List, Dict, Tuple, Optional, Any, Set
from modules.utils.logging_utils import log_message

@dataclass
class MatchResult:
    source_path: str
    destination_name: str
    confidence: float
    reason: str
    category: str

def normalize_folder_name(folder: str, skipworld_list: List[str], ignore_numbers: bool) -> str:
    """Normalize a single folder name by removing unwanted substrings and formatting."""
    normalized = unidecode(folder).strip()
    
    # Remove unwanted words
    for skip_word in skipworld_list:
        normalized = normalized.replace(skip_word, '')
    
    # Ignore numbers if desired
    if ignore_numbers:
        normalized = ''.join(filter(lambda x: not x.isdigit(), normalized))
    
    # Format folder name
    return normalized.replace("_", " ").title()

def normalize_folders(source_subfolders: List[str], selected_source_folder: str, skipworld_list: List[str], ignore_numbers: bool) -> Dict[str, Tuple[str, str]]:
    """Normalize source folder names by removing unwanted substrings, numbers, and formatting."""
    path_to_normalized_map = {}
    for folder in source_subfolders:
        full_path = os.path.join(selected_source_folder, folder)
        normalized_name = normalize_folder_name(folder, skipworld_list, ignore_numbers)
        path_to_normalized_map[full_path] = (folder, normalized_name.strip())
    
    log_message(f"Normalized folder mapping: {path_to_normalized_map}")
    return path_to_normalized_map

def apply_aliases(normalized_map: Dict[str, Tuple[str, str]], alias_data: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    """Apply aliases to normalized folder names and return a mapping of full paths to normalized names and their aliases."""
    path_to_alias_map = {}

    if not alias_data:
        log_message("No alias data provided.")
        return {full_path: (original_name, normalized_name) for full_path, (original_name, normalized_name) in normalized_map.items()}

    for full_path, (original_name, normalized_name) in normalized_map.items():
        folder_lower = normalized_name.lower()
        alias_name = next((alias for key, alias in alias_data.items() if key in folder_lower), normalized_name).strip()
        path_to_alias_map[full_path] = (original_name, alias_name)

    log_message(f"Alias applied mapping: {path_to_alias_map}")
    return path_to_alias_map

def partial_match(source_name: str, destination_names: List[str]) -> bool:
    """Check if the source name partially matches any of the destination names."""
    # Normalize the source name by removing spaces and converting to lowercase
    normalized_source = source_name.replace(" ", "").lower()
    for destination in destination_names:
        normalized_destination = destination.replace(" ", "").lower()
        if normalized_source in normalized_destination or normalized_destination in normalized_source:
            return True
    return False

def check_files_in_subfolder(subfolder_path: str, extensions_check: List[str], destination_folders: List[str]) -> Optional[str]:
    """Check for files in the specified subfolder that match the destination folder names."""
    log_message(f"Checking for files in subfolder: {subfolder_path}")

    if not extensions_check or not destination_folders:
        log_message("No extensions or destination folders provided for checking.")
        return None

    extensions_set = set(extensions_check)
    
    for root, _, files in os.walk(subfolder_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions_set):
                matched_destination = partial_match(file, destination_folders)
                if matched_destination:
                    log_message(f"Found matching file: {os.path.join(root, file)} for destination folder: {matched_destination}")
                    return matched_destination

    log_message(f"No matching files found in {subfolder_path}")
    return None

def process_match_to_categorized(
        selected_source_folder: str, 
        available_source_folders_list: List[Tuple[str, str]],
        destination_folder: str,
        alias_data: Dict[str, str], 
        similarity_threshold: Dict[str, int], 
        extensions_check: List[str], 
        skipworld_list: List[str],
        ignore_numbers_status: bool,  
        ) -> List[MatchResult]:
    """Process matching for a source folder and return a categorized dictionary of results for all destination folders."""
    
    # Extract confidence thresholds
    high_confidence_threshold = similarity_threshold.get('HIGH_CONFIDENCE', 0)
    medium_confidence_threshold = similarity_threshold.get('MEDIUM_CONFIDENCE', 0)

    if not selected_source_folder:
        log_message("No source folder selected. Please ensure the folder exists and try again.")
        return {}
    
    # Get all subfolders in the source directory
    available_source_folders_list_path = [path for _, path in available_source_folders_list]
    if not available_source_folders_list_path:
        log_message(f"Source folder '{selected_source_folder}' is empty or not found.")
        return {}
    
    # Get all subfolders in the destination directory
    list_destination_subfolders = list_folders_in_directory(destination_folder)
    if not list_destination_subfolders:
        log_message(f"Destination folder '{destination_folder}' is empty or not found.")
        return {}

    log_message(f"Found {len(available_source_folders_list_path)} source subfolders and {len(list_destination_subfolders)} destination subfolders.")
    
    # Normalize source folder names
    normalized_map = normalize_folders(available_source_folders_list_path, selected_source_folder, skipworld_list, ignore_numbers_status)
    
    # Apply aliases to normalized names
    path_to_name_map = apply_aliases(normalized_map, alias_data)
    
    # Match folders and categorize results
    mapping_data = get_matching_weight(
            selected_source_folder,
            list(path_to_name_map.keys()), 
            [value[1] for value in path_to_name_map.values()],  # Use normalized names for matching
            list_destination_subfolders,
            extensions_check
    )
    log_message(f"Mapping data: {mapping_data}")
    if not mapping_data:
        log_message("Mapping data is empty after get_matching_weight.")
        return {}
    
    # Create categorized results based on mapping data
    categorized_results = []

    for full_path, destination_match, confidence, reason in mapping_data:
        # Determine the category based on confidence
        if confidence >= high_confidence_threshold:
            category = 'HIGH'
        elif confidence >= medium_confidence_threshold:
            category = 'MEDIUM'
        else:
            category = 'LOW'
        
        # Create a MatchResult instance and add it to the results list
        match_result = MatchResult(
            source_path=full_path,
            destination_name=destination_match,
            confidence=confidence,
            reason=reason,
            category=category
        )
        categorized_results.append(match_result)

    log_message(f"Categorized Results: {categorized_results}")

    return categorized_results

def get_matching_weight(
    selected_source_folder: str,
    list_selected_source_subfolder: List[str],  # as original_source_name
    normalized_reference_dict: List[str],  # as normalized_source_name
    list_destination_subfolders: List[str],  # as destination_name
    extensions_check: List[str]
) -> List[Tuple[str, str, int]]:
    """
    Calculate matching weights between original source names and destination folders.
    Returns a list of tuples containing original_source_name, best match folder, and matching weight.
    """
    results = []  # List to hold all match results

    log_message(
        f"\n \n"
        f"#################################\n"
        f"selected_source_folder = {selected_source_folder} \n"
        f"list_selected_source_subfolder= '{list_selected_source_subfolder}', \n"
        f"normalized_reference_dict= '{normalized_reference_dict}', \n"
        f"list_destination_subfolder= '{list_destination_subfolders}', \n"
        f"#################################"
        f"\n \n"
    )

    # Loop through each source folder
    for original_source_name, normalized_name in zip(list_selected_source_subfolder, normalized_reference_dict):
        log_message(f"Processing source folder: {original_source_name}")
        
        match_result = {
            'source_path': original_source_name,
            'matched_destination': 'Not Found',  # Default value if no match is found
            'confidence': 0,
            'reason': '',
        }

        # Check for matches against all destination folders
        for destination in list_destination_subfolders:
            log_message(f"Checking match folder {original_source_name} with '{destination}'")

            # Check for partial match by folder name
            if partial_match(normalized_name, [destination]):
                match_result['matched_destination'] = destination
                match_result['confidence'] = 100  # Set confidence to 100 for partial match
                match_result['reason'] = "Matched by folder name"
                log_message(f"✅ Match folder name '{original_source_name}' with '{destination}' \n\n")
                results.append((original_source_name, destination, match_result['confidence'], match_result['reason']))  # Append to results
                break  # Move to the next source folder

        # If a match was found by folder name, skip further checks
        if match_result['confidence'] == 100:
            continue

        # Check for matching files in the original source folder
        source_path = os.path.join(selected_source_folder, original_source_name)
        for destination in list_destination_subfolders:
            matched_file_destination = check_files_in_subfolder(source_path, extensions_check, [destination])
            if matched_file_destination:
                match_result['matched_destination'] = destination
                match_result['confidence'] = 100
                match_result['reason'] = "Matched by file name"
                results.append((original_source_name, destination, match_result['confidence'], match_result['reason']))  # Append to results
                log_message(f"✅ Match file on folder '{original_source_name}' with '{destination}' \n\n")
                break  # Move to the next source folder

        # If no match was found by file name, perform fuzzy matching
        if match_result['confidence'] == 0:
            best_match = None
            best_confidence = 0
            for destination in list_destination_subfolders:
                similarity = fuzz.ratio(normalized_name, destination)
                log_message(f"Comparing '{original_source_name}' with '{destination}': Similarity = {similarity}")

                # Update best match if the similarity is higher than the current best
                if similarity > best_confidence:
                    best_confidence = similarity
                    best_match = destination

            # If a fuzzy match was found, record it
            if best_confidence > 0:
                match_result['matched_destination'] = best_match
                match_result['confidence'] = best_confidence
                match_result['reason'] = "Matched by fuzzy matching"
                results.append((original_source_name, best_match, best_confidence, match_result['reason']))  # Append to results

        # If no matches were found, keep the default values
        if match_result['confidence'] == 0:
            match_result['reason'] = "No significant match found"
            results.append((original_source_name, match_result['matched_destination'], match_result['confidence'], match_result['reason']))  # Append to results

    return results
