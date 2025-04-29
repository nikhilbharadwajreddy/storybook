"""
Text Overlay Module
-----------------
Creates text overlay images by combining text with background images.
"""
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def create_text_overlay(
    text: str,
    background_image_path: str,
    session_id: str,
    scene_index: int,
    output_dir: str,
    font_path: Optional[str] = None,
    font_size: int = 36,
    font_color: Tuple[int, int, int] = (0, 0, 0),  # Black
    padding: int = 50
) -> str:
    """
    Create an image with text overlaid on a background.
    
    Args:
        text: Story text to overlay
        background_image_path: Path to background image
        session_id: Session identifier
        scene_index: Index of the scene
        output_dir: Directory to save the image
        font_path: Path to font file (optional)
        font_size: Font size
        font_color: Font color (RGB tuple)
        padding: Padding around text
        
    Returns:
        Path to the generated overlay image
    """
    logger.info(f"Creating text overlay for scene {scene_index}")
    
    # Check if background image exists
    if not os.path.exists(background_image_path):
        logger.warning(f"Background image not found: {background_image_path}")
        # Create a blank background if the background image doesn't exist
        img = Image.new('RGB', (1024, 1024), color=(255, 255, 255))
    else:
        # Open the background image
        img = Image.open(background_image_path)
    
    # Set up the drawing context
    draw = ImageDraw.Draw(img)
    
    # Try to use the specified font, or fall back to default
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            # Use a default font
            font = ImageFont.load_default()
            font_size = 24  # Adjust for default font
    except Exception as e:
        logger.warning(f"Error loading font: {str(e)}. Using default font.")
        font = ImageFont.load_default()
        font_size = 24
    
    # Format text for better readability
    formatted_text = format_text_for_display(text)
    
    # Calculate text position (centered)
    img_width, img_height = img.size
    text_width = img_width - (2 * padding)
    
    # Word wrap the text to fit the width
    wrapped_text = wrap_text(formatted_text, font, text_width)
    
    # Get the total height of wrapped text
    text_height = 0
    for line in wrapped_text:
        # Modern Pillow versions use font.getbbox() instead of draw.textsize
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]  # bottom - top
        text_height += line_height + 10  # 10px line spacing
    
    # Draw each line of text
    y_position = (img_height - text_height) // 2  # Center vertically
    for line in wrapped_text:
        # Get text dimensions using font.getbbox()
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]  # right - left
        x_position = (img_width - text_width) // 2  # Center horizontally
        
        # Draw text with a slight shadow for better readability
        draw.text((x_position + 2, y_position + 2), line, font=font, fill=(128, 128, 128))  # Shadow
        draw.text((x_position, y_position), line, font=font, fill=font_color)  # Main text
        
        y_position += font_size + 10  # Move to next line
    
    # Save the image
    filename = f"{session_id}_scene_{scene_index}_text.png"
    output_path = os.path.join(output_dir, filename)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    img.save(output_path)
    logger.info(f"Text overlay saved to {output_path}")
    
    return output_path

def format_text_for_display(text: str) -> str:
    """
    Format text for better display on image.
    
    Args:
        text: Original text
        
    Returns:
        Formatted text
    """
    # Remove any excessive newlines or spaces
    text = ' '.join(text.split())
    
    # Add a title style to first sentence
    sentences = text.split('.')
    if len(sentences) > 0:
        first_sentence = sentences[0].strip()
        rest_of_text = '.'.join(sentences[1:]).strip()
        
        if first_sentence and rest_of_text:
            return f"{first_sentence.upper()}.\n\n{rest_of_text}"
    
    return text

def wrap_text(text: str, font, max_width: int) -> list:
    """
    Wrap text to fit within a specified width.
    
    Args:
        text: Text to wrap
        font: Font object
        max_width: Maximum width in pixels
        
    Returns:
        List of wrapped text lines
    """
    words = text.split()
    wrapped_lines = []
    current_line = []
    
    for word in words:
        # Add the word to the current line
        current_line.append(word)
        
        # Check if current line is too wide
        line_width = font.getlength(' '.join(current_line))
        
        if line_width > max_width:
            # If just one word is already too wide, keep it and move on
            if len(current_line) == 1:
                wrapped_lines.append(current_line[0])
                current_line = []
            else:
                # Remove the last word and add the line
                current_line.pop()
                wrapped_lines.append(' '.join(current_line))
                current_line = [word]  # Start new line with the last word
    
    # Add the last line if there's anything left
    if current_line:
        wrapped_lines.append(' '.join(current_line))
    
    return wrapped_lines
