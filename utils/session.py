"""
Session Management Utility
-----------------------
Handles session data storage and retrieval.
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Simple in-memory session storage
_SESSION_DATA = {}

# Define the session data file path
SESSION_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session_data.json")

def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get data for a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session data dict or None if not found
    """
    # Try in-memory first
    if session_id in _SESSION_DATA:
        return _SESSION_DATA[session_id]
    
    # Try reading from file
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                all_sessions = json.load(f)
                return all_sessions.get(session_id)
    except Exception as e:
        logger.error(f"Error reading session file: {str(e)}")
    
    return None

def save_session_data(session_id: str, data: Dict[str, Any]) -> None:
    """
    Save data for a session.
    
    Args:
        session_id: Session identifier
        data: Session data to save
    """
    # Save in memory
    _SESSION_DATA[session_id] = data
    
    # Also persist to file
    try:
        # Read existing data
        all_sessions = {}
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                try:
                    all_sessions = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Corrupted session file, creating new")
        
        # Add new session data
        all_sessions[session_id] = data
        
        # Write back to file
        with open(SESSION_FILE, 'w') as f:
            json.dump(all_sessions, f, indent=2)
            
        logger.info(f"Session {session_id} saved")
    except Exception as e:
        logger.error(f"Error saving session: {str(e)}")

def get_all_sessions() -> Dict[str, Dict[str, Any]]:
    """
    Get all session data.
    
    Returns:
        Dictionary of all sessions
    """
    # Combine in-memory and file data
    all_sessions = {}
    
    # Get from file first
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                all_sessions.update(json.load(f))
    except Exception as e:
        logger.error(f"Error reading all sessions: {str(e)}")
    
    # Update with in-memory data (which is more recent)
    all_sessions.update(_SESSION_DATA)
    
    return all_sessions

def cleanup_old_sessions(max_age_days: int = 7) -> int:
    """
    Remove sessions older than specified age.
    
    Args:
        max_age_days: Maximum age in days
        
    Returns:
        Number of sessions cleaned up
    """
    count = 0
    current_time = datetime.now()
    
    # Get all sessions
    all_sessions = get_all_sessions()
    sessions_to_keep = {}
    
    for session_id, data in all_sessions.items():
        try:
            # Parse created_at timestamp
            created_at = datetime.fromisoformat(data.get('created_at', '2000-01-01'))
            
            # Calculate age in days
            age_days = (current_time - created_at).days
            
            if age_days <= max_age_days:
                sessions_to_keep[session_id] = data
            else:
                count += 1
                # Remove from in-memory storage
                if session_id in _SESSION_DATA:
                    del _SESSION_DATA[session_id]
        except Exception as e:
            logger.warning(f"Error parsing session date: {str(e)}")
            # Keep the session if there's an error
            sessions_to_keep[session_id] = data
    
    # Save updated sessions to file
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(sessions_to_keep, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving cleaned sessions: {str(e)}")
    
    logger.info(f"Cleaned up {count} old sessions")
    return count
