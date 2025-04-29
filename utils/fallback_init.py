"""
Fallback Initialization Module
----------------------------
Creates any missing but required directories and initializes necessary files.
"""
import os
import logging
import shutil
import requests
from PIL import ImageFont

logger = logging.getLogger(__name__)

def ensure_required_directories():
    """
    Ensure all required directories exist, creating them if not.
    """
    required_dirs = [
        'static/images',
        'static/pdfs',
        'static/references',
        'static/fonts'
    ]
    
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for dir_path in required_dirs:
        full_path = os.path.join(current_dir, dir_path)
        if not os.path.exists(full_path):
            logger.info(f"Creating required directory: {full_path}")
            os.makedirs(full_path, exist_ok=True)

def ensure_default_font():
    """
    Ensure there's at least one usable font file in the static/fonts directory.
    If none exists, download a free font.
    """
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(current_dir, 'static', 'fonts')
    
    # Make sure directory exists
    os.makedirs(fonts_dir, exist_ok=True)
    
    # Look for any .ttf files
    font_files = [f for f in os.listdir(fonts_dir) if f.lower().endswith('.ttf')]
    
    if not font_files:
        # No fonts found, try to download one
        logger.info("No font files found. Attempting to download a default font.")
        try:
            # Source: Google Fonts - Open Sans (Apache License 2.0)
            font_url = "https://github.com/google/fonts/raw/main/apache/opensans/OpenSans%5Bwdth%2Cwght%5D.ttf"
            font_path = os.path.join(fonts_dir, "OpenSans.ttf")
            
            response = requests.get(font_url, timeout=10)
            if response.status_code == 200:
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Downloaded default font to {font_path}")
            else:
                logger.warning(f"Failed to download font: {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading font: {str(e)}")

def initialize_all():
    """Initialize all required resources."""
    try:
        logger.info("Ensuring required directories exist...")
        ensure_required_directories()
        
        logger.info("Checking for default font...")
        ensure_default_font()
        
        logger.info("Initialization complete.")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
