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
    
    # Get all list folder name and path in source_folders_list create variable source_folders_list_name and source_folders_list_path
    source_folders_list_name = [name for name, path in source_folders_list]
    source_folders_list_path = [path for name, path in source_folders_list]
    
    if not source_folders_list_path:
        log_message(f"Source folder '{selected_source_folder}' is empty or not found.")
        return {}
    
    # Get all subfolders in the destination directory
    destination_folder_subfolder_list = list_folders_in_directory(destination_folder)
    if not destination_folder_subfolder_list:
        log_message(f"Destination folder '{destination_folder}' is empty or not found.")
        return {}

    log_message(f"Found {len(source_folders_list_path)} source subfolders and {len(destination_folder_subfolder_list)} destination subfolders.")
    
    # Match folders and categorize results
    mapping_data = get_matching_weight(
            source_folders_list_path, # get list of source folders 
            destination_folder_subfolder_list,
            skipworld_list,
            ignore_numbers_status,
            alias_data,
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
    source_folders_list_path: List[str],
    destination_folder_subfolder_list: List[str],
    skipworld_list: List[str],
    ignore_numbers_status: bool,
    alias_data: Dict[str, str],
    extensions_check: List[str]
) -> List[Tuple[str, str, int, str]]:
    """
    Three-step matching process between source and destination folders.
    Returns list of tuples: (source_path, destination, confidence, reason)
    """
    results = []
    
    # Loop through each source folder path
    for source_folder_path in source_folders_list_path:
        source_folder_name = os.path.basename(source_folder_path)
        log_message(f"Processing source folder: {source_folder_path}")
        
        # if name is too short, direct to step 2
        min_destination_length = min(len(dest) for dest in destination_folder_subfolder_list)
        if len(source_folder_name) >= min_destination_length:
            # Step 1: Direct Folder Name Matching   
            folder_match = find_folder_name_match(source_folder_path, destination_folder_subfolder_list, skipworld_list, ignore_numbers_status, alias_data)
            if folder_match:
                results.append((source_folder_path, folder_match, 100, "Direct folder match"))
                continue

        # Step 2: Content-Based Matching (only if Step 1 failed)
        content_match = find_content_match(source_folder_path, destination_folder_subfolder_list, skipworld_list, ignore_numbers_status, extensions_check, alias_data)
        if content_match:
            results.append((source_folder_path, content_match, 95, "Content match"))
            continue

        # Step 3: Fuzzy Matching (only if Step 1 and 2 failed)
        fuzzy_match, confidence = find_fuzzy_match(source_folder_path, destination_folder_subfolder_list, skipworld_list, ignore_numbers_status, alias_data)
        if confidence > 0:
            results.append((source_folder_path, fuzzy_match, confidence, "Fuzzy match"))
        else:
            results.append((source_folder_path, "Not Found", 0, "No match"))

    return results

def find_folder_name_match(source_folder_path: str, destination_folder_subfolder_list: List[str], skipworld_list, ignore_numbers_status, alias_data) -> Optional[str]:
    """Step 1: Find direct folder name matches"""
    
    # Normalize source folder names
    normalized_map = normalize_folders(source_folder_path, skipworld_list, ignore_numbers_status)
    log_message(f"Normalizing source folders: {normalized_map}")
    
    # Apply aliases to normalized names
    path_to_name_map = apply_aliases(normalized_map, alias_data)
    log_message(f"Applying aliases: {path_to_name_map}")

    original_source_name, normalized_name = path_to_name_map.get(source_folder_path, (None, None))
    
    for destination in destination_folder_subfolder_list:
        if partial_match(normalized_name, [destination]):
            log_message(f" Direct folder match: '{normalized_name}' with '{destination}'")
            return destination
    return None
        

def find_content_match(source_folder_path: str, destination_folder_subfolder_list: List[str], skipworld_list: List[str], ignore_numbers_status: bool, extensions_check: List[str], alias_data: Dict[str, str]):
    """Find matches based on folder content analysis"""
    for destination_folder_subfolder in destination_folder_subfolder_list:
        # Try folder name matching first
        matched_folder = find_folder_name_in_subfolders(
            source_folder_path, 
            destination_folder_subfolder,
            skipworld_list,
            ignore_numbers_status,
            alias_data
        )
        if matched_folder:
            return destination_folder_subfolder

        # Try file matching if folder match fails
        matched_file = find_file_in_subfolders(
            source_folder_path,
            destination_folder_subfolder, 
            skipworld_list,
            ignore_numbers_status,
            extensions_check,
            alias_data
        )
        if matched_file:
            return destination_folder_subfolder

    return None

def find_folder_name_in_subfolders(source_path: str, destination_name: str, skipworld_list: List[str], ignore_numbers: bool, alias_data: Dict[str, str]) -> Optional[str]:
    """Check subfolder names up to 5 levels deep"""

    for root, dirs, _ in os.walk(source_path):
        depth = root[len(source_path):].count(os.sep)
        if depth > 5:
            continue
            
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            
            # First try exact folder name match
            if dir_name.lower() == destination_name.lower():
                log_message(f" Exact folder match found: '{dir_name}' at depth {depth}")
                return dir_path
            
            # Then try normalized matching
            normalized_map = normalize_folders(dir_path, skipworld_list, ignore_numbers)
            path_to_name_map = apply_aliases(normalized_map, alias_data)
            
            for _, (original_name, normalized_name) in path_to_name_map.items():
                # Check for exact normalized match first
                if normalized_name.lower() == destination_name.lower():
                    log_message(f" Exact normalized match found: '{dir_name}' → '{destination_name}' at depth {depth}")
                    return dir_path
                    
                # Then try partial matching
                if partial_match(normalized_name, [destination_name]):
                    log_message(f" Partial match found: '{dir_name}' → '{destination_name}' at depth {depth}")
                    return dir_path
                    
    log_message(f"No folder matches found in: '{source_path}'")
    return None

def find_file_in_subfolders(source_path: str, destination_name: str, skipworld_list: List[str], ignore_numbers: bool, extensions_check: List[str], alias_data: Dict[str, str]) -> Optional[str]:
    """Check files with specific extensions up to 5 levels deep"""
    if not extensions_check:
        log_message("Skipping file check - no extensions specified")
        return None
        
    log_message(f"Checking files in '{source_path}' for matches with '{destination_name}'")
    log_message(f"Looking for extensions: {extensions_check}")
    
    # Parse extensions string to list
    extensions_list = [ext.strip() for ext in extensions_check.get('extensions', '').split(',')]
    extensions_set = set(extensions_list)
    
    # Walk through all subdirectories
    for root, _, files in os.walk(source_path):
        depth = root[len(source_path):].count(os.sep)
        if depth > 5:
            continue
            
        for file_name in files:
            if any(file_name.endswith(ext.strip()) for ext in extensions_set):
                file_path = os.path.join(root, file_name)
                
                # First check if character name exists in file name
                base_name = os.path.splitext(file_name)[0]
                if destination_name.lower() in base_name.lower():
                    log_message(f" Direct character name match in file: '{file_name}' → '{destination_name}'")
                    return file_path
                
                # Then try normalized matching
                normalized_map = normalize_folders(file_path, skipworld_list, ignore_numbers)
                path_to_name_map = apply_aliases(normalized_map, alias_data)
                
                for _, (original_name, normalized_name) in path_to_name_map.items():
                    if partial_match(normalized_name, [destination_name]):
                        log_message(f" File match found: '{file_name}' → '{destination_name}' at depth {depth}")
                        return file_path
    
    log_message(f" No file matches found in: '{source_path}'")
    return None

def find_fuzzy_match(source_folder_path: str, destination_folder_subfolder_list: List[str], skipworld_list, ignore_numbers_status, alias_data):
    """Step 3: Find best fuzzy match using string similarity"""
    
    # Normalize source folder names
    normalized_map = normalize_folders(source_folder_path, skipworld_list, ignore_numbers_status)
    log_message(f"Normalizing source folders: {normalized_map}")
    
    # Apply aliases to normalized names
    path_to_name_map = apply_aliases(normalized_map, alias_data)
    log_message(f"Applying aliases: {path_to_name_map}")

    original_source_name, normalized_name = path_to_name_map.get(source_folder_path, (None, None))
    
    best_match = None
    best_score = 0
    
    for destination in destination_folder_subfolder_list:
        cropped_names = crop_text_to_length(normalized_name, len(destination)+1)
        for cropped in cropped_names:
            score = fuzz.ratio(cropped, destination)
            if score > best_score:
                best_score = score
                best_match = destination
                
    if best_match:
        log_message(f"Fuzzy match found: '{normalized_name}' → '{best_match}' (score: {best_score})")
    
    return best_match or "Not Found", best_score


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

def crop_text_to_length(text: str, target_length: int) -> List[str]:
    """Crop the text into substrings of a specified length."""
    return [text[i:i + target_length] for i in range(len(text) - target_length + 1)]


def normalize_folders(source_folder_path: str, skipworld_list: List[str], ignore_numbers: bool) -> Dict[str, Tuple[str, str]]:
    """Normalize folder names by handling non-Latin chars, numbers and formatting."""
    source_folder_name = os.path.basename(source_folder_path)
    
    # Handle non-Latin characters
    normalized_name = unidecode(source_folder_name).lower().strip()
    
    # Remove skip words
    for skip_word in skipworld_list:
        normalized_name = normalized_name.replace(skip_word.lower(), '')
    
    # Handle numbers
    if ignore_numbers and not normalized_name.isdigit():
        normalized_name = ''.join(char for char in normalized_name if not char.isdigit())
    
    # Clean up formatting
    normalized_name = normalized_name.replace("_", " ").replace("-", " ")
    normalized_name = " ".join(normalized_name.split())  # Handle multiple spaces
    normalized_name = normalized_name.title()
    
    return {source_folder_path: (source_folder_name, normalized_name)}

def apply_aliases(normalized_map: Dict[str, Tuple[str, str]], alias_data: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    """Apply aliases to normalized folder names and return a mapping of full paths to normalized names and their aliases."""
    if not alias_data:
        log_message("No alias data provided.")
        return normalized_map

    updated_map = {}
    for full_path, (original_name, normalized_name) in normalized_map.items():
        alias_found = False
        for alias_key, alias_value in alias_data.items():
            if alias_key.lower() in normalized_name.lower():
                log_message(f"Alias found for {original_name} is {alias_value}!")
                updated_map[full_path] = (original_name, alias_value)
                alias_found = True
                break  # Stop checking once an alias is found
        if not alias_found:
            updated_map[full_path] = (original_name, normalized_name)

    return updated_map


def partial_match(source_name: str, destination_names: List[str]) -> bool:
    """Check if the source name partially matches any of the destination names."""
    # Normalize the source name by removing spaces and converting to lowercase
    normalized_source = source_name.replace(" ", "").lower()
    for destination in destination_names:
        normalized_destination = destination.replace(" ", "").lower()
        # Only match if source length is greater than or equal to destination length
        if len(normalized_source) >= len(normalized_destination):
            if normalized_source in normalized_destination or normalized_destination in normalized_source:
                return True
    return False