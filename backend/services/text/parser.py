"""
Parser module for text responses from API calls.
Handles parsing of JSON and other structured text formats.
"""
import json
import re
import logging

logger = logging.getLogger(__name__)

def parse_openai_json_response(text):
    """
    Parse JSON response from OpenAI API.
    
    Args:
        text: Text response from OpenAI
        
    Returns:
        Parsed JSON object
        
    Raises:
        Exception: If parsing fails
    """
    try:
        # First try direct JSON parsing
        try:
            json_obj = json.loads(text)
            return json_obj
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON
            logger.info("Direct JSON parsing failed, trying to extract JSON")
            pass
        
        # Remove potential non-JSON prefix (like comments or instructions)
        json_pattern = r'(\[.*\]|\{.*\})'
        json_match = re.search(json_pattern, text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            # If no JSON found, try to create an array from the text
            logger.warning("No JSON found in response, attempting to create a structured array")
            lines = text.split('\n')
            prompts = []
            
            current_prompt = ""
            for line in lines:
                line = line.strip()
                if line and (line.startswith('Prompt') or line.startswith('Story')):
                    if current_prompt:
                        prompts.append({"prompt": current_prompt.strip()})
                        current_prompt = ""
                    current_prompt = line
                elif current_prompt and line:
                    current_prompt += " " + line
            
            # Add the last prompt
            if current_prompt:
                prompts.append({"prompt": current_prompt.strip()})
            
            if not prompts:
                # Last resort: Just create prompts from each paragraph
                paragraphs = [p for p in text.split('\n\n') if p.strip()]
                prompts = [{"prompt": p.strip()} for p in paragraphs if len(p.strip()) > 20]
            
            if prompts:
                return prompts
            
            raise Exception("Failed to generate valid prompts from response")
    
    except Exception as e:
        logger.exception(f"Error parsing OpenAI response: {str(e)}")
        logger.error(f"Response text: {text[:200]}...")
        raise Exception(f"Could not parse prompts: {str(e)}")

def extract_text_from_html(html):
    """
    Extract plain text from HTML.
    
    Args:
        html: HTML content
        
    Returns:
        Plain text extracted from HTML
    """
    try:
        # Simple HTML tag removal
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    except Exception as e:
        logger.exception(f"Error extracting text from HTML: {str(e)}")
        return html
