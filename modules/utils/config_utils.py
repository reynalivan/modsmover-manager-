import os
import json
from tkinter import messagebox
from modules.utils.logging_utils import log_message

BASE_DIR_DEFAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ConfigUtils:
    def __init__(self, base_dir=BASE_DIR_DEFAULT, config_file='config.json', dictionary_file='dictionary.json'):
        """Define the location path for the config file and dictionary file."""
        self.config_file = config_file  # Point to the root folder for config file
        self.dictionary_file = dictionary_file  # Point to the root folder for dictionary file

    def check_config(self):
        """Check if the config file exists."""
        if not os.path.isfile(self.config_file):
            log_message(f"Config file '{self.config_file}' not found")
            return False
        return True

    def load_config(self):
        """Load config from the config.json file."""
        if not self.check_config():
            return None
        try:
            with open(self.config_file, 'r') as configfile:
                config_data = json.load(configfile)

            # Validate the format of the config data
            if not self.validate_config(config_data):
                log_message(f"Config file '{self.config_file}' is invalid. Delete the file for setup new config.")
                messagebox.showerror("Invalid Config File", "The config file is invalid. Please delete the file to setup a new config.")
                os.remove(self.config_file)  # Delete the invalid config file
                return None  # Return None for invalid config

            # Return all config data
            return {
                'DESTINATION_CONFIG': {
                    'XXMI_path': config_data['DESTINATION_CONFIG']['XXMI_path'],
                },
                'DESTINATION_PATH': config_data['DESTINATION_PATH'],
                'SIMILARITY_THRESHOLD': {
                    'HIGH_CONFIDENCE': int(config_data['SIMILARITY_THRESHOLD']['HIGH_CONFIDENCE']),
                    'MEDIUM_CONFIDENCE': int(config_data['SIMILARITY_THRESHOLD']['MEDIUM_CONFIDENCE']),
                },
                'EXTENSIONS_CHECK': {
                    'extensions': ', '.join(ext.strip() for ext in config_data.get('EXTENSIONS_CHECK', {}).get('extensions', '').split(',') if ext.strip())
                }
            }
        except Exception as e:
            log_message(f"Error loading config from '{self.config_file}': {e}")
            messagebox.showerror("Failed Read Config File", "The config file is invalid. Please delete the file to setup a new config.")
            return None  # Return None for errors


    def validate_config(self, config_data):
        """Validate the format of the config data."""
        required_keys = ['DESTINATION_CONFIG', 'DESTINATION_PATH', 'SIMILARITY_THRESHOLD', 'EXTENSIONS_CHECK']
        return all(key in config_data for key in required_keys)

    def key_exists_in_destination_path(self, key):
        """Check if the specified key exists in DESTINATION_PATH."""
        try:
            # Load the current configuration
            with open(self.config_file, 'r') as configfile:
                config_data = json.load(configfile)

            # Check if DESTINATION_PATH exists
            if 'DESTINATION_PATH' in config_data:
                # Return True if the key exists, otherwise return False
                exists = key in config_data['DESTINATION_PATH']
                log_message(f"Key '{key}' exists in DESTINATION_PATH: {exists}")
                return exists
            else:
                log_message("DESTINATION_PATH not found in config.")
                return False
        except Exception as e:
            log_message(f"Error checking key in config: {e}")
            messagebox.showerror("Check Failed", "Failed to check the key in the configuration. Please try again.")
            return False


    def update_destination_path(self, key, new_path):
        """Update the specified key in the DESTINATION_PATH with a new path if the key exists."""
        try:
            # Load the current configuration
            with open(self.config_file, 'r') as configfile:
                config_data = json.load(configfile)

            # Check if DESTINATION_PATH exists
            if 'DESTINATION_PATH' in config_data:
                # Check if the specified key exists in DESTINATION_PATH
                if key in config_data['DESTINATION_PATH']:
                    # Update the specified key with the new path
                    config_data['DESTINATION_PATH'][key] = new_path

                    # Save the updated configuration
                    with open(self.config_file, 'w') as configfile:
                        json.dump(config_data, configfile, indent=4)
                    log_message(f"Updated '{key}' in DESTINATION_PATH to '{new_path}' successfully.")
                    return True
                else:
                    log_message(f"Key '{key}' not found in DESTINATION_PATH.")
                    return False
            else:
                log_message("DESTINATION_PATH not found in config.")
                return False
        except Exception as e:
            log_message(f"Error updating config: {e}")
            messagebox.showerror("Update Failed", "Failed to update the configuration. Please try again.")
            return False
    
    def add_destination_path(self, key, new_path):
        """Add a new key and path to the DESTINATION_PATH."""
        try:
            # Load the current configuration
            with open(self.config_file, 'r') as configfile:
                config_data = json.load(configfile)

            # Check if DESTINATION_PATH exists
            if 'DESTINATION_PATH' not in config_data:
                config_data['DESTINATION_PATH'] = {}

            # Add the new key and path
            config_data['DESTINATION_PATH'][key] = new_path

            # Save the updated configuration
            with open(self.config_file, 'w') as configfile:
                json.dump(config_data, configfile, indent=4)
            log_message(f"Added '{key}' to DESTINATION_PATH with path '{new_path}' successfully.")
            return True
        except Exception as e:
            log_message(f"Error adding to config: {e}")
            messagebox.showerror("Add Failed", "Failed to add the new destination path. Please try again.")
            return False

    def save_config(self, config_data):
        """Save the updated configuration to config.json."""
        try:
            # Prepare the data structure for JSON
            config_to_save = {
                'DESTINATION_CONFIG': config_data.get('DESTINATION_CONFIG', {}),
                'DESTINATION_PATH': config_data.get('DESTINATION_PATH', {}),
                'SIMILARITY_THRESHOLD': config_data.get('SIMILARITY_THRESHOLD', {}),
                'EXTENSIONS_CHECK': config_data.get('EXTENSIONS_CHECK', [])
            }

            # Write the configuration data to the JSON file
            with open(self.config_file, 'w') as configfile:
                json.dump(config_to_save, configfile, indent=4)
                log_message("Config saved successfully.")

                # Prepare a single log message for the config data
                log_message_content = "\n\n" + \
                    "==============================\n" + \
                    "Config saved successfully\n" + \
                    "Config Data: \n" + json.dumps(config_to_save, indent=4) + \
                    "\n==============================\n\n"

                log_message(log_message_content)

            return True
        except Exception as e:
            log_message(f"Error saving config: {e}")
            return False

    
    def load_dictionary(self):
        """Load mappings and dictionary from the dictionary.json file."""
        if not os.path.isfile(self.dictionary_file):
            log_message(f"Dictionary file '{self.dictionary_file}' not found. Setting default dictionary.")
            self.set_default_dictionary()
            return None  # Return None for default dictionary

        try:
            with open(self.dictionary_file, 'r') as dictionaryfile:
                dictionary_data = json.load(dictionaryfile)

            # Validate the format of the dictionary data
            if not self.validate_dictionary(dictionary_data):
                log_message(f"Dictionary file '{self.dictionary_file}' is invalid. Setting default dictionary.")
                os.remove(self.dictionary_file)  # Delete the invalid dictionary file
                self.set_default_dictionary()
                return None  # Return None for default dictionary

            # Return all dictionary data
            return {
                'ALIAS': dictionary_data['ALIAS'],
                'SETTINGS': dictionary_data['SETTINGS'],
            }
        except Exception as e:
            log_message(f"Error loading dictionary from '{self.dictionary_file}': {e}")
            self.set_default_dictionary()
            return None  # Return None for default dictionary

    def validate_dictionary(self, dictionary_data):
        """Validate the format of the dictionary data."""
        required_keys = ['ALIAS', 'SETTINGS']
        return all(key in dictionary_data for key in required_keys)


    def set_default_dictionary(self):
        """Set default values for dictionary if the dictionary.json file does not exist."""
        default_dictionary = {
            'ALIAS': {
                'Raiden': 'Raiden Shogun',
                'Shogun': 'Raiden Shogun',
                'Ei': 'Raiden Shogun',
            },
            'SETTINGS': {
                'ignore_numbers': 'true',
                'skipword': 'DISABLED, download',
            }
        }

        # Check if the dictionary file already exists
        if os.path.isfile(self.dictionary_file):
            os.remove(self.dictionary_file)

        # Write the default dictionary to the file
        with open(self.dictionary_file, 'w') as dictionaryfile:
            json.dump(default_dictionary, dictionaryfile, indent=4)
        log_message("Default dictionary created.")
    
    def save_dictionary(self, dictionary_data):
        """Save the updated dictionary to dictionary.json."""
        try:
            # Prepare the data structure for JSON
            dictionary_to_save = {
                'ALIAS': dictionary_data.get('ALIAS', {}),
                'SETTINGS': dictionary_data.get('SETTINGS', {})
            }

            # Write the dictionary data to the JSON file
            with open(self.dictionary_file, 'w') as dictionaryfile:
                json.dump(dictionary_to_save, dictionaryfile, indent=4)
            log_message("Dictionary saved successfully.")
            return True
        except Exception as e:
            log_message(f"Error saving dictionary: {e}")
            return False

# Example usage
if __name__ == "__main__":
    config_utils = ConfigUtils()
    # Load config and dictionary for demonstration
    config = config_utils.load_config()
    dictionary = config_utils.load_dictionary()
    
    # Print loaded config and dictionary for verification
    log_message("Loaded Config:")
    log_message(str(config))
    log_message("Loaded Dictionary:")
    log_message(str(dictionary))

