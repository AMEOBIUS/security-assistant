# VULNERABLE:
# import requests
# url = request.args.get('url')
# requests.get(url)  # Can hit http://localhost:8080/admin

# SECURE:
import ipaddress
import socket
from urllib.parse import urlparse


def validate_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid scheme")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid hostname")

    # Resolve hostname to IP
    ip = socket.gethostbyname(hostname)
    ip_obj = ipaddress.ip_address(ip)

    # Check if IP is private
    if ip_obj.is_private or ip_obj.is_loopback:
        raise ValueError("Access to internal resources is forbidden")

    return url


# requests.get(validate_url(user_input_url))
