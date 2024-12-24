import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Custom formatter to format log messages with a specific format."""
    
    def format(self, record):
        # Format timestamp and level
        timestamp = self.formatTime(record, self.datefmt)
        level = record.levelname
        header = f"{timestamp} - {level} ↴"
        
        # Format message
        message = record.getMessage()
        
        # Split message into lines and indent each line
        if isinstance(message, str):
            message_lines = message.split('\n')
            formatted_message = '\n'.join([header] + ['    ' + line for line in message_lines])
        else:
            formatted_message = f"{header}\n    {message}"
        
        return formatted_message

def log_message(message, level=logging.INFO):
    # Convert message to ASCII using unidecode
    # message = unidecode(message)
    
    # Define log directory
    log_directory = 'logs'
    
    # Create log directory if it doesn't exist
    os.makedirs(log_directory, exist_ok=True)
    
    # Define log format and date format
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'  # Format waktu tanpa milidetik
    
    # Create handler for rotating log files
    log_filename = f"log-{datetime.now().strftime('%Y%m%d')}.log"  # Daily log file
    log_file_path = os.path.join(log_directory, log_filename)
    
    # Set up logger
    logger = logging.getLogger()
    if not logger.hasHandlers():  # Check if handlers already exist
        logger.setLevel(logging.DEBUG)  # Set level to DEBUG to capture all log levels
        
        # Create custom formatter
        formatter = CustomFormatter(log_format, datefmt=date_format)
        
        # Set up file handler with custom formatter
        file_handler = TimedRotatingFileHandler(
            log_file_path, 
            when='midnight', 
            interval=1, 
            backupCount=7,  # Keep only the last 7 log files
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Set up console handler with custom formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Log initialization message
        logger.info("Logger initialized and handler added.")
        
        # Log the path of the log file
        logger.info(f"Log file created at: {log_file_path}")

    # Log message at the specified level
    if level == logging.DEBUG:
        logger.debug(message)
    elif level == logging.INFO:
        logger.info(message)
    elif level == logging.WARNING:
        logger.warning(message)
    elif level == logging.ERROR:
        logger.error(message)
    elif level == logging.CRITICAL:
        logger.critical(message)

# Example usage
if __name__ == "__main__":
    # Log various messages with different levels
    log_message("This is an info message.")
    log_message("This is a debug message.", level=logging.DEBUG)
    log_message("This is a warning message.", level=logging.WARNING)
    log_message("This is an error message.", level=logging.ERROR)
    log_message("This is a critical message.", level=logging.CRITICAL)
    