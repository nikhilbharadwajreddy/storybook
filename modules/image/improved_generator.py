"""
Improved Image Generator Module
-----------------------------
Simplified, direct approach to generating illustrations using OpenAI's API.
"""
import os
import io
import base64
import logging
from PIL import Image
import openai
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def generate_illustration(
    prompt: str,
    session_id: str,
    scene_index: int,
    child_name: str,
    api_key: str,
    reference_image_path: Optional[str] = None,
    quality: str = "high",
    size: str = "1024x1536",
    output_dir: str = "static/images"
) -> str:
    """
    Generate an illustration for a story scene.
    
    Args:
        prompt: Story scene description
        session_id: Session identifier
        scene_index: Index of the scene
        child_name: Name of the child
        api_key: OpenAI API key
        reference_image_path: Path to reference image (optional)
        quality: Image quality (low, medium, high)
        size: Image dimensions
        output_dir: Directory to save the image
        
    Returns:
        Path to the generated image
    """
    logger.info(f"Generating illustration for scene {scene_index}")
    
    # Enhance the prompt for better illustration
    enhanced_prompt = create_enhanced_prompt(prompt, child_name, bool(reference_image_path))
    
    # Initialize OpenAI client
    openai.api_key = api_key
    
    try:
        # Create the output filename
        filename = f"{session_id}_scene_{scene_index}_illustration.png"
        output_path = os.path.join(output_dir, filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate image based on whether reference image is provided
        if reference_image_path and os.path.exists(reference_image_path):
            # Process reference image
            ref_image = Image.open(reference_image_path).convert("RGBA")
            buf = io.BytesIO()
            ref_image.save(buf, format="PNG")
            buf.name = f"{child_name}_reference.png"  # Important for MIME type
            buf.seek(0)
            
            # Generate image with reference
            logger.info(f"Using reference image for {child_name}")
            try:
                result = openai.images.edit(
                    model="gpt-image-1",
                    image=[buf],  # Send the image buffer directly
                    prompt=enhanced_prompt,
                    size=size,
                    quality=quality
                )
            except Exception as edit_error:
                logger.warning(f"Edit API failed: {edit_error}, trying generation API")
                # Fall back to standard generation if edit fails
                result = openai.images.generate(
                    model="gpt-image-1",
                    prompt=enhanced_prompt + f" The child should resemble {child_name}.",
                    size=size,
                    quality=quality,
                    n=1
                )
        else:
            # Standard image generation without reference
            logger.info("Generating image without reference")
            result = openai.images.generate(
                model="gpt-image-1",
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                n=1
            )
        
        # Save the generated image
        if hasattr(result.data[0], 'b64_json') and result.data[0].b64_json:
            # Save from base64
            img_bytes = base64.b64decode(result.data[0].b64_json)
            with open(output_path, "wb") as f:
                f.write(img_bytes)
        elif hasattr(result.data[0], 'url') and result.data[0].url:
            # Download from URL
            import requests
            response = requests.get(result.data[0].url, timeout=30)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
            else:
                raise Exception(f"Failed to download image: {response.status_code}")
        else:
            raise Exception("No image data in response")
        
        logger.info(f"Illustration saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating illustration: {str(e)}")
        raise Exception(f"Failed to generate illustration: {str(e)}")

def create_enhanced_prompt(original_prompt: str, child_name: str, has_reference: bool = False) -> str:
    """
    Create an enhanced prompt for image generation.
    
    Args:
        original_prompt: Original story scene
        child_name: Name of the child
        has_reference: Whether a reference image is provided
        
    Returns:
        Enhanced prompt for image generation
    """
    if has_reference:
        # When we have a reference image, focus on matching the child to the reference
        return f"""
        {original_prompt}

        Make {child_name} match the reference photo's face, hair, and expression.
        Create a professional children's storybook illustration in portrait orientation.
        Use bright, rich colors, a child-friendly style, and warm lighting.
        Show the characters in action in a detailed scene with a complete background.
        """
    else:
        # Without reference, focus on creating a distinctive character
        return f"""
        {original_prompt}

        Create a professional children's storybook illustration in portrait orientation.
        Make {child_name} the main character with clear, detailed features.
        Use bright, rich colors, a child-friendly style, and warm lighting.
        Show the characters in action in a detailed scene with a complete background.
        """
