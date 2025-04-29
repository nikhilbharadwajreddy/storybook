"""
Improved Text Overlay Module
--------------------------
Creates text overlay images with larger, more readable text that fills the image better.
"""
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

def create_text_overlay(
    text: str,
    background_image_path: str,
    session_id: str,
    scene_index: int,
    output_dir: str,
    font_path: Optional[str] = None,
    font_size: int = 55,  # Default font size set to 55
    font_color: Tuple[int, int, int] = (20, 30, 70),  # Dark navy blue instead of black
    padding_percent: float = 0.1  # Padding as percentage of image width
) -> str:
    """
    Create an image with large text overlaid on a background.
    
    Args:
        text: Story text to overlay
        background_image_path: Path to background image
        session_id: Session identifier
        scene_index: Index of the scene
        output_dir: Directory to save the image
        font_path: Path to font file (optional)
        font_size: Initial font size to try (will be adjusted to fit)
        font_color: Font color (RGB tuple)
        padding_percent: Padding around text as percentage of image width
        
    Returns:
        Path to the generated overlay image
    """
    logger.info(f"Creating improved text overlay for scene {scene_index}")
    
    # Check if background image exists
    if not os.path.exists(background_image_path):
        logger.warning(f"Background image not found: {background_image_path}")
        # Create a blank background if the background image doesn't exist
        img = Image.new('RGB', (1024, 1536), color=(255, 255, 255))
    else:
        # Open the background image and ensure it's the right size
        img = Image.open(background_image_path)
        # Ensure the image is in RGB mode for drawing text
        if img.mode != 'RGB':
            img = img.convert('RGB')
    
    # Get image dimensions
    img_width, img_height = img.size
    
    # Calculate padding in pixels
    padding = int(img_width * padding_percent)
    
    # Set up the drawing context
    draw = ImageDraw.Draw(img)
    
    # Try to use the specified font, or fall back to default
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            # Use a system font that's likely to be available and good for display
            try:
                # Try common fonts that look good for storybooks
                system_fonts = [
                    "Comic Sans MS", "Baloo Bhai", "Fredoka One", "Quicksand",
                    "Arial Rounded MT Bold", "Chalkboard", "Marker Felt",
                    "Verdana", "Georgia", "Tahoma", "Trebuchet MS"
                ]
                for font_name in system_fonts:
                    try:
                        font = ImageFont.truetype(font_name, font_size)
                        break
                    except:
                        continue
                else:
                    # If none of the specific fonts work, fall back to default
                    font = ImageFont.load_default()
                    font_size = 60  # Still make it fairly large
            except Exception:
                font = ImageFont.load_default()
                font_size = 60
    except Exception as e:
        logger.warning(f"Error loading font: {str(e)}. Using default font.")
        font = ImageFont.load_default()
        font_size = 60
    
    # Format text for better readability
    formatted_text = format_text_for_display(text)
    
    # Calculate usable text area
    text_area_width = img_width - (2 * padding)
    text_area_height = img_height - (2 * padding)
    
    # Find the optimal font size to fill the available space
    font, wrapped_text = find_optimal_font_size(
        formatted_text, 
        font, 
        text_area_width, 
        text_area_height,
        initial_size=font_size
    )
    
    # Calculate text block height
    total_height = calculate_text_block_height(wrapped_text, font)
    
    # Draw text centered in the image
    draw_centered_text(
        draw,
        wrapped_text,
        font,
        (img_width, img_height),
        padding,
        font_color
    )
    
    # Save the image
    filename = f"{session_id}_scene_{scene_index}_text.png"
    output_path = os.path.join(output_dir, filename)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    img.save(output_path)
    logger.info(f"Improved text overlay saved to {output_path}")
    
    return output_path

def format_text_for_display(text: str) -> str:
    """
    Format text for better display on image.
    
    Args:
        text: Original text
        
    Returns:
        Formatted text
    """
    # Handle multiple paragraphs properly
    paragraphs = text.split('\n\n')
    formatted_paragraphs = []
    
    for i, paragraph in enumerate(paragraphs):
        # Clean up the paragraph - remove excess whitespace
        paragraph = ' '.join(paragraph.split())
        
        # Handle first paragraph differently - it gets the title treatment
        if i == 0:
            sentences = paragraph.split('.')
            if len(sentences) > 0 and sentences[0].strip():
                first_sentence = sentences[0].strip()
                rest_of_paragraph = '.'.join(sentences[1:]).strip()
                
                # Format first sentence as title and add the rest
                if rest_of_paragraph:
                    formatted_paragraphs.append(f"{first_sentence.upper()}.\n{rest_of_paragraph}")
                else:
                    formatted_paragraphs.append(f"{first_sentence.upper()}.")
            else:
                formatted_paragraphs.append(paragraph)
        else:
            # Just add other paragraphs normally
            formatted_paragraphs.append(paragraph)
    
    # Join paragraphs with double newlines
    return '\n\n'.join(formatted_paragraphs)

def wrap_text(text: str, font, max_width: int) -> List[str]:
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

def find_optimal_font_size(text: str, initial_font, max_width: int, max_height: int, initial_size: int = 100) -> tuple:
    """
    Find the optimal font size to fill the available space.
    
    Args:
        text: Text to display
        initial_font: Font object to start with
        max_width: Maximum width available
        max_height: Maximum height available
        initial_size: Initial font size to try
        
    Returns:
        Tuple of (optimal font, wrapped text lines)
    """
    # Start with a large font size and decrease until text fits
    font_size = initial_size
    current_font = initial_font
    
    # Try to load the same font but with different sizes
    font_family = getattr(initial_font, "path", None)
    min_font_size = 10  # Don't go smaller than this
    
    while font_size >= min_font_size:
        try:
            if font_family:
                current_font = ImageFont.truetype(font_family, font_size)
            else:
                # If we don't have a font family, just use the default font
                current_font = ImageFont.load_default()
                # We can't resize the default font, so just return it
                break
        except Exception:
            # If we can't load the font, just use the initial font
            current_font = initial_font
            break
        
        # Wrap text with current font
        wrapped_text = wrap_text(text, current_font, max_width)
        
        # Calculate text block height
        text_height = calculate_text_block_height(wrapped_text, current_font)
        
        # Check if text fits in available height
        if text_height <= max_height:
            # Found a suitable font size
            return current_font, wrapped_text
        
        # Reduce font size and try again
        font_size -= 5
    
    # If we get here, use the smallest acceptable font size
    if font_family:
        try:
            current_font = ImageFont.truetype(font_family, max(font_size, min_font_size))
        except Exception:
            current_font = initial_font
    
    wrapped_text = wrap_text(text, current_font, max_width)
    return current_font, wrapped_text

def calculate_text_block_height(wrapped_text: List[str], font) -> int:
    """
    Calculate the total height of the text block.
    
    Args:
        wrapped_text: List of text lines
        font: Font object
        
    Returns:
        Total height in pixels
    """
    total_height = 0
    line_spacing = 1.2  # Multiplier for line spacing
    
    for line in wrapped_text:
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]  # bottom - top
        total_height += int(line_height * line_spacing)
    
    return total_height

def draw_centered_text(draw, wrapped_text: List[str], font, image_size: Tuple[int, int], padding: int, color: Tuple[int, int, int]):
    """
    Draw text centered in the image with proper spacing.
    
    Args:
        draw: ImageDraw object
        wrapped_text: List of text lines
        font: Font object
        image_size: Tuple of (width, height)
        padding: Padding around text in pixels
        color: Text color
    """
    img_width, img_height = image_size
    
    # Handle multi-paragraph detection
    formatted_lines = []
    line_types = []  # 0 = normal, 1 = title, 2 = paragraph break
    
    # Process lines to handle paragraph breaks and identify title
    for i, line in enumerate(wrapped_text):
        if line.strip() == "":
            # This is a paragraph break
            formatted_lines.append("")
            line_types.append(2)  # paragraph break
        elif i == 0:
            # This is the title line
            formatted_lines.append(line)
            line_types.append(1)  # title
        else:
            # Normal line
            formatted_lines.append(line)
            line_types.append(0)  # normal
    
    # Calculate text block height with adjusted spacing for paragraph breaks
    text_height = 0
    for i, line in enumerate(formatted_lines):
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1] if line else 0  # Height is 0 for empty lines
        
        # Add line height with appropriate spacing
        if line_types[i] == 2:  # paragraph break
            text_height += int(line_height * 2.0)  # Extra space for paragraph breaks
        else:
            text_height += int(line_height * 1.2)  # Normal spacing
    
    # Start position (centered vertically)
    y_position = (img_height - text_height) // 2
    
    # Get title font (larger version of the same font if possible)
    title_font = font
    try:
        if hasattr(font, "path"):
            title_font_size = int(font.size * 1.2)  # Make title 20% larger
            title_font = ImageFont.truetype(font.path, title_font_size)
    except Exception:
        # If we can't create a larger title font, just use the regular font
        pass
    
    # Draw each line
    for i, line in enumerate(formatted_lines):
        # Skip empty paragraph break lines
        if line_types[i] == 2:
            y_position += int(font.getbbox("A")[3] * 2.0)  # Extra space for paragraph break
            continue
            
        # Get line dimensions
        current_font = title_font if line_types[i] == 1 else font
        bbox = current_font.getbbox(line)
        line_width = bbox[2] - bbox[0]  # right - left
        line_height = bbox[3] - bbox[1]  # bottom - top
        
        # Center horizontally
        x_position = (img_width - line_width) // 2
        
        # Title line (first line)
        if line_types[i] == 1:
            # Create a stronger outline/glow for the title
            outline_color = (50, 50, 50, 180)  # Dark gray with some transparency
            outline_width = max(3, int(line_height * 0.03))  # Thicker outline for title
            
            # Draw multiple outline positions for a stronger effect
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, -2), (0, 2), (-2, 0), (2, 0)]:
                draw.text(
                    (x_position + dx * outline_width//2, y_position + dy * outline_width//2), 
                    line, 
                    font=current_font, 
                    fill=outline_color
                )
            
            # Draw main title text
            draw.text((x_position, y_position), line, font=current_font, fill=color)
            
        else:  # Normal text lines
            # Add subtle outline for better readability on all backgrounds
            outline_color = (60, 60, 60, 160)  # Dark gray with more transparency
            
            # Draw subtle outline
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text(
                    (x_position + dx, y_position + dy), 
                    line, 
                    font=current_font, 
                    fill=outline_color
                )
            
            # Draw main text
            draw.text((x_position, y_position), line, font=current_font, fill=color)
        
        # Move to next line with appropriate spacing
        y_position += int(line_height * 1.2)  # 20% extra space between lines
