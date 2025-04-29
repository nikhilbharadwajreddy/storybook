"""
Helper Utilities
--------------
Common utility functions used across the application.
"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def ensure_directories(directories: List[str]) -> None:
    """
    Ensure that all specified directories exist.
    
    Args:
        directories: List of directory paths
    """
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")

def allowed_file(filename: str) -> bool:
    """
    Check if a file has an allowed extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if file extension is allowed, False otherwise
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to make it safe for file systems.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove characters that aren't alphanumeric, underscore, or dot
    return ''.join(c for c in filename if c.isalnum() or c in ['_', '.'])

def get_file_extension(filename: str) -> Optional[str]:
    """
    Get the extension of a file.
    
    Args:
        filename: Name of the file
        
    Returns:
        Extension without the dot, or None if there is no extension
    """
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None

def generate_unique_filename(base_name: str, extension: str, directory: str) -> str:
    """
    Generate a unique filename that doesn't exist in the given directory.
    
    Args:
        base_name: Base filename
        extension: File extension
        directory: Directory to check for existing files
        
    Returns:
        Unique filename
    """
    # Sanitize the base name
    base_name = sanitize_filename(base_name)
    
    # Create initial filename
    filename = f"{base_name}.{extension}"
    path = os.path.join(directory, filename)
    
    # Check if file exists and add a counter if needed
    counter = 1
    while os.path.exists(path):
        filename = f"{base_name}_{counter}.{extension}"
        path = os.path.join(directory, filename)
        counter += 1
    
    return filename

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., '2.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            break
        size_bytes /= 1024
    
    return f"{size_bytes:.1f} {unit}"
