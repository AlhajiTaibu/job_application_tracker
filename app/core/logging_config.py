import logging
import sys

# Define the log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

def setup_logging():
    logger = logging.getLogger("job_tracker")
    logger.setLevel(logging.INFO)

    # 3. Create a StreamHandler (for terminal output)
    handler = logging.StreamHandler(sys.stdout)

    # 4. Create the formatter and add it to the handler
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)

    # 5. Add the handler to your logger
    # Check to prevent adding multiple handlers if the function is called twice
    if not logger.handlers:
        logger.addHandler(handler)

    # Optional: Prevent logs from being sent to the "root" logger (stops duplicates)
    logger.propagate = False

setup_logging()
logger = logging.getLogger("job_tracker")