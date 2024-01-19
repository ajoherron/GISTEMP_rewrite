import logging
import datetime
import sys

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"logs/gistemp_{timestamp}.log"
# log_filename = f"logs/gistemp_{timestamp}.log"


# logging.basicConfig(
#     filename=log_filename,
#     level=logging.INFO,  # Change the level as needed
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )

# stream_handler = logging.StreamHandler()
# logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# Create a module-level logger and add the file handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Change the log level as needed
logger.addHandler(file_handler)

# Configure a stream handler to print logs to stdout
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# Add the stream handler to the logger
logger.addHandler(stream_handler)