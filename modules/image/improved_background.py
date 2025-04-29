"""
Improved Background Generator Module
---------------------------------
Simplified approach to generating background images.
"""
import os
import base64
import logging
import openai
import requests
from typing import Optional

logger = logging.getLogger(__name__)

def generate_background(
    theme: str,
    child_name: str,
    api_key: str,
    output_dir: str,
    session_id: str,
    quality: str = "medium",
    size: str = "1024x1536"
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
        
    Returns:
        Path to the generated background image
    """
    logger.info(f"Generating background image for theme: {theme}")
    
    # Create background prompt
    prompt = create_background_prompt(theme, child_name)
    
    try:
        # Initialize OpenAI client
        openai.api_key = api_key
        
        # Generate background image
        result = openai.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1
        )
        
        # Save the image
        filename = f"{session_id}_background.png"
        image_path = os.path.join(output_dir, filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        # Save based on response type
        if hasattr(result.data[0], 'b64_json') and result.data[0].b64_json:
            # Save from base64
            img_bytes = base64.b64decode(result.data[0].b64_json)
            with open(image_path, "wb") as f:
                f.write(img_bytes)
        elif hasattr(result.data[0], 'url') and result.data[0].url:
            # Download from URL
            response = requests.get(result.data[0].url, timeout=30)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
            else:
                raise Exception(f"Failed to download image: {response.status_code}")
        else:
            raise Exception("No image data in response")
        
        logger.info(f"Background image saved to {image_path}")
        return image_path
        
    except Exception as e:
        logger.error(f"Error generating background: {str(e)}")
        # Use a default or placeholder background in case of failure
        default_path = os.path.join(output_dir, "default_background.png")
        return default_path

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
