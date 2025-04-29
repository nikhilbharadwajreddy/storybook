"""
Background Image Generator Module
-------------------------------
Generates themed background images for text pages.
"""
import os
import logging
import requests
import uuid
import base64
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def generate_background(
    theme: str,
    child_name: str,
    api_key: str,
    output_dir: str,
    session_id: str,
    quality: str = "medium",  # Medium quality is sufficient for backgrounds
    size: str = "1024x1536",  # Match portrait orientation of illustrations
    model: str = "gpt-image-1"
) -> str:
    """
    Generate a themed background image for text pages.
    
    Args:
        theme: Story theme
        child_name: Name of the child
        api_key: OpenAI API key
        output_dir: Directory to save the image
        session_id: Session identifier
        quality: Image quality
        size: Image dimensions
        model: Image model to use
        
    Returns:
        Path to the generated background image
    """
    logger.info(f"Generating background image for theme: {theme}")
    
    # Create background prompt
    prompt = create_background_prompt(theme, child_name)
    
    try:
        # Call OpenAI API
        image_data = generate_background_image(api_key, prompt, quality, size, model)
        
        # Save the image
        filename = f"{session_id}_background.png"
        image_path = os.path.join(output_dir, filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        # Save image based on the type of data received
        if "b64_json" in image_data:
            # Save from base64
            img_data = base64.b64decode(image_data["b64_json"])
            with open(image_path, "wb") as f:
                f.write(img_data)
                
        elif "url" in image_data:
            # Download from URL
            response = requests.get(image_data["url"], timeout=30)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
            else:
                raise Exception(f"Failed to download image: {response.status_code}")
        else:
            raise Exception(f"Unsupported image data format: {image_data.keys()}")
        
        logger.info(f"Background image saved to {image_path}")
        return image_path
        
    except Exception as e:
        logger.error(f"Error generating background: {str(e)}")
        # If background generation fails, return a placeholder path
        # In a real app, you might want to have a default background image
        return os.path.join(output_dir, "default_background.png")

def create_background_prompt(theme: str, child_name: str) -> str:
    """
    Create a prompt for generating a background image.
    
    Args:
        theme: Story theme
        child_name: Name of the child
        
    Returns:
        Formatted prompt string
    """
    return f"""
    Create a subtle, magical background pattern for a children's storybook with a {theme} theme.
    
    This background will be used for text pages in a storybook for {child_name}.
    
    The background should be:
    - In PORTRAIT ORIENTATION (taller than wide, 1024x1536 pixels)
    - Very light and subtle (text will be overlaid on top)
    - Have soft, pastel colors related to the {theme} theme
    - Include gentle, non-distracting patterns or elements that suggest the {theme}
    - Be appropriate for a children's storybook
    - Have a dreamy, magical quality
    - Be somewhat abstract or minimalist
    - Not have any text
    - Not include any characters or prominent figures
    - Be seamless and consistent across the entire image
    
    The background must be very light so that dark text can be easily read when overlaid on top of it.
    """

def generate_background_image(
    api_key: str, 
    prompt: str, 
    quality: str = "medium",
    size: str = "1024x1536",
    model: str = "gpt-image-1"
) -> Dict[str, str]:
    """
    Generate a background image using OpenAI's API.
    
    Args:
        api_key: OpenAI API key
        prompt: Background prompt
        quality: Image quality
        size: Image dimensions
        model: Image model to use
        
    Returns:
        Dictionary with image data (URL or base64)
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "prompt": prompt,
        "quality": quality,
        "size": size,
        "n": 1
    }
    
    logger.info(f"Calling OpenAI API for background with prompt: {prompt[:50]}...")
    
    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers=headers,
        json=data,
        timeout=60
    )
    
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")
    
    result = response.json()
    if "data" in result and len(result["data"]) > 0:
        return result["data"][0]
    else:
        raise Exception("No image data in response")
