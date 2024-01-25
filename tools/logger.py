"""
Logger settings and declarations for the project
"""

# Standard library imports
import logging
import datetime
import sys


# Generate a log file name with the current timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"logs/gistemp_{timestamp}.log"

# Create a console handler and file handler to output logs to stdout and a file respectively
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(log_filename)

# Set the log level for the console handler to INFO
console_handler.setLevel(logging.INFO)

# Set the log level for the file handler to DEBUG, this allows specific messages to go to the
# log file and won't interrupt console messages
file_handler.setLevel(logging.DEBUG)

# Uncomment the below lines to set a custom format for console logging
# console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(console_formatter)

# Define a and apply formatter for the log messages
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# Get a logger instance for the current module and add the handlers
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Set the logger's level to DEBUG (lowest level, capturing all messages)
logger.setLevel(logging.DEBUG)
