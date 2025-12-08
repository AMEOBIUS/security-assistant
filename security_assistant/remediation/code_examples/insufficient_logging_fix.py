# VULNERABLE:
# try:
#     login(user)
# except AuthError:
#     pass # Silencing error

# SECURE:
import logging

logger = logging.getLogger("security")

try:
    login(user)
except AuthError:
    # Log the event with context
    logger.warning(
        "Failed login attempt for user: %s from IP: %s",
        user.username,
        request.remote_addr,
    )
    raise
