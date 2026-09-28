"""Security primitives shared by future services and handlers."""
from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
PRIVATE_HOSTS = {"localhost", "localhost.localdomain"}


def validate_external_url(value: str) -> str:
    """Validate a user supplied URL before handing it to a downloader."""
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ValueError("Only HTTP(S) URLs are allowed")
    host = (parsed.hostname or "").lower().rstrip(".")
    if host in PRIVATE_HOSTS:
        raise ValueError("Local hosts are not allowed")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return value
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise ValueError("Private network addresses are not allowed")
    return value
