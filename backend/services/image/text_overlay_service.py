"""
Text overlay service for the Storybook application.
Creates images with text overlaid on backgrounds.
"""
import os
import logging
import uuid
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
from utils.common import ensure_directory_exists

logger = logging.getLogger(__name__)

def generate_text_image(
    prompt_text,
    backdrop_image_path,
    child_name,
    theme,
    upload_folder=None,
    session_id=None,
    prompt_index=None,
    output_filename=None
):
    """
    Generate an image with text overlaid on a magical backdrop.
    
    Args:
        prompt_text: Text to overlay
        backdrop_image_path: Path to backdrop image
        child_name: Name of the child for personalization
        theme: Story theme
        upload_folder: Path to upload directory
        session_id: Session identifier
        prompt_index: Index of the prompt
        output_filename: Specific filename to use
        
    Returns:
        Dictionary with image path and metadata
    """
    try:
        # Determine filename and path
        if session_id and prompt_index is not None:
            # Use sequential numbering: prompt_index * 2 + 2 for text images
            text_number = prompt_index * 2 + 2
            
            # Create session folder if needed
            ensure_directory_exists(os.path.join(upload_folder, session_id))
            
            # Use sequential numbered filename
            image_filename = f"{session_id}/{text_number}_text.png"
        elif output_filename:
            # Use specified filename
            image_filename = output_filename
            
            # Ensure any parent directories exist
            if '/' in image_filename:
                dir_path = os.path.join(upload_folder, os.path.dirname(image_filename))
                os.makedirs(dir_path, exist_ok=True)
        else:
            # Fallback to UUID if no session/index provided
            image_filename = f"text_{uuid.uuid4()}.png"
        
        # Full path for the output image
        image_path = os.path.join(upload_folder, image_filename)
        
        # Check backdrop dimensions if possible
        portrait_dimensions = None
        if backdrop_image_path and os.path.exists(backdrop_image_path):
            try:
                backdrop_img = Image.open(backdrop_image_path)
                # Use the same aspect ratio as the backdrop, but ensure portrait orientation
                w, h = backdrop_img.size
                if h > w:  # Already portrait
                    portrait_dimensions = (w, h)
                else:  # Convert to portrait by swapping dimensions
                    portrait_dimensions = (h, w)
                logger.info(f"Using backdrop dimensions for consistency: {portrait_dimensions}")
            except Exception as img_err:
                logger.warning(f"Could not read backdrop image dimensions: {str(img_err)}")
        
        # Generate text image with proper portrait dimensions
        success = create_text_image(
            text=prompt_text,
            backdrop_path=backdrop_image_path,
            output_path=image_path,
            child_name=child_name,
            theme=theme,
            dimensions=portrait_dimensions
        )
        
        if not success:
            raise Exception("Failed to create text image")
        
        # Return result
        return {
            "image_path": f"/static/images/{image_filename}",
            "from_cache": False,
            "filename": image_filename
        }
        
    except Exception as e:
        logger.exception(f"Error generating text overlay image: {str(e)}")
        raise Exception(f"Failed to generate text overlay: {str(e)}")

def create_text_image(text, backdrop_path, output_path, child_name, theme, dimensions=None):
    """
    Create an image with text overlaid on a beautiful background.
    
    Args:
        text: Text to overlay
        backdrop_path: Path to backdrop image
        output_path: Path to save the output image
        child_name: Child's name for personalization
        theme: Story theme
        dimensions: Optional (width, height) tuple to override default dimensions
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    def get_background_brightness(image, x, y, width, height):
        """Calculate average brightness of a region"""
        region = image.crop((x, y, x+width, y+height))
        avg_color = region.convert('L').resize((1, 1)).getpixel((0, 0))
        return avg_color
    try:
        # Create a new portrait-oriented image with ideal storybook dimensions
        if dimensions:
            width, height = dimensions
            logger.info(f"Using provided dimensions: {width}x{height}")
        else:
            width, height = 1024, 1536  # Default portrait orientation (tall, not wide)
            logger.info(f"Using default dimensions: {width}x{height}")
        
        # Force portrait orientation - ensure height is greater than width
        if width > height:
            # Swap dimensions if they're in landscape orientation
            logger.warning(f"Dimensions were in landscape format ({width}x{height}), swapping to ensure portrait orientation")
            width, height = height, width
            logger.info(f"Swapped to portrait: {width}x{height}")
        
        # Create a new blank image with gradient background
        img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Create theme-based gradient background
        theme_colors = get_theme_colors(theme)
        
        # Draw gradient background
        for y in range(height):
            # Calculate ratio of current position
            r = y / height
            
            # Calculate color using smooth interpolation
            if r < 0.4:  # Top 40%
                ratio = r / 0.4
                r_val = int(theme_colors['bg_top'][0] * (1 - ratio) + theme_colors['bg_middle'][0] * ratio)
                g_val = int(theme_colors['bg_top'][1] * (1 - ratio) + theme_colors['bg_middle'][1] * ratio)
                b_val = int(theme_colors['bg_top'][2] * (1 - ratio) + theme_colors['bg_middle'][2] * ratio)
            else:  # Bottom 60%
                ratio = (r - 0.4) / 0.6
                r_val = int(theme_colors['bg_middle'][0] * (1 - ratio) + theme_colors['bg_bottom'][0] * ratio)
                g_val = int(theme_colors['bg_middle'][1] * (1 - ratio) + theme_colors['bg_bottom'][1] * ratio)
                b_val = int(theme_colors['bg_middle'][2] * (1 - ratio) + theme_colors['bg_bottom'][2] * ratio)
            
            # Draw horizontal line with this color
            draw.line([(0, y), (width, y)], fill=(r_val, g_val, b_val))
        
        # Add background texture/pattern
        add_background_texture(img, draw, theme, theme_colors)
        
        # Create a WHITE overlay for text area to ensure readability
        overlay = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Draw a semi-transparent white rectangle in the center for text readability
        text_box_width = int(width * 0.8)
        text_box_height = int(height * 0.7)  # Increased height for better text coverage
        text_box_x = (width - text_box_width) // 2
        text_box_y = (height - text_box_height) // 2
        overlay_draw.rectangle((text_box_x, text_box_y, text_box_x + text_box_width, text_box_y + text_box_height), 
                              fill=(255, 255, 255, 210))  # White with 80% opacity for better contrast
        
        # Apply the overlay
        img = Image.alpha_composite(img, overlay)
        
        # Try to load a nice font, fall back to default if not available
        try:
            title_font = ImageFont.truetype("Arial Bold", 72)
            body_font = ImageFont.truetype("Arial", 48)
        except:
            # Use default font
            title_font = ImageFont.load_default().font_variant(size=72)
            body_font = ImageFont.load_default().font_variant(size=48)
        
        # Draw title
        title_text = f"{child_name}'s {theme.title()} Adventure"
        
        # Get title dimensions
        try:
            title_bbox = title_font.getbbox(title_text)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            title_y = height // 8  # Position at top eighth
        except Exception:
            # Fallback method
            title_width = len(title_text) * 30  # Rough estimate
            title_x = (width - title_width) // 2
            title_y = height // 8
        
        # Get background brightness for the title area
        title_area_brightness = get_background_brightness(img, 
                                                      max(0, title_x - 20), 
                                                      max(0, title_y - 20),
                                                      min(width, title_width + 40),
                                                      min(100, title_font.getbbox('Ay')[3] + 40))
        
        # Draw the title with a glow effect, adapting to background
        draw_text_with_glow(draw, title_x, title_y, title_text, title_font, (20, 20, 80), title_area_brightness)
        
        # Wrap and draw the main text
        margin = int(width * 0.15)  # 15% margin
        text_box_width = width - (2 * margin)
        
        # Wrap the text
        wrapped_text = text_wrap(text, body_font, text_box_width)
        
        # Calculate line height
        try:
            ascent, descent = body_font.getmetrics()
            line_height = (ascent + descent) * 1.5  # 1.5 line spacing
        except Exception:
            # Fallback
            line_height = body_font.getbbox('hg')[3] * 1.5
        
        # Calculate total text height
        text_height = len(wrapped_text) * line_height
        
        # Position text in the center, below the title
        text_y = title_y + title_font.getbbox(title_text)[3] + 50
        
        # Draw each line of text
        for line in wrapped_text:
            # Center the line
            try:
                line_bbox = body_font.getbbox(line)
                line_width = line_bbox[2] - line_bbox[0]
            except Exception:
                line_width = len(line) * 20  # Rough estimate
            
            line_x = (width - line_width) // 2
            
            # Get background brightness for this line of text
            line_area_brightness = get_background_brightness(img,
                                                          max(0, line_x - 10),
                                                          max(0, text_y - 5),
                                                          min(width, line_width + 20),
                                                          min(line_height, body_font.getbbox('Ay')[3] + 10))
            
            # Draw the text with a glow effect, adapting to background
            draw_text_with_glow(draw, line_x, text_y, line, body_font, (40, 40, 40), line_area_brightness)
            
            # Move to the next line
            text_y += line_height
        
        # Save the image
        img = img.convert('RGB')  # Convert back to RGB for saving as PNG
        img.save(output_path)
        
        return True
        
    except Exception as e:
        logger.exception(f"Error creating text image: {str(e)}")
        return False

def create_text_image_from_scratch(text, output_path, child_name, theme):
    """
    Create a text image from scratch when no backdrop is available.
    
    Args:
        text: Text to display
        output_path: Path to save the image
        child_name: Child's name
        theme: Story theme
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create a new image with A4 dimensions
        width, height = 1748, 2480  # ~A4 at 300 DPI
        img = Image.new('RGB', (width, height), (240, 240, 255))  # Light blue background
        draw = ImageDraw.Draw(img)
        
        # Try to load a nice font, fall back to default if not available
        try:
            title_font = ImageFont.truetype("Arial Bold", 72)
            body_font = ImageFont.truetype("Arial", 48)
        except:
            # Use default font
            title_font = ImageFont.load_default().font_variant(size=72)
            body_font = ImageFont.load_default().font_variant(size=48)
        
        # Draw title
        title_text = f"{child_name}'s {theme.title()} Adventure"
        
        # Get title dimensions
        try:
            title_bbox = title_font.getbbox(title_text)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            title_y = height // 8  # Position at top eighth
        except Exception:
            # Fallback method
            title_width = len(title_text) * 30  # Rough estimate
            title_x = (width - title_width) // 2
            title_y = height // 8
        
        # Draw the title
        draw.text((title_x, title_y), title_text, font=title_font, fill=(20, 20, 80))
        
        # Wrap and draw the main text
        margin = int(width * 0.15)  # 15% margin
        text_box_width = width - (2 * margin)
        
        # Wrap the text
        wrapped_text = text_wrap(text, body_font, text_box_width)
        
        # Calculate line height
        try:
            ascent, descent = body_font.getmetrics()
            line_height = (ascent + descent) * 1.5  # 1.5 line spacing
        except Exception:
            # Fallback
            line_height = body_font.getbbox('hg')[3] * 1.5
        
        # Position text in the center, below the title
        text_y = title_y + title_font.getbbox(title_text)[3] + 50
        
        # Draw each line of text
        for line in wrapped_text:
            # Center the line
            try:
                line_bbox = body_font.getbbox(line)
                line_width = line_bbox[2] - line_bbox[0]
            except Exception:
                line_width = len(line) * 20  # Rough estimate
            
            line_x = (width - line_width) // 2
            
            # Draw the text
            draw.text((line_x, text_y), line, font=body_font, fill=(40, 40, 40))
            
            # Move to the next line
            text_y += line_height
        
        # Save the image
        img.save(output_path)
        
        return True
        
    except Exception as e:
        logger.exception(f"Error creating text image from scratch: {str(e)}")
        return False

def get_background_brightness(img, x, y, width, height):
    """
    Calculate average brightness of a region in the image.
    
    Args:
        img: PIL Image object
        x, y: Top-left corner of region
        width, height: Dimensions of region
        
    Returns:
        float: Average brightness (0-255)
    """
    try:
        # Convert image to luminance
        region = img.crop((x, y, x+width, y+height))
        grayscale = region.convert('L')
        histogram = grayscale.histogram()
        
        # Calculate weighted average brightness
        total_pixels = sum(histogram)
        brightness = sum(i * histogram[i] for i in range(256)) / total_pixels if total_pixels > 0 else 128
        
        return brightness
    except Exception as e:
        logger.error(f"Error calculating background brightness: {e}")
        return 128  # Default mid-brightness

def draw_text_with_glow(draw, x, y, text, font, color, background_brightness=None):
    """
    Draw text with a strong glow effect for better readability.
    
    Args:
        draw: PIL ImageDraw object
        x, y: Text position
        text: Text to draw
        font: PIL ImageFont object
        color: Text color (RGB tuple)
        background_brightness: Optional brightness value to adapt colors
    """
    # Determine if background is dark or light
    is_dark_background = False
    if background_brightness is not None:
        is_dark_background = background_brightness < 128
    
    # Choose outline colors based on background
    outer_outline_color = (255, 255, 255, 220) if is_dark_background else (0, 0, 0, 220)  # White on dark, black on light
    inner_outline_color = (255, 255, 255, 240) if is_dark_background else (0, 0, 0, 240)  # More opaque
    
    # Thicker outer outline
    offsets = [
        (3, 0), (3, 1), (3, 2), (2, 3), (1, 3), (0, 3), (-1, 3), (-2, 3),
        (-3, 2), (-3, 1), (-3, 0), (-3, -1), (-3, -2), (-2, -3), (-1, -3), (0, -3),
        (1, -3), (2, -3), (3, -2), (3, -1)
    ]
    
    # Outer outline
    for offset_x, offset_y in offsets:
        draw.text((x + offset_x, y + offset_y), text, font=font, fill=outer_outline_color)
    
    # Inner outline (thicker)
    inner_offsets = [
        (2, 0), (2, 1), (1, 2), (0, 2), (-1, 2), (-2, 1),
        (-2, 0), (-2, -1), (-1, -2), (0, -2), (1, -2), (2, -1),
        (1, 1), (-1, 1), (1, -1), (-1, -1), (1, 0), (0, 1), (-1, 0), (0, -1)
    ]
    
    for offset_x, offset_y in inner_offsets:
        draw.text((x + offset_x, y + offset_y), text, font=font, fill=inner_outline_color)
    
    # Adapt the main text color based on background brightness if needed
    adjusted_color = color
    if background_brightness is not None:
        if is_dark_background and sum(color) / 3 < 128:  # If dark text on dark background
            adjusted_color = (250, 250, 250)  # Use white text
        elif not is_dark_background and sum(color) / 3 > 128:  # If light text on light background
            adjusted_color = (20, 20, 60)  # Use dark text
    
    # Draw the main text
    draw.text((x, y), text, font=font, fill=adjusted_color)

def text_wrap(text, font, max_width):
    """
    Wrap text to fit within a given width.
    
    Args:
        text: Text to wrap
        font: Font to use for measuring text
        max_width: Maximum width in pixels
        
    Returns:
        list: Wrapped text lines
    """
    words = text.split()
    wrapped_lines = []
    current_line = []
    
    for word in words:
        # Add the word to the current line
        current_line.append(word)
        
        # Check if the line is now too wide
        line = ' '.join(current_line)
        
        # Get line width
        try:
            line_bbox = font.getbbox(line)
            line_width = line_bbox[2] - line_bbox[0]
        except Exception:
            # Fallback estimation
            line_width = len(line) * (font.size / 2 if hasattr(font, 'size') else 20)
        
        if line_width > max_width:
            # If adding this word makes the line too wide, 
            # remove it and add the current line to wrapped_lines
            if len(current_line) > 1:
                current_line.pop()
                wrapped_lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # If a single word is too wide, keep it and move on
                wrapped_lines.append(line)
                current_line = []
    
    # Add the last line
    if current_line:
        wrapped_lines.append(' '.join(current_line))
    
    return wrapped_lines
