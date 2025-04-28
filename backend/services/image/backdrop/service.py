"""
Backdrop image generation service for storybook.
Handles generating a single backdrop image for the entire storybook.
"""
import os
import json
import hashlib
import logging
from datetime import datetime
from services.image.service import create_image_with_openai
from utils.cache import get_cached_response, cache_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_backdrop_image(
    backdrop_description,
    session_id,
    api_key,
    child_name="the child",
    reference_image_path=None,
    quality="high",
    size="1536x1024",  # Landscape for backdrop
    templates_folder=None,
    upload_folder=None,
    cache_folder=None
):
    """
    Generate a single backdrop image for the entire storybook.
    
    Args:
        backdrop_description (str): Description of the backdrop to generate
        session_id (str): Unique session identifier
        api_key (str): OpenAI API key
        child_name (str): Name of the child
        reference_image_path (str): Path to reference image if available
        quality (str): Image quality setting (low, medium, high)
        size (str): Image size (for landscape orientation)
        templates_folder (str): Path to templates directory
        upload_folder (str): Path to upload directory
        cache_folder (str): Path to cache directory
        
    Returns:
        dict: Dictionary containing image path and token usage information
    """
    try:
        # Create a unique hash for the backdrop request
        request_hash = hashlib.md5(
            f"{child_name}_{backdrop_description}_{size}_{quality}".encode()
        ).hexdigest()
        
        # Check cache first
        cached_response = get_cached_response(request_hash, cache_folder)
        if cached_response:
            logger.info(f"Using cached backdrop image for session {session_id}")
            return {
                "image_path": cached_response["image_path"],
                "token_usage": cached_response["token_usage"],
                "from_cache": True
            }
        
        # No cache hit, generate the image
        logger.info(f"Generating backdrop image for session {session_id}")
        
        # Generate a unique filename for the backdrop image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_filename = f"backdrop_{session_id}_{timestamp}.png"
        image_path = os.path.join(upload_folder, image_filename)
        
        # For now, we'll just use the existing create_image_with_openai function
        # In the future, we might want to customize this for backdrops
        result = create_image_with_openai(
            prompt=backdrop_description,
            api_key=api_key,
            size=size,
            quality=quality,
            output_path=image_path,
            model="gpt-image-1"  # Use GPT Image for best quality backgrounds
        )
        
        # Prepare response
        response = {
            "image_path": f"/static/images/{image_filename}",  # Web path
            "token_usage": {
                "model": "gpt-image-1",
                "size": size,
                "quality": quality
            },
            "from_cache": False
        }
        
        # Cache the response
        cache_response(request_hash, response, cache_folder)
        
        return response
    
    except Exception as e:
        logger.exception(f"Error generating backdrop image: {str(e)}")
        raise
