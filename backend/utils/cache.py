"""
Caching utilities for the Storybook application.
Handles caching of prompts, images, and other data to reduce API costs.
"""
import os
import json
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_cache_key(text, params=None):
    """
    Generate a cache key based on input text and optional parameters.
    
    Args:
        text: Input text to hash
        params: Optional parameters to include in the hash
    
    Returns:
        str: MD5 hash to use as cache key
    """
    # Create a string combining text and params
    cache_str = text
    if params:
        if isinstance(params, dict):
            for key in sorted(params.keys()):
                cache_str += f"|{key}:{params[key]}"
        else:
            cache_str += f"|{params}"
    
    # Generate MD5 hash
    cache_key = hashlib.md5(cache_str.encode('utf-8')).hexdigest()
    return cache_key

def check_cache(key, cache_folder, max_age_days=30):
    """
    Check if a cache entry exists and is not expired.
    
    Args:
        key: Cache key
        cache_folder: Path to cache directory
        max_age_days: Maximum age of cache entry in days
        
    Returns:
        dict: Cache data if exists and valid, None otherwise
    """
    try:
        cache_key = generate_cache_key(key)
        cache_file = os.path.join(cache_folder, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        # Check cache age
        file_age_days = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))).days
        if file_age_days > max_age_days:
            logger.info(f"Cache expired for key: {cache_key}")
            return None
        
        # Read cache file
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        return cache_data
    
    except Exception as e:
        logger.exception(f"Error checking cache: {str(e)}")
        return None

def save_to_cache(key, data, cache_folder):
    """
    Save data to cache.
    
    Args:
        key: Cache key
        data: Data to cache (must be JSON serializable)
        cache_folder: Path to cache directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create cache folder if it doesn't exist
        os.makedirs(cache_folder, exist_ok=True)
        
        # Generate cache key
        cache_key = generate_cache_key(key)
        cache_file = os.path.join(cache_folder, f"{cache_key}.json")
        
        # Add timestamp
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Save to file
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.info(f"Saved to cache: {cache_key}")
        return True
    
    except Exception as e:
        logger.exception(f"Error saving to cache: {str(e)}")
        return False

def check_image_cache(prompt_text, quality, size, cache_folder, static_folder):
    """
    Check if an image exists in the cache.
    
    Args:
        prompt_text: Text used to generate the image
        quality: Image quality setting
        size: Image size
        cache_folder: Path to cache directory
        static_folder: Path to static directory (for images)
        
    Returns:
        tuple: (cache_file, image_filename, cache_data) or (None, None, None)
    """
    try:
        # Generate cache key
        params = {"quality": quality, "size": size}
        cache_key = generate_cache_key(prompt_text, params)
        cache_file = os.path.join(cache_folder, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None, None, None
        
        # Read cache file
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Get image filename
        image_filename = cache_data.get("data", {}).get("filename")
        if not image_filename:
            return None, None, None
        
        # Check if image file exists
        image_path = os.path.join(static_folder, image_filename)
        if not os.path.exists(image_path):
            logger.warning(f"Image referenced in cache not found: {image_path}")
            return None, None, None
        
        return cache_file, image_filename, cache_data.get("data", {})
    
    except Exception as e:
        logger.exception(f"Error checking image cache: {str(e)}")
        return None, None, None

def clear_cache(cache_folder, max_age_days=30):
    """
    Clear expired cache entries.
    
    Args:
        cache_folder: Path to cache directory
        max_age_days: Maximum age of cache entry in days
        
    Returns:
        int: Number of entries cleared
    """
    try:
        if not os.path.exists(cache_folder):
            return 0
        
        cleared_count = 0
        current_time = datetime.now()
        
        for filename in os.listdir(cache_folder):
            if not filename.endswith('.json'):
                continue
            
            file_path = os.path.join(cache_folder, filename)
            file_age_days = (current_time - datetime.fromtimestamp(os.path.getmtime(file_path))).days
            
            if file_age_days > max_age_days:
                os.remove(file_path)
                cleared_count += 1
        
        logger.info(f"Cleared {cleared_count} expired cache entries")
        return cleared_count
    
    except Exception as e:
        logger.exception(f"Error clearing cache: {str(e)}")
        return 0
