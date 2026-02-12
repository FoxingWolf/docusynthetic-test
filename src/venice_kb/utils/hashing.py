"""Content fingerprinting using hashing."""

import hashlib


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content for fingerprinting.

    Args:
        content: String content to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()
