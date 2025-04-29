"""
Story Generator Module
---------------------
Handles the generation of personalized stories using OpenAI's GPT models.
"""
import logging
import json
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def generate_story(
    child_name: str,
    theme: str,
    traits: str,
    api_key: str,
    num_scenes: int = 3,
    model: str = "gpt-3.5-turbo"
) -> List[str]:
    """
    Generate a personalized story based on child's name, theme, and traits.
    
    Args:
        child_name: Name of the child
        theme: Theme of the story
        traits: Personal traits and interests of the child
        api_key: OpenAI API key
        num_scenes: Number of scenes to generate (default: 3)
        model: OpenAI model to use (default: gpt-4-turbo)
        
    Returns:
        List of story scenes as strings
    """
    logger.info(f"Generating story for {child_name} with theme: {theme}")
    
    # Create prompt for story generation
    prompt = create_story_prompt(child_name, theme, traits, num_scenes)
    
    # Call OpenAI API
    try:
        response = call_openai_api(api_key, prompt, model)
        
        # Parse response into list of scenes
        scenes = parse_story_response(response, num_scenes)
        
        logger.info(f"Successfully generated {len(scenes)} story scenes")
        return scenes
        
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        raise Exception(f"Failed to generate story: {str(e)}")

def create_story_prompt(child_name: str, theme: str, traits: str, num_scenes: int) -> str:
    """
    Create a prompt for the story generation.
    
    Args:
        child_name: Name of the child
        theme: Theme of the story
        traits: Personal traits and interests of the child
        num_scenes: Number of scenes to generate
        
    Returns:
        Formatted prompt string
    """
    return f"""Create a children's story about {child_name} who {traits}. 
The story should have a {theme} theme.

The story should be divided into exactly {num_scenes} sequential scenes that tell ONE continuous story with:
1. A clear beginning (introduction of character and setting)
2. Middle (adventure or challenge)
3. End (resolution)

Each scene should build on the previous one, maintaining continuity of characters, plot, and settings. 
The characters should remain consistent throughout the story.

Format your response as a JSON array of {num_scenes} objects, where each object has a "prompt" key containing 
the scene description. Make each scene description detailed and visual, about 3-4 sentences long.

Example output format:
[
  {{
    "prompt": "Scene 1 description here..."
  }},
  {{
    "prompt": "Scene 2 description here that continues directly from scene 1..."
  }},
  {{
    "prompt": "Scene 3 description that follows from scene 2 and brings the story to conclusion..."
  }}
]

IMPORTANT: Make sure each scene directly continues from the previous one in a logical story flow. 
This is a single, coherent story told across {num_scenes} scenes, NOT {num_scenes} different story ideas.

Return ONLY the JSON array, nothing else.
"""

def call_openai_api(api_key: str, prompt: str, model: str = "gpt-4-turbo") -> str:
    """
    Call the OpenAI API to generate text.
    
    Args:
        api_key: OpenAI API key
        prompt: Text prompt to send
        model: Model to use
        
    Returns:
        Generated text response
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )
    
    if response.status_code != 200:
        error_text = response.text or f"Status code: {response.status_code}"
        raise Exception(f"OpenAI API error: {error_text}")
    
    result = response.json()
    return result["choices"][0]["message"]["content"]

def parse_story_response(response: str, expected_scenes: int) -> List[str]:
    """
    Parse the JSON response from OpenAI into a list of story scenes.
    
    Args:
        response: JSON string response from OpenAI
        expected_scenes: Expected number of scenes
        
    Returns:
        List of story scenes as strings
    """
    try:
        # Clean up the response to ensure it's valid JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response.split("```json")[1]
        if response.startswith("```"):
            response = response.split("```")[1]
        response = response.strip()
        
        # Parse JSON
        scenes_data = json.loads(response)
        
        # Extract prompts
        scenes = []
        for scene in scenes_data:
            if "prompt" in scene:
                scenes.append(scene["prompt"])
        
        # Validate we have the expected number of scenes
        if len(scenes) != expected_scenes:
            logger.warning(f"Expected {expected_scenes} scenes but got {len(scenes)}")
        
        return scenes
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        # Fallback: try to extract content without JSON parsing
        if "prompt" in response:
            # Try basic extraction if JSON parsing fails
            scenes = []
            parts = response.split('"prompt":')
            for part in parts[1:]:  # Skip first part before first "prompt"
                # Extract text between quotes
                start = part.find('"')
                if start != -1:
                    end = part.find('"', start + 1)
                    if end != -1:
                        scene = part[start + 1:end].strip()
                        scenes.append(scene)
            return scenes
        else:
            # Last resort: split by newlines and return non-empty lines
            scenes = [line.strip() for line in response.split('\n') if line.strip()]
            return scenes[:expected_scenes]  # Limit to expected number
