"""
User Management Module
---------------------
Handles user login information and storage.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# File to store user data
USER_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils', 'users')
os.makedirs(USER_DATA_DIR, exist_ok=True)

def save_user_data(email: str, name: str) -> str:
    """
    Save user data to a file with timestamp.
    
    Args:
        email: User's email address
        name: User's name
        
    Returns:
        Path to the saved user data file
    """
    try:
        # Create a unique filename based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_{timestamp}.json"
        filepath = os.path.join(USER_DATA_DIR, filename)
        
        # Prepare user data
        user_data = {
            "email": email,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "ip_address": "",  # This could be populated from request.remote_addr if needed
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(user_data, f, indent=2)
            
        logger.info(f"User data saved for {email}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error saving user data: {str(e)}")
        raise

def get_all_users() -> list:
    """
    Get all registered users.
    
    Returns:
        List of user data dictionaries
    """
    users = []
    try:
        # Iterate through all user files
        for filename in os.listdir(USER_DATA_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(USER_DATA_DIR, filename)
                with open(filepath, 'r') as f:
                    user_data = json.load(f)
                    users.append(user_data)
        
        # Sort by timestamp (newest first)
        users.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return users
        
    except Exception as e:
        logger.error(f"Error retrieving user data: {str(e)}")
        return []
