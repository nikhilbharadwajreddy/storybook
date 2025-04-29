"""
Final Text Overlay Module
----------------------
Creates text overlay images with large, readable text optimized for storybooks.
Incorporates all improvements with fixed font size of 55.
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
    font_size: int = 55,  # Fixed optimal font size
    font_color: Tuple[int, int, int] = (20, 30, 70)  # Dark navy blue
) -> str:
    """
    Create a text overlay image with optimal font size and styling.
    """
    logger.info(f"Creating final text overlay for scene {scene_index}")
    
    # Open or create background
    if not os.path.exists(background_image_path):
        img = Image.new('RGB', (1024, 1536), color=(255, 255, 255))
    else:
        img = Image.open(background_image_path).convert('RGB')
    
    # Get dimensions
    img_width, img_height = img.size
    padding = int(img_width * 0.1)  # 10% padding
    
    # Create drawing context
    draw = ImageDraw.Draw(img)
    
    # Get font - try kid-friendly fonts first
    font = get_storybook_font(font_size)
    
    # Format and wrap text
    formatted_text = format_text(text)
    wrapped_text = wrap_text(formatted_text, font, img_width - 2*padding)
    
    # Calculate text height for centering
    total_height = calculate_text_height(wrapped_text, font)
    y_pos = (img_height - total_height) // 2
    
    # Get title font (20% larger)
    title_font = get_title_font(font, int(font_size * 1.2))
    
    # Draw text
    current_y = y_pos
    for i, line in enumerate(wrapped_text):
        # Skip empty lines (paragraph breaks)
        if not line.strip():
            current_y += int(font_size * 0.8)
            continue
            
        # Determine if this is a title line
        is_title = (i == 0)
        current_font = title_font if is_title else font
        
        # Center line
        line_width = get_text_width(line, current_font)
        x_pos = (img_width - line_width) // 2
        
        # Draw outline/shadow
        outline_color = (50, 50, 50, 180) if is_title else (60, 60, 60, 160)
        
        # Draw outlines (thicker for title)
        offsets = [(-1,-1), (1,-1), (-1,1), (1,1)]
        if is_title:
            offsets.extend([(0,-2), (0,2), (-2,0), (2,0)])
            
        for dx, dy in offsets:
            draw.text((x_pos+dx, current_y+dy), line, font=current_font, fill=outline_color)
        
        # Draw main text
        draw.text((x_pos, current_y), line, font=current_font, fill=font_color)
        
        # Move to next line
        line_height = get_text_height(line, current_font)
        current_y += int(line_height * 1.2)  # 20% extra space
    
    # Save image
    filename = f"{session_id}_scene_{scene_index}_text.png"
    output_path = os.path.join(output_dir, filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    
    return output_path

# def get_storybook_font(size: int) -> ImageFont.FreeTypeFont:
#     """Get a kid-friendly font, with several fallbacks."""
#     kid_fonts = [
#         "Comic Sans MS", "Baloo Bhai", "Fredoka One", "Quicksand",
#         "Arial Rounded MT Bold", "Chalkboard", "Marker Felt",
#         "Verdana", "Georgia", "Tahoma", "Trebuchet MS"
#     ]
    
#     for font_name in kid_fonts:
#         try:
#             return ImageFont.truetype(font_name, size)
#         except:
#             continue
    
#     return ImageFont.load_default()

def get_storybook_font(size: int) -> ImageFont.FreeTypeFont:
    """Load available kid-friendly fonts from static/fonts/ with absolute path."""
    # Get absolute path to the static/fonts directory
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fonts_dir = os.path.join(current_dir, 'static', 'fonts')
    
    # Define font paths
    kid_font_paths = [
        os.path.join(fonts_dir, "ComicNeue-Regular.ttf"),
        os.path.join(fonts_dir, "AkayaKanadaka-Regular.ttf"),
        os.path.join(fonts_dir, "Barriecito-Regular.ttf"),
        os.path.join(fonts_dir, "DynaPuff-VariableFont_wdth,wght.ttf")
    ]
    
    # Log available fonts
    logger.info(f"Looking for fonts in: {fonts_dir}")
    if os.path.exists(fonts_dir):
        available_fonts = os.listdir(fonts_dir)
        logger.info(f"Available fonts: {available_fonts}")
    else:
        logger.warning(f"Fonts directory not found: {fonts_dir}")
    
    # Try each font
    for font_path in kid_font_paths:
        if os.path.exists(font_path):
            try:
                logger.info(f"Loading font: {font_path}")
                return ImageFont.truetype(font_path, size)
            except Exception as e:
                logger.warning(f"Failed to load font {font_path}: {e}")
                continue

    # Fall back to default
    logger.warning("No custom fonts found. Falling back to default font.")
    return ImageFont.load_default()



def get_title_font(base_font, size: int) -> ImageFont.FreeTypeFont:
    """Get a slightly larger font for the title, based on the base font."""
    if hasattr(base_font, "path"):
        try:
            return ImageFont.truetype(base_font.path, size)
        except:
            pass
    return base_font

def format_text(text: str) -> str:
    """Format text with title and paragraph handling."""
    # Handle paragraphs
    paragraphs = text.split('\n\n')
    formatted = []
    
    for i, para in enumerate(paragraphs):
        para = ' '.join(para.split())  # Clean whitespace
        
        # Handle title in first paragraph
        if i == 0:
            sentences = para.split('.')
            if sentences[0].strip():
                first = sentences[0].strip().upper()
                rest = '.'.join(sentences[1:]).strip()
                if rest:
                    formatted.append(f"{first}.\n{rest}")
                else:
                    formatted.append(f"{first}.")
            else:
                formatted.append(para)
        else:
            formatted.append(para)
    
    return '\n\n'.join(formatted)

def wrap_text(text: str, font, max_width: int) -> List[str]:
    """Wrap text to fit within max_width."""
    lines = []
    
    # Split by paragraphs first (preserve paragraph breaks)
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append('')  # Empty line for paragraph break
            continue
            
        words = paragraph.split()
        current_line = []
        
        for word in words:
            # Add word to current line
            current_line.append(word)
            
            # Check width
            width = get_text_width(' '.join(current_line), font)
            
            if width > max_width:
                if len(current_line) == 1:
                    # Single word too long - have to keep it
                    lines.append(current_line[0])
                    current_line = []
                else:
                    # Remove word and add line
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        # Add remaining line
        if current_line:
            lines.append(' '.join(current_line))
        
        # Add paragraph break (except after last paragraph)
        if paragraph != paragraphs[-1]:
            lines.append('')
    
    return lines

def get_text_width(text: str, font) -> int:
    """Get width of text with given font."""
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
    except:
        return font.getlength(text)

def get_text_height(text: str, font) -> int:
    """Get height of text with given font."""
    try:
        bbox = font.getbbox(text)
        return bbox[3] - bbox[1]
    except:
        return font.size

def calculate_text_height(lines: List[str], font) -> int:
    """Calculate total height of all lines."""
    total = 0
    for line in lines:
        if not line.strip():
            # Paragraph break - add less space
            total += int(font.size * 0.8)
        else:
            # Normal line with spacing
            height = get_text_height(line, font)
            total += int(height * 1.2)
    return total
