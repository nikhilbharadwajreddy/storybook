"""
Image processing utilities for the Storybook application.
Handles image loading, processing, and saving.
"""
import os
import io
import requests
import base64
import logging
from PIL import Image

logger = logging.getLogger(__name__)

def process_reference_image(reference_image_path, child_name):
    """
    Process a reference image for use with the OpenAI API.
    Uses a clean, simple approach to ensure proper MIME type.
    
    Args:
        reference_image_path: Path to reference image
        child_name: Name of the child (for logging)
        
    Returns:
        A list containing a single buffer with the image data (OpenAI format)
    """
    if not reference_image_path or not os.path.exists(reference_image_path):
        logger.warning(f"No reference image found at {reference_image_path}")
        return None
    
    try:
        # Log that we're using a reference image
        logger.info(f"Processing reference image for {child_name} at path: {reference_image_path}")
        
        # Load the image and convert to RGBA (ensures proper format)
        img = Image.open(reference_image_path).convert("RGBA")
        
        # Create a memory buffer
        buf = io.BytesIO()
        # Save as PNG to ensure consistent format
        img.save(buf, format="PNG")
        # Important: Set name attribute to get proper MIME type (image/png)
        buf.name = f"{child_name}_reference.png"
        # Reset position to beginning of buffer
        buf.seek(0)
        
        logger.info(f"Successfully processed reference image: {buf.name}, size: {img.size}")
        return [buf]  # Return as list for OpenAI API
        
    except Exception as e:
        logger.exception(f"Error processing reference image: {str(e)}")
        return None

def save_image_from_response(image_data, output_path):
    """
    Save image data to file.
    
    Args:
        image_data: Image data from API response
        output_path: Path to save the image
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Handle different image data formats
        if 'b64_json' in image_data:
            # Base64 encoded image
            img_data = base64.b64decode(image_data['b64_json'])
            with open(output_path, 'wb') as f:
                f.write(img_data)
        elif 'url' in image_data:
            # URL to image
            response = requests.get(image_data['url'], stream=True, timeout=30)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                logger.error(f"Failed to download image: {response.status_code}")
                return False
        else:
            logger.error(f"Unsupported image data format: {image_data.keys()}")
            return False
        
        # Verify the image was saved
        if not os.path.exists(output_path):
            logger.error(f"Image file not created: {output_path}")
            return False
            
        return True
    
    except Exception as e:
        logger.exception(f"Error saving image: {str(e)}")
        return False

def extract_image_data(response):
    """
    Extract image data from API response.
    
    Args:
        response: API response object
        
    Returns:
        dict: Image data
    """
    try:
        # Handle different response formats
        if hasattr(response, 'data') and response.data:
            # OpenAI client library format
            image_data = response.data[0]
            
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                return {'b64_json': image_data.b64_json}
            elif hasattr(image_data, 'url') and image_data.url:
                return {'url': image_data.url}
        
        # Direct JSON response format
        if isinstance(response, dict):
            if 'data' in response and response['data']:
                image_data = response['data'][0]
                
                if 'b64_json' in image_data:
                    return {'b64_json': image_data['b64_json']}
                elif 'url' in image_data:
                    return {'url': image_data['url']}
        
        logger.error(f"Could not extract image data from response: {response}")
        return None
    
    except Exception as e:
        logger.exception(f"Error extracting image data: {str(e)}")
        return None
