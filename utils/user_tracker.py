"""
User Tracker Module
------------------
Simple module to track users who access the storybook generator.
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Path to the users data file
USERS_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'user_data.json')

def save_user_data(name: str, email: str) -> bool:
    """
    Save user information to the JSON file.
    
    Args:
        name: User's name
        email: User's email
        
    Returns:
        True if successfully saved, False otherwise
    """
    try:
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        # Prepare new user entry
        user_entry = {
            "name": name,
            "email": email,
            "timestamp": timestamp
        }
        
        # Load existing data or create new structure
        if os.path.exists(USERS_DATA_FILE):
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                try:
                    users_data = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("User data file corrupted, creating new one")
                    users_data = {"users": []}
        else:
            users_data = {"users": []}
        
        # Add new user to the list
        users_data["users"].append(user_entry)
        
        # Save the updated data
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2)
        
        logger.info(f"User data saved for {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving user data: {str(e)}")
        return False

def get_all_users() -> List[Dict]:
    """
    Get all users who have accessed the application.
    
    Returns:
        List of user data dictionaries
    """
    if not os.path.exists(USERS_DATA_FILE):
        return []
    
    try:
        with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
            return users_data.get("users", [])
    except Exception as e:
        logger.error(f"Error reading user data: {str(e)}")
        return []
