"""
Text generation service for the Storybook application.
"""
import logging
import requests
from utils.common import read_template, calculate_text_tokens
from utils.cache import check_cache, save_to_cache
from services.text.parser import parse_openai_json_response

logger = logging.getLogger(__name__)

def generate_prompts(child_name, theme, num_prompts, traits, api_key, text_model, templates_folder, cache_folder):
    """
    Generate story prompts based on user input.
    
    Args:
        child_name: Name of the child
        theme: Story theme
        num_prompts: Number of prompts to generate
        traits: Personal traits/details of the child
        api_key: OpenAI API key
        text_model: Model to use for text generation
        templates_folder: Path to templates directory
        cache_folder: Path to cache directory
        
    Returns:
        Dictionary with prompts and token usage information
    """
    # Create prompt from template
    prompt = create_prompt_from_template(child_name, theme, num_prompts, traits, templates_folder)
    
    # Create cache key
    cache_key = f"{child_name}_{theme}_{num_prompts}_{traits}_{text_model}"
    
    # Check cache for existing results
    cache_result = check_cache(cache_key, cache_folder)
    if cache_result and "data" in cache_result:
        logger.info(f"Using cached prompts for {cache_key}")
        return cache_result["data"]
    
    # Generate new prompts from OpenAI
    result = generate_text_with_openai(
        api_key=api_key,
        prompt=prompt,
        model=text_model
    )
    
    # Cache the results
    prompts = result["content"]
    token_usage = result["token_usage"]
    
    cache_data = {
        "prompts": prompts,
        "token_usage": token_usage,
        "from_cache": False
    }
    
    save_to_cache(cache_key, cache_data, cache_folder)
    
    return cache_data

def create_prompt_from_template(child_name, theme, num_prompts, traits, templates_folder):
    """
    Create a prompt from template with proper error handling.
    
    Args:
        child_name: Name of the child
        theme: Story theme
        num_prompts: Number of prompts to generate
        traits: Personal traits/details
        templates_folder: Path to templates directory
        
    Returns:
        Formatted prompt string
    """
    # Try to read the connected narrative template first
    try:
        template = read_template(templates_folder, 'text_prompt_connected.txt')
        logger.info("Using connected narrative template")
    except Exception as e:
        # If that fails, fall back to the fixed template
        logger.warning(f"Could not load connected template: {e}. Falling back to fixed template.")
        template = read_template(templates_folder, 'text_prompt_fixed.txt', 'text_prompt.txt')
    
    # Format the template
    try:
        # Log template info for debugging
        logger.info(f"Template length: {len(template)}")
        logger.info(f"Template placeholders: {[p for p in template.split('{') if '}' in p]}")
        
        prompt = template.format(
            child_name=child_name,
            theme=theme,
            traits=traits,
            num_prompts=num_prompts
        )
    except KeyError as e:
        logger.error(f"KeyError in template formatting: {str(e)}")
        # Try a direct approach without using .format()
        prompt = template
        prompt = prompt.replace('{child_name}', child_name)
        prompt = prompt.replace('{theme}', theme)
        prompt = prompt.replace('{traits}', traits)
        prompt = prompt.replace('{num_prompts}', str(num_prompts))
        # Log the fixed prompt
        logger.info("Used manual placeholder replacement instead of .format()")
    
    return prompt

def generate_text_with_openai(api_key, prompt, model="gpt-4", temperature=0.7, max_tokens=1000):
    """
    Generate text using the OpenAI API.
    
    Args:
        api_key: OpenAI API key
        prompt: Text prompt to send
        model: Model to use
        temperature: Creativity setting (0-1)
        max_tokens: Maximum tokens to generate
        
    Returns:
        Dictionary with parsed content and usage statistics
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        # Check for errors
        if response.status_code != 200:
            error_text = response.text if response.text else f"Status code: {response.status_code}"
            logger.error(f"OpenAI API error: {error_text}")
            raise Exception(f"OpenAI API error: {error_text}")
        
        # Parse response
        result = response.json()
        
        # Extract generated content
        content = result["choices"][0]["message"]["content"]
        logger.info(f"Raw content from API: {content[:100]}...") # Log the beginning of the content
        
        # Parse JSON from the response
        parsed_content = parse_openai_json_response(content)
        
        # Get usage statistics
        usage = result.get("usage", {})
        token_usage = {
            "model": model,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0)
        }
        
        return {
            "content": parsed_content,
            "token_usage": token_usage
        }
        
    except requests.exceptions.Timeout:
        logger.error("OpenAI API request timed out")
        raise Exception("Request timed out. The server took too long to respond.")
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAI API request failed: {str(e)}")
        raise Exception(f"Request failed: {str(e)}")
    except Exception as e:
        if "Failed to generate valid prompts" in str(e) or "Could not parse prompts" in str(e):
            # Re-raise parsing errors
            raise
        logger.exception(f"Error in OpenAI text generation: {str(e)}")
        raise Exception(f"Error generating text: {str(e)}")
