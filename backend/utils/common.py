"""
Common utility functions for the Storybook application.
"""
import os
import re
import json
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """
    Check if the file has an allowed extension.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_prompt_text(prompt_data):
    """
    Extract prompt text from different possible data structures.
    
    Args:
        prompt_data: Prompt data (string or dictionary)
        
    Returns:
        str: Prompt text
    """
    if isinstance(prompt_data, str):
        return prompt_data
    elif isinstance(prompt_data, dict) and 'prompt' in prompt_data:
        return prompt_data['prompt']
    elif hasattr(prompt_data, 'get'):
        return prompt_data.get('prompt', str(prompt_data))
    return str(prompt_data)

def read_template(templates_folder, primary_template_name, fallback_template_name=None):
    """
    Read a template file with fallback options.
    
    Args:
        templates_folder: Path to templates directory
        primary_template_name: Name of the primary template file
        fallback_template_name: Name of the fallback template file (optional)
        
    Returns:
        str: Template content
        
    Raises:
        Exception: If no template could be read
    """
    try:
        template_path = os.path.join(templates_folder, primary_template_name)
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif fallback_template_name:
            fallback_path = os.path.join(templates_folder, fallback_template_name)
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        # Last resort fallback
        default_template = """
        Create a children's story about {child_name} who {traits}. 
        The story should have a {theme} theme and be appropriate for a young child.
        Generate {num_prompts} creative and engaging story prompts.
        """
        logger.warning(f"Using default template, could not find {primary_template_name} or {fallback_template_name}")
        return default_template
    
    except Exception as e:
        logger.exception(f"Error reading template: {str(e)}")
        raise Exception(f"Failed to read template: {str(e)}")

def ensure_directory_exists(directory_path):
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        str: Path to the directory
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return directory_path
    except Exception as e:
        logger.exception(f"Error creating directory {directory_path}: {str(e)}")
        raise Exception(f"Failed to create directory: {str(e)}")

def calculate_text_tokens(model, text_length):
    """
    Estimate token count for billing purposes.
    
    Args:
        model: Model name
        text_length: Length of the text in characters
        
    Returns:
        dict: Token usage information
    """
    # Rough estimation: 1 token ≈ 4 characters in English
    tokens = max(1, int(text_length / 4))
    
    # Assume roughly 1:2 ratio of input to output tokens
    input_tokens = tokens // 3
    output_tokens = tokens - input_tokens
    
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens
    }

def calculate_image_token_usage(size, quality):
    """
    Calculate token usage for image generation based on size and quality.
    
    Args:
        size: Image size
        quality: Image quality
        
    Returns:
        dict: Token usage information
    """
    # Token usage estimates for GPT Image
    quality_tokens = {
        "low": 272,      # ~272 tokens
        "medium": 1056,  # ~1056 tokens
        "high": 4160     # ~4160 tokens
    }
    
    # Size multipliers
    size_multipliers = {
        "1024x1024": 1.0,
        "1024x1536": 1.5,
        "1536x1024": 1.5,
        "1792x1024": 1.7
    }
    
    # Get base tokens for quality level
    base_tokens = quality_tokens.get(quality, quality_tokens["high"])
    
    # Apply size multiplier
    multiplier = size_multipliers.get(size, 1.0)
    tokens = int(base_tokens * multiplier)
    
    return {
        "model": "gpt-image-1",
        "size": size,
        "quality": quality,
        "tokens": tokens
    }

def process_file_path(path):
    """
    Process a file path to ensure it's valid.
    
    Args:
        path: Original file path
        
    Returns:
        str: Processed file path
    """
    # Remove leading /static/ if present
    if path.startswith('/static/'):
        path = path[8:]
    
    # Remove leading /images/ if present
    if path.startswith('/images/'):
        path = path[8:]
    
    return path
