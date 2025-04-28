"""
Backdrop generation service for the Storybook application.
Creates a cohesive background image for text pages.
"""
import os
import logging
import uuid
from utils.common import read_template, ensure_directory_exists, calculate_image_token_usage
from utils.cache import check_cache, save_to_cache
from services.image.service import generate_gpt_image, save_generated_image

logger = logging.getLogger(__name__)

def generate_story_backdrop(
    theme,
    child_name,
    traits,
    api_key,
    reference_image_path=None,
    quality="high",
    size="1024x1536",  # Portrait orientation (taller than wide)
    templates_folder=None,
    upload_folder=None,
    cache_folder=None,
    session_id=None
):
    """
    Generate a backdrop image for the storybook text pages.
    
    Args:
        theme: Story theme
        child_name: Name of the child
        traits: Child's traits
        api_key: OpenAI API key
        reference_image_path: Path to reference image (optional)
        quality: Image quality (low, medium, high)
        size: Image size (default "1024x1536" for portrait orientation - taller than wide)
        templates_folder: Path to templates directory
        upload_folder: Path to upload directory for saving images
        cache_folder: Path to cache directory
        session_id: Session ID for organization
        
    Returns:
        Dictionary with image path and metadata
    """
    try:
        # Create a unique identifier for the backdrop
        if not session_id:
            session_id = str(uuid.uuid4())
            
        # Create prompt for backdrop
        prompt = create_backdrop_prompt(theme, child_name, traits)
        
        # Check cache
        cache_key = f"backdrop_{theme}_{child_name}_{quality}_{size}"
        cache_result = check_cache(cache_key, cache_folder)
        
        # Return cached image if available
        if cache_result and "data" in cache_result:
            cache_data = cache_result["data"]
            image_filename = cache_data.get("filename")
            
            if image_filename:
                # Check if the image file actually exists
                image_path = os.path.join(upload_folder, image_filename)
                if os.path.exists(image_path):
                    logger.info(f"Using cached backdrop for {cache_key}")
                    return {
                        "image_path": f"/static/images/{image_filename}",
                        "from_cache": True,
                        "token_usage": cache_data.get("token_usage", {}),
                        "filename": image_filename
                    }
        
        # Create output filename
        output_filename = f"{session_id}/0_backdrop.png"
        
        # Ensure the session folder exists
        ensure_directory_exists(os.path.join(upload_folder, session_id))
        
        # Generate backdrop image
        image_data = generate_gpt_image(
            api_key=api_key,
            prompt_text=prompt,
            child_name=child_name,
            reference_image_path=reference_image_path,
            quality=quality,
            size=size,
            templates_folder=templates_folder,
            upload_folder=upload_folder
        )
        
        # Save the backdrop image
        result = save_generated_image(
            image_data=image_data,
            prompt_text=prompt,
            quality=quality,
            size=size,
            session_id=session_id,
            reference_image_path=reference_image_path,
            upload_folder=upload_folder,
            cache_folder=cache_folder,
            output_filename=output_filename
        )
        
        # Save to cache
        cache_data = {
            "filename": output_filename,
            "token_usage": result.get("token_usage", {}),
            "quality": quality,
            "size": size
        }
        save_to_cache(cache_key, cache_data, cache_folder)
        
        # Return result
        return result
        
    except Exception as e:
        logger.exception(f"Error generating backdrop: {str(e)}")
        raise Exception(f"Failed to generate backdrop: {str(e)}")

def create_backdrop_prompt(theme, child_name, traits):
    """
    Create a prompt for backdrop generation.
    
    Args:
        theme: Story theme
        child_name: Name of the child
        traits: Child's traits
        
    Returns:
        str: Prompt text
    """
    # Create an atmospheric backdrop prompt that's not too specific
    prompt = f"""
    Create a beautiful, professional-quality backdrop for a children's storybook with a {theme} theme.
    This will be used as a background for text pages in PORTRAIT ORIENTATION (taller than wide).
    
    The backdrop should have these specific qualities:
    - PORTRAIT ORIENTATION with visual elements filling the vertical space appropriately
    - Soft, dreamy quality with some gentle blurring or fog effects
    - Colors and imagery that perfectly match the {theme} theme
    - Magical, enchanting atmosphere with subtle fantasy elements
    - Even, balanced lighting that won't interfere with text readability
    - Subtle visual elements around the edges, keeping the center area clearer for text
    - Gradient effects that create depth without being distracting
    
    The story is for {child_name}, who {traits}.
    
    CRITICALLY IMPORTANT: 
    - Create ONLY a BACKGROUND IMAGE in PORTRAIT FORMAT (taller than it is wide)
    - The image MUST be taller than it is wide (portrait orientation)
    - Do NOT include any characters, animals, people, or text elements
    - Keep the center area visually simpler so text can be easily read when placed on top
    - Design specifically for a book page in portrait orientation
    - Create an image with dimensions of 1024 pixels wide by 1536 pixels tall
    """
    
    return prompt
