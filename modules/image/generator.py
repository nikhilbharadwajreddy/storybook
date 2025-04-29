"""
Image Generator Module
--------------------
Handles the generation of illustrations for story scenes using OpenAI's image API.
"""
import os
import logging
import requests
import uuid
import io
import base64
from PIL import Image
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def generate_illustration(
    prompt: str,
    session_id: str,
    scene_index: int,
    child_name: str,
    api_key: str,
    reference_image_path: Optional[str] = None,
    model: str = "gpt-image-1",
    quality: str = "high",
    size: str = "1024x1536",  # Portrait orientation for storybooks
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
        model: Image model to use
        quality: Image quality (low, medium, high)
        size: Image dimensions
        output_dir: Directory to save the image
        
    Returns:
        Path to the generated image
    """
    logger.info(f"Generating illustration for scene {scene_index}")
    
    # Create enhanced prompt for better illustration
    enhanced_prompt = create_enhanced_prompt(prompt, child_name, bool(reference_image_path))
    
    # Process reference image if provided
    reference_image = process_reference_image(reference_image_path) if reference_image_path else None
    
    # Generate image
    try:
        if reference_image:
            # Generate image with reference
            logger.info(f"Using reference image for {child_name}")
            image_data = generate_image_with_reference(
                api_key=api_key, 
                prompt=enhanced_prompt, 
                reference_image=reference_image, 
                quality=quality, 
                size=size,
                model=model
            )
        else:
            # Generate image without reference
            image_data = generate_image_standard(
                api_key=api_key, 
                prompt=enhanced_prompt, 
                quality=quality, 
                size=size,
                model=model
            )
        
        # Save image
        filename = f"{session_id}_scene_{scene_index}_illustration.png"
        image_path = os.path.join(output_dir, filename)
        
        save_image(image_data, image_path)
        logger.info(f"Illustration saved to {image_path}")
        
        return image_path
        
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
    base_prompt = f"""
    Create a professional-quality children's book illustration in PORTRAIT ORIENTATION depicting this exact scene:
    {original_prompt}
    
    This must be a PREMIUM-QUALITY, FULL SCENE ILLUSTRATION with:
    - PORTRAIT ORIENTATION (taller than wide, 1024x1536 pixels)
    - Make {child_name} the main character with clear, detailed features
    - Show the exact action described in the prompt
    - Use bright, saturated colors with strong contrast
    - Include a detailed background environment
    - Create a whimsical, magical feeling
    - Use a cartoon art style similar to modern Disney/Pixar animation
    """
    
    if has_reference:
        reference_addition = f"""
        IMPORTANT: I have uploaded a reference image showing what {child_name} looks like.
        You MUST make the child look EXACTLY like the uploaded reference image.
        Match the same face, hair, skin tone, and general appearance from the reference.
        """
        base_prompt += reference_addition
    
    return base_prompt

def process_reference_image(reference_image_path: str) -> io.BytesIO:
    """
    Process a reference image for use with the OpenAI API.
    
    Args:
        reference_image_path: Path to reference image
        
    Returns:
        BytesIO object containing the image
    """
    if not os.path.exists(reference_image_path):
        raise FileNotFoundError(f"Reference image not found: {reference_image_path}")
    
    # Load the image and convert to RGBA
    img = Image.open(reference_image_path).convert("RGBA")
    
    # Create a memory buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.name = "reference.png"  # Set name for MIME type
    buf.seek(0)  # Reset position to beginning
    
    return buf

def generate_image_with_reference(
    api_key: str, 
    prompt: str, 
    reference_image: io.BytesIO,
    quality: str = "high",
    size: str = "1024x1536",
    model: str = "gpt-image-1",
    max_retries: int = 2
) -> Dict[str, str]:
    """
    Generate an image using OpenAI's API with a reference image.
    
    Args:
        api_key: OpenAI API key
        prompt: Enhanced prompt
        reference_image: Processed reference image
        quality: Image quality
        size: Image dimensions
        
    Returns:
        Dictionary with image data (URL or base64)
    """
    try:
        # Make sure reference image is at the beginning
        reference_image.seek(0)
        
        # Create transparent mask for the reference image
        reference = Image.open(reference_image)
        reference_image.seek(0)  # Reset position after reading
        
        mask = Image.new("RGBA", reference.size, (0, 0, 0, 0))
        mask_buffer = io.BytesIO()
        mask.save(mask_buffer, format="PNG")
        mask_buffer.name = "mask.png"
        mask_buffer.seek(0)
        
        # Create form data properly
        files = {
            "image": ("reference.png", reference_image, "image/png"),
            "mask": ("mask.png", mask_buffer, "image/png")
        }
        
        data = {
            "prompt": prompt,
            "model": model,
            "size": size,
            "quality": quality,
            "n": "1"
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Implement retry mechanism
        for attempt in range(max_retries + 1):
            try:
                # Make API request with proper multipart form
                response = requests.post(
                    "https://api.openai.com/v1/images/edits",
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=60
                )
                
                if response.status_code == 200:
                    break
                elif response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries:
                    # Retry on rate limit or server errors
                    retry_after = int(response.headers.get('retry-after', 1))
                    logger.warning(f"Rate limited or server error ({response.status_code}). Retrying in {retry_after}s...")
                    import time
                    time.sleep(retry_after)
                    # Need to reset file positions for retry
                    reference_image.seek(0)
                    mask_buffer.seek(0)
                else:
                    # Other error, raise exception
                    raise Exception(f"API error: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    logger.warning(f"Request failed: {str(e)}. Retrying...")
                    import time
                    time.sleep(1)
                    # Need to reset file positions for retry
                    reference_image.seek(0)
                    mask_buffer.seek(0)
                else:
                    raise
        
        result = response.json()
        if "data" in result and len(result["data"]) > 0:
            return result["data"][0]
        else:
            raise Exception("No image data in response")
            
    except Exception as e:
        logger.error(f"Error in image generation with reference: {str(e)}")
        # Fall back to standard generation
        logger.info("Falling back to standard image generation")
        return generate_image_standard(
            api_key=api_key, 
            prompt=prompt, 
            quality=quality, 
            size=size, 
            model=model, 
            max_retries=max_retries
        )

def generate_image_standard(
    api_key: str, 
    prompt: str, 
    quality: str = "high",
    size: str = "1024x1536",
    model: str = "gpt-image-1",
    max_retries: int = 2
) -> Dict[str, str]:
    """
    Generate an image using OpenAI's standard image generation API.
    
    Args:
        api_key: OpenAI API key
        prompt: Enhanced prompt
        quality: Image quality
        size: Image dimensions
        
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
    
    # Implement retry mechanism
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                break
            elif response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries:
                # Retry on rate limit or server errors
                retry_after = int(response.headers.get('retry-after', 1))
                logger.warning(f"Rate limited or server error ({response.status_code}). Retrying in {retry_after}s...")
                import time
                time.sleep(retry_after)
            else:
                # Other error, raise exception
                raise Exception(f"API error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                logger.warning(f"Request failed: {str(e)}. Retrying...")
                import time
                time.sleep(1)
            else:
                raise
    
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")
    
    result = response.json()
    if "data" in result and len(result["data"]) > 0:
        return result["data"][0]
    else:
        raise Exception("No image data in response")

def save_image(image_data: Dict[str, str], output_path: str) -> None:
    """
    Save image data to a file.
    
    Args:
        image_data: Image data from API (URL or base64)
        output_path: Path to save the image
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        if "b64_json" in image_data:
            # Decode base64 data
            img_data = base64.b64decode(image_data["b64_json"])
            with open(output_path, "wb") as f:
                f.write(img_data)
                
        elif "url" in image_data:
            # Download from URL
            response = requests.get(image_data["url"], timeout=30)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
            else:
                raise Exception(f"Failed to download image: {response.status_code}")
        else:
            raise Exception(f"Unsupported image data format: {image_data.keys()}")
            
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        raise
