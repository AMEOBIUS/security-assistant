# VULNERABLE:
# try:
#     process_data()
# except Exception as e:
#     return str(e)  # Exposes stack trace or internal paths

# SECURE:
import logging
logger = logging.getLogger(__name__)

try:
    process_data()
except Exception as e:
    logger.exception("Internal error occurred") # Logs full trace locally
    return "An internal error occurred. Request ID: 12345", 500
