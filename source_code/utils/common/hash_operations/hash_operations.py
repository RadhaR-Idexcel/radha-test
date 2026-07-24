"""
Hash Operations Utility Module

Provides functions for generating file hashes for CloudFormation stack deployments.
"""

import hashlib
from pathlib import Path
from typing import List
from logger_config import get_logger

logger = get_logger(__name__)


def generate_file_hash(file_path: str) -> str:
    """
    Generate SHA256 hash of a file's contents.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: SHA256 hash of file contents (hexadecimal string)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        logger.debug(f"Generating hash for file: {file_path}")
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        
        hash_value = sha256_hash.hexdigest()
        logger.debug(f"Generated hash: {hash_value[:16]}...")
        return hash_value
        
    except IOError as e:
        error_msg = f"Failed to read file {file_path}: {e}"
        logger.error(error_msg)
        raise IOError(error_msg) from e


def generate_combined_hash(file_paths: List[str]) -> str:
    """
    Generate a combined SHA256 hash from multiple files.
    Files are hashed in the order provided.
    
    Args:
        file_paths: List of file paths to hash
        
    Returns:
        str: Combined SHA256 hash (hexadecimal string)
        
    Raises:
        FileNotFoundError: If any file doesn't exist
        ValueError: If file_paths is empty
    """
    if not file_paths:
        raise ValueError("file_paths cannot be empty")
    
    logger.debug(f"Generating combined hash for {len(file_paths)} files")
    
    combined_hash = hashlib.sha256()
    
    for file_path in file_paths:
        file_hash = generate_file_hash(file_path)
        combined_hash.update(file_hash.encode('utf-8'))
    
    hash_value = combined_hash.hexdigest()
    logger.debug(f"Combined hash generated: {hash_value[:16]}...")
    return hash_value


def generate_content_hash(content: str) -> str:
    """
    Generate SHA256 hash of string content.
    
    Args:
        content: String content to hash
        
    Returns:
        str: SHA256 hash of content (hexadecimal string)
    """
    logger.debug(f"Generating SHA256 hash for content ({len(content)} bytes)")
    
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content.encode('utf-8'))
    
    hash_value = sha256_hash.hexdigest()
    logger.debug(f"Generated SHA256 hash: {hash_value[:16]}...")
    return hash_value
