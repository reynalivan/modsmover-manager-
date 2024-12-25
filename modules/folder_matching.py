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

def normalize_folders(source_subfolder_list: List[str], skipworld_list: List[str], ignore_numbers: bool) -> Dict[str, Tuple[str, str]]:
    """Normalize source folder names by removing unwanted substrings, numbers, and formatting."""
    path_to_normalized_map = {}
    for source_subfolder in source_subfolder_list:
        source_basename = os.path.basename(source_subfolder)
        normalized_name = normalize_folder_name(source_basename, skipworld_list, ignore_numbers)
        path_to_normalized_map[source_subfolder] = (source_basename, normalized_name.strip())
    
    log_message(f"Normalized folder mapping: {path_to_normalized_map}")
    return path_to_normalized_map

def apply_aliases(normalized_map: Dict[str, Tuple[str, str]], alias_data: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    """Apply aliases to normalized folder names and return a mapping of full paths to normalized names and their aliases."""
    if not alias_data:
        log_message("No alias data provided.")
        return normalized_map
    
    path_to_alias_map = {}
    for full_path, (original_name, normalized_name) in normalized_map.items():
        found_match = False
        for alias_key, alias_value in alias_data.items():
            if alias_key.lower() in normalized_name.lower():
                path_to_alias_map[full_path] = (original_name, alias_value)
                found_match = True
                log_message(f"Found alias for folder '{original_name}' -> '{alias_value}'")
                break
                
        if not found_match:
            path_to_alias_map[full_path] = (original_name, normalized_name)

    log_message(f"Alias mapping complete: {path_to_alias_map}")
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

import os
from typing import List, Optional

import os
from typing import List, Optional

def check_files_in_subfolder(
    subfolder_path: str,
    extensions_check: List[str],
    destination_folders: List[str],
    normalized_reference_dict: dict
) -> Optional[str]:
    """Check for files and folders in the specified subfolder that match the destination folder names using normalized names."""
    log_message(f"Checking for files and folders in subfolder: {subfolder_path}")

    if not extensions_check or not destination_folders:
        log_message("No extensions or destination folders provided for checking.")
        return None

    extensions_set = set(extensions_check)

    # Traverse the directory structure up to 3 levels deep
    for root, dirs, files in os.walk(subfolder_path):
        # Limit the depth of the search to 3 levels
        depth = root[len(subfolder_path):].count(os.sep)
        if depth > 3:
            continue

        # Check for matching folders
        for dir_name in dirs:
            normalized_dir_name = dir_name.replace(" ", "").lower()
            # Check against normalized_reference_dict values
            for alias in normalized_reference_dict:
                if partial_match(normalized_dir_name, [alias]):
                    log_message(f"Found matching on subfolder: {os.path.join(root, dir_name)} for destination folder: {alias}")
                    return alias

        # Check for matching files
        for file in files:
            if any(file.endswith(ext) for ext in extensions_set):
                normalized_file_name = file.replace(" ", "").lower()
                # Check against normalized_reference_dict values
                for alias in normalized_reference_dict.values():
                    if partial_match(normalized_file_name, [alias[1]]):  # Use the alias for matching
                        log_message(f"Found matching file: {os.path.join(root, file)} for destination folder: {alias[1]}")
                        return alias[1]  # Return the matched alias

    log_message(f"No matching files or folders found in {subfolder_path}")
    return None

def process_match_to_categorized(
        selected_source_folder: str, # Root Folder
        source_folders_list: List[Tuple[str, str]], # List Alvailable source want to process
        destination_folder: str,  # Root destination folder
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
    source_folders_list_path = [path for _, path in source_folders_list]
    if not source_folders_list_path:
        log_message(f"Source folder '{selected_source_folder}' is empty or not found.")
        return {}
    
    # Get all subfolders in the destination directory
    destination_folder_subfolder_list = list_folders_in_directory(destination_folder)
    if not destination_folder_subfolder_list:
        log_message(f"Destination folder '{destination_folder}' is empty or not found.")
        return {}

    log_message(f"Found {len(source_folders_list_path)} source subfolders and {len(destination_folder_subfolder_list)} destination subfolders.")
    
    # Normalize source folder names
    normalized_map = normalize_folders(source_folders_list_path, skipworld_list, ignore_numbers_status)
    log_message(f"Normalizing source folders: {normalized_map}")
    
    # Apply aliases to normalized names
    path_to_name_map = apply_aliases(normalized_map, alias_data)
    log_message(f"Applying aliases: {path_to_name_map}")
    
    # Match folders and categorize results
    mapping_data = get_matching_weight(
            selected_source_folder,
            list(path_to_name_map.keys()), 
            [value[1] for value in path_to_name_map.values()],  # Use normalized and alias applied folder names for matching
            destination_folder_subfolder_list,
            extensions_check
    )

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

    return categorized_results

def get_matching_weight(
    selected_source_folder: str,
    list_selected_source_subfolder: List[str],
    normalized_reference_dict: List[str],
    list_destination_subfolders: List[str],
    extensions_check: List[str]
) -> List[Tuple[str, str, int, str]]:
    """
    Three-step matching process between source and destination folders.
    Returns list of tuples: (source_path, destination, confidence, reason)
    """
    results = []
    
    for original_source_name, normalized_name in zip(list_selected_source_subfolder, normalized_reference_dict):
        log_message(f"Processing source folder: {original_source_name}")
        
        # Step 1: Direct Folder Name Matching
        folder_match = find_folder_name_match(normalized_name, list_destination_subfolders)
        if folder_match:
            results.append((original_source_name, folder_match, 100, "Matched by folder name"))
            continue

        # Step 2: Content-Based Matching
        source_path = os.path.join(selected_source_folder, original_source_name)
        content_match = find_content_match(source_path, extensions_check, list_destination_subfolders, normalized_reference_dict)
        if content_match:
            results.append((original_source_name, content_match, 100, "Matched by content"))
            continue

        # Step 3: Fuzzy Matching
        fuzzy_match, confidence = find_fuzzy_match(normalized_name, list_destination_subfolders)
        if confidence > 0:
            results.append((original_source_name, fuzzy_match, confidence, "Matched by fuzzy matching"))
        else:
            results.append((original_source_name, "Not Found", 0, "No significant match found"))

    return results

def find_folder_name_match(normalized_name: str, destinations: List[str]) -> Optional[str]:
    """Step 1: Find direct folder name matches"""
    for destination in destinations:
        if partial_match(normalized_name, [destination]):
            log_message(f"✅ Direct folder match: '{normalized_name}' with '{destination}'")
            return destination
    return None

def find_content_match(source_path: str, extensions: List[str], destinations: List[str], normalized_dict: dict) -> Optional[str]:
    """Step 2: Find matches based on content analysis"""
    for destination in destinations:
        matched = check_files_in_subfolder(source_path, extensions, [destination], normalized_dict)
        if matched:
            log_message(f"✅ Content match in: '{source_path}' with '{destination}'")
            return destination
    return None

def find_fuzzy_match(normalized_name: str, destinations: List[str]) -> Tuple[str, int]:
    """Step 3: Find best fuzzy match using string similarity"""
    best_match = None
    best_score = 0
    
    for destination in destinations:
        cropped_names = crop_text_to_length(normalized_name, len(destination)+1)
        for cropped in cropped_names:
            score = fuzz.ratio(cropped, destination)
            if score > best_score:
                best_score = score
                best_match = destination
                
    if best_match:
        log_message(f"Fuzzy match found: '{normalized_name}' → '{best_match}' (score: {best_score})")
    
    return best_match or "Not Found", best_score
def crop_text_to_length(text: str, target_length: int) -> List[str]:
    """Crop the text into substrings of a specified length."""
    return [text[i:i + target_length] for i in range(len(text) - target_length + 1)]

def get_best_fuzzy_match(normalized_name: str, destination_names: List[str]) -> Tuple[str, int]:
    """Get the best fuzzy match for a normalized name against a list of destination names."""
    best_match = None
    best_confidence = 0

    for destination in destination_names:
        # Crop the normalized name into substrings of the same length
        cropped_names = crop_text_to_length(normalized_name, len(destination)+1)
        
        # Check similarity for each cropped substring
        for cropped in cropped_names:
            similarity = fuzz.ratio(cropped, destination)
            log_message(f"Comparing cropped '{cropped}' with '{destination}': Similarity = {similarity}")

            # Update best match if the similarity is higher than the current best
            if similarity > best_confidence:
                best_confidence = similarity
                best_match = destination

    return best_match, best_confidence