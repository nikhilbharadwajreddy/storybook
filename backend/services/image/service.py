"""
Image generation service for the Storybook application.
Focused exclusively on GPT Image (gpt-image-1) generation.
"""
import os
import logging
import uuid
import requests
import io
from PIL import Image
from openai import OpenAI
from utils.common import get_prompt_text, read_template, calculate_image_token_usage, ensure_directory_exists
from utils.cache import check_cache, save_to_cache
from services.image.processing import process_reference_image, save_image_from_response, extract_image_data

logger = logging.getLogger(__name__)

def generate_image(
    prompt_data, 
    session_id, 
    api_key, 
    child_name,
    reference_image_path=None,
    previous_images=None,
    quality="high",  # Always use high quality for best results
    size="1024x1536",  # Portrait orientation for storybooks
    templates_folder=None,
    upload_folder=None,
    cache_folder=None,
    prompt_index=None,
    output_filename=None
):
    """
    Generate an image for a story prompt using GPT Image.
    
    Args:
        prompt_data: Prompt data dictionary or string
        session_id: Session ID for tracking
        api_key: OpenAI API key
        child_name: Name of the child
        reference_image_path: Path to reference image (optional)
        previous_images: List of previously generated images for continuity
        quality: Image quality (low, medium, high)
        size: Image size (1024x1024, 1024x1536, etc.)
        templates_folder: Path to templates directory
        upload_folder: Path to upload directory for saving images
        cache_folder: Path to cache directory
        prompt_index: Index of the prompt (for sequential numbering)
        output_filename: Specific filename to use (overrides automatic naming)
        
    Returns:
        Dictionary with image path and metadata
    """
    # Safely extract the prompt text
    prompt_text = get_prompt_text(prompt_data)
    logger.info(f"Extracted prompt text: {prompt_text[:50]}...")
    
    # Create cache key from prompt text and parameters
    cache_key = f"{prompt_text}_{quality}_{size}"
    
    # Check cache for existing image
    cache_result = check_cache(cache_key, cache_folder)
    
    # Return cached image if available
    if cache_result and "data" in cache_result:
        cache_data = cache_result["data"]
        image_filename = cache_data.get("filename")
        
        if image_filename:
            # Check if the image file actually exists
            image_path = os.path.join(upload_folder, image_filename)
            if os.path.exists(image_path):
                logger.info(f"Using cached image for {cache_key}")
                return {
                    "image_path": f"/static/images/{image_filename}",
                    "from_cache": True,
                    "token_usage": cache_data.get("token_usage", {}),
                    "filename": image_filename
                }
    
    # Generate new image using gpt-image-1
    image_data = generate_gpt_image(
        api_key, prompt_text, child_name, 
        reference_image_path, previous_images,
        quality, size, templates_folder,
        upload_folder
    )
    
    # Save the image
    return save_generated_image(
        image_data, prompt_text, quality, size,
        session_id, reference_image_path, upload_folder, cache_folder,
        prompt_index=prompt_index, output_filename=output_filename
    )

def generate_gpt_image(api_key, prompt_text, child_name, reference_image_path=None, 
                      previous_images=None, quality="high", size="1024x1536", templates_folder=None,
                      upload_folder=None):
    """
    Generate an image using GPT Image model with simplified reference image handling.
    
    Args:
        api_key: OpenAI API key
        prompt_text: Original prompt text
        child_name: Name of the child
        reference_image_path: Path to reference image (if any)
        previous_images: List of previously generated images for continuity
        quality: Image quality (default "high")
        size: Image size (default "1024x1536" for portrait orientation)
        templates_folder: Path to templates directory
        upload_folder: Path needed for accessing previous images
        
    Returns:
        Image data response
    """
    # Initialize formatted_prompt at the beginning to avoid reference before assignment errors
    formatted_prompt = prompt_text  # Default to original text if template processing fails
    
    try:
        # Initialize the OpenAI client
        openai_client = OpenAI(api_key=api_key)
        
        # Prepare the reference image with the simplified approach
        reference_images = process_reference_image(reference_image_path, child_name)
        
        # Create image prompt from template
        template = read_template(templates_folder, 'image_prompt.txt')
            
        # Use template with reference if available
        if reference_image_path and os.path.exists(reference_image_path):
            template = read_template(templates_folder, 'image_prompt_with_reference.txt')
        
        # Format the prompt
        formatted_prompt = template.format(
            prompt_text=prompt_text,
            child_name=child_name
        )
        
        # Create enhanced prompt for better results with continuity
        enhanced_prompt = create_enhanced_prompt(
            prompt_text, 
            child_name, 
            bool(reference_images),
            previous_images
        )
        
        logger.info(f"Generating image with prompt: {enhanced_prompt[:100]}...")
        
        # If we have a reference image, use edit API
        if reference_images:
            try:
                logger.info(f"Using reference image for {child_name}")
                
                # Call the OpenAI API using the edit endpoint
                logger.info(f"Calling OpenAI API with reference image")
                
                # Debug information about the reference image
                if hasattr(reference_images[0], 'name'):
                    logger.info(f"Reference image name: {reference_images[0].name}")
                
                # Try reading the first few bytes to verify it's a valid image file
                try:
                    image_start = reference_images[0].read(16)
                    reference_images[0].seek(0)  # Reset position
                    logger.info(f"Reference image first bytes: {image_start.hex()}")
                    
                    # Check if these are valid PNG or JPEG bytes
                    is_png = image_start.startswith(b'\x89PNG')
                    is_jpeg = image_start.startswith(b'\xff\xd8')
                    logger.info(f"Image format check - PNG: {is_png}, JPEG: {is_jpeg}")
                except Exception as e:
                    logger.warning(f"Error checking image bytes: {e}")
                
                # Create transparent mask
                try:
                    # First read the image size
                    temp_img = Image.open(reference_images[0])
                    reference_images[0].seek(0)  # Reset position after reading
                    
                    # Create a transparent mask with same size
                    mask_buffer = io.BytesIO()
                    mask = Image.new("RGBA", temp_img.size, (0, 0, 0, 0))
                    mask.save(mask_buffer, format="PNG")
                    mask_buffer.seek(0)
                    mask_buffer.name = "mask.png"  # Important for MIME type detection
                    
                    # Log mask details
                    logger.info(f"Created transparent mask: size={temp_img.size}")
                    
                    # Call the OpenAI API with mask
                    result = openai_client.images.edit(
                        model="gpt-image-1",
                        image=reference_images,
                        mask=mask_buffer,
                        prompt=enhanced_prompt,
                        size=size,
                        quality=quality
                    )
                except Exception as mask_error:
                    # If mask creation fails, try without mask
                    logger.warning(f"Error with mask: {mask_error}, attempting without mask")
                    
                    # Call API without mask as fallback
                    result = openai_client.images.edit(
                        model="gpt-image-1",
                        image=reference_images,
                        prompt=enhanced_prompt,
                        size=size,
                        quality=quality
                    )
                logger.info("Successfully generated image with reference")
                
            except Exception as e:
                logger.warning(f"Reference image failed, falling back to standard generation: {e}")
                # Fall back to standard generation with extra description
                result = openai_client.images.generate(
                    model="gpt-image-1",
                    prompt=enhanced_prompt + f" The child named {child_name} should be the main character.",
                    size=size,
                    quality=quality
                )
        else:
            # No reference image, use standard generation
            result = openai_client.images.generate(
                model="gpt-image-1",
                prompt=enhanced_prompt,
                size=size,
                quality=quality
            )
        
        # Extract image data from the response
        image_data = extract_image_data(result)
        if image_data:
            return image_data
        else:
            raise Exception("No image data found in API response")
    
    except Exception as e:
        logger.exception(f"Error using GPT Image generation: {str(e)}")
        # Fall back to standard approach
        return generate_image_with_fallback(
            api_key, 
            formatted_prompt, 
            quality=quality, 
            size=size
        )

def create_enhanced_prompt(original_prompt, child_name, has_reference=False, previous_images=None):
    """
    Create an enhanced prompt for GPT Image generation with better results.
    
    Args:
        original_prompt: Original story prompt
        child_name: Name of the child
        has_reference: Whether a reference image is being used
        previous_images: List of previously generated images for continuity
        
    Returns:
        Enhanced prompt text
    """
    # Create different prompts based on whether a reference image is provided
    if has_reference:
        # If reference image is provided, emphasize keeping child's appearance consistent
        illustration_prompt = f"""
        Create a professional-quality children's book illustration in PORTRAIT ORIENTATION depicting this exact scene: {original_prompt}
        
        IMPORTANT: I have uploaded a reference image that shows what {child_name} looks like. You MUST make the child look EXACTLY like the uploaded reference image.
        
        This must be a PREMIUM-QUALITY, FULL SCENE ILLUSTRATION with these specific characteristics:
        
        - PORTRAIT ORIENTATION (taller than wide, 1024x1536 pixels) designed specifically for a children's book page
        - Make {child_name} look EXACTLY like the child in the uploaded reference image (same face, hair, skin tone, clothing style)
        - Position {child_name} prominently in the composition as the clear focal point
        - Use the UPLOADED REFERENCE IMAGE to accurately depict {child_name}'s appearance and facial features
        - Show the exact action and all elements described in the prompt with careful attention to detail
        - Use bright, saturated colors with strong contrast to create visual interest
        - Include a complete, detailed background environment that enhances the story
        - Use professional-quality lighting effects to create depth and atmosphere
        - Create a whimsical, magical feeling with fantastical elements and wonder
        - Apply an appealing cartoon art style similar to modern Disney/Pixar animation
        - Ensure all characters have clear outlines and distinct silhouettes
        
        CRITICALLY IMPORTANT: 
        - {child_name} MUST look EXACTLY like the child in the UPLOADED REFERENCE IMAGE
        - The reference image I uploaded contains the actual appearance of {child_name} that must be matched
        - The image MUST be in PORTRAIT ORIENTATION (width: 1024px, height: 1536px)
        - Create a complete scene with characters AND detailed background
        - The illustration must look PROFESSIONAL-QUALITY like it belongs in a published book
        
        Create an illustration that would look perfectly at home in a high-quality published children's picture book.
        """
    else:
        # Standard prompt without reference image
        illustration_prompt = f"""
        Create a professional-quality children's book illustration in PORTRAIT ORIENTATION depicting this exact scene: {original_prompt}
        
        This must be a PREMIUM-QUALITY, FULL SCENE ILLUSTRATION with these specific characteristics:
        
        - PORTRAIT ORIENTATION (taller than wide, 1024x1536 pixels) designed specifically for a children's book page
        - Make {child_name} the main character with clear, detailed features and expressive face
        - Position {child_name} prominently in the composition as the clear focal point
        - Show the exact action and all elements described in the prompt with careful attention to detail
        - Use bright, saturated colors with strong contrast to create visual interest
        - Include a complete, detailed background environment that enhances the story
        - Use professional-quality lighting effects to create depth and atmosphere
        - Create a whimsical, magical feeling with fantastical elements and wonder
        - Apply an appealing cartoon art style similar to modern Disney/Pixar animation
        - Ensure all characters have clear outlines and distinct silhouettes
        
        CRITICALLY IMPORTANT: 
        - This MUST be a COMPLETE SCENE with characters AND detailed background
        - The image MUST directly illustrate the exact action in the prompt
        - The character {child_name} MUST be prominently featured and instantly recognizable
        - The image MUST be in PORTRAIT ORIENTATION (width: 1024px, height: 1536px)
        - The illustration must look PROFESSIONAL-QUALITY like it belongs in a published book
        
        Create an illustration that would look perfectly at home in a high-quality published children's picture book.
        """
    
    return illustration_prompt

def generate_image_with_fallback(api_key, prompt, quality="high", size="1024x1536"):  # Portrait orientation
    """
    Simple fallback implementation for image generation.
    
    Args:
        api_key: OpenAI API key
        prompt: Text prompt for image generation
        quality: Image quality level
        size: Image size
        
    Returns:
        Image data response
    """
    # Prepare request data
    request_data = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "quality": quality,
        "size": size
    }
    
    # Set endpoint
    endpoint = "https://api.openai.com/v1/images/generations"
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"Making fallback image generation request")
        response = requests.post(
            endpoint,
            headers=headers,
            json=request_data,
            timeout=120
        )
        
        # Check for errors
        if response.status_code != 200:
            error_message = f"API error {response.status_code}: {response.text}"
            logger.error(error_message)
            return {"error": error_message}
        
        # Parse response
        result = response.json()
        
        # Extract data
        if 'data' in result and len(result['data']) > 0:
            image_data = result['data'][0]
            
            # Handle different response formats
            if 'b64_json' in image_data:
                return {
                    'b64_json': image_data['b64_json']
                }
            elif 'url' in image_data:
                return {
                    'url': image_data['url']
                }
        
        return {"error": "Unexpected response format"}
            
    except Exception as e:
        error_message = f"Error in fallback image generation: {str(e)}"
        logger.error(error_message)
        return {"error": error_message}

def save_generated_image(image_data, prompt_text, quality, size, 
                        session_id, reference_image_path, upload_folder, cache_folder,
                        prompt_index=None, output_filename=None):
    """
    Save a generated image and update cache.
    
    Args:
        image_data: Image data from API
        prompt_text: Original prompt text
        quality: Quality setting
        size: Image size
        session_id: Session ID
        reference_image_path: Path to reference image
        upload_folder: Path to upload directory
        cache_folder: Path to cache directory
        prompt_index: Index of the prompt (for sequential numbering)
        output_filename: Specific filename to use (overrides automatic naming)
        
    Returns:
        Dictionary with image path and metadata
    """
    # Create filename based on provided parameters or generate a unique one
    if output_filename:
        image_filename = output_filename
    elif session_id and prompt_index is not None:
        # Use sequential numbering: prompt_index * 2 + 1 for story images
        image_number = prompt_index * 2 + 1
        image_filename = f"{session_id}/{image_number}_image.png"
        
        # Ensure the session folder exists
        ensure_directory_exists(os.path.join(upload_folder, session_id))
    else:
        # Fallback to UUID if no session/index provided
        ref_part = os.path.basename(reference_image_path) if reference_image_path else ""
        image_filename = f"{uuid.uuid4()}_{ref_part}.png"
    
    image_path = os.path.join(upload_folder, image_filename)
    
    # Save the image file
    save_success = save_image_from_response(image_data, image_path)
    if not save_success:
        raise Exception("Failed to save generated image")
    
    # Calculate token usage
    token_usage = calculate_image_token_usage(size, quality)
    
    # Create cache data
    cache_data = {
        "filename": image_filename,
        "token_usage": token_usage,
        "quality": quality,
        "size": size
    }
    
    # Save to cache
    cache_key = f"{prompt_text}_{quality}_{size}"
    save_to_cache(cache_key, cache_data, cache_folder)
    
    # Return result
    return {
        "image_path": f"/static/images/{image_filename}",
        "from_cache": False,
        "token_usage": token_usage,
        "filename": image_filename
    }
