"""
Text-on-image rendering and PDF generation service for the Storybook application.
"""
import os
import uuid
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

def render_text_on_backdrop(
    text,
    backdrop_path,
    upload_folder,
    font_size=36,
    font_color=(255, 255, 255),
    shadow_color=(0, 0, 0),
    shadow_offset=2,
    padding=40
):
    """
    Render text on the backdrop image with custom styling.
    
    Args:
        text: Text to render on the image
        backdrop_path: Path to the backdrop image
        upload_folder: Where to save the generated image
        font_size: Text font size
        font_color: RGB tuple for text color
        shadow_color: RGB tuple for text shadow color
        shadow_offset: Offset pixels for the shadow effect
        padding: Padding from edges
        
    Returns:
        Path to the generated image
    """
    try:
        # Convert backdrop_path to full path if it's a relative URL
        if backdrop_path.startswith("/static/images/"):
            backdrop_filename = backdrop_path.split("/")[-1]
            full_backdrop_path = os.path.join(upload_folder, backdrop_filename)
        else:
            full_backdrop_path = backdrop_path
            
        # Open the backdrop image
        img = Image.open(full_backdrop_path)
        width, height = img.size
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Try to use a fancy font if available, otherwise use default
        try:
            # Try to find a nice font - adjust path based on your system
            font_path = "/System/Library/Fonts/Supplemental/Comic Sans MS.ttf"  # Default Comic Sans for children's book
            if not os.path.exists(font_path):
                # Fallbacks
                possible_fonts = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                    "C:/Windows/Fonts/comic.ttf",  # Windows Comic Sans
                    "C:/Windows/Fonts/Arial.ttf",   # Windows Arial
                ]
                
                for possible_font in possible_fonts:
                    if os.path.exists(possible_font):
                        font_path = possible_font
                        break
            
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            # Fallback to default font
            font = ImageFont.load_default()
            font_size = 24  # Smaller size for default font
            
        # Wrap text to fit the image width
        wrapped_text = wrap_text(text, font, width - (padding * 2))
        
        # Calculate position to center the text
        text_lines = wrapped_text.split('\n')
        total_text_height = len(text_lines) * (font_size + 10)  # Add line spacing
        
        # Position slightly above center for better visual balance
        y_position = (height - total_text_height) // 2 - 50
        
        # Create semi-transparent overlay for better text readability
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Calculate text block position and size
        text_block_y = max(y_position - padding, 0)
        text_block_height = total_text_height + (padding * 2)
        
        # Draw semi-transparent rectangle behind text
        overlay_draw.rectangle(
            [(padding//2, text_block_y), (width - padding//2, text_block_y + text_block_height)],
            fill=(0, 0, 0, 80)  # Black with 80/255 alpha (semi-transparent)
        )
        
        # Composite the overlay onto the original image
        img = Image.alpha_composite(img.convert('RGBA'), overlay)
        
        # Draw each line of text with shadow for better readability
        current_y = y_position
        for line in text_lines:
            # Get line width for centering
            text_width = draw.textlength(line, font=font)
            x_position = (width - text_width) // 2
            
            # Draw shadow first
            draw = ImageDraw.Draw(img)
            draw.text(
                (x_position + shadow_offset, current_y + shadow_offset),
                line,
                font=font,
                fill=shadow_color
            )
            
            # Draw actual text
            draw.text(
                (x_position, current_y),
                line,
                font=font,
                fill=font_color
            )
            
            current_y += font_size + 10  # Move to next line with spacing
        
        # Create unique filename for the text image
        output_filename = f"text_image_{uuid.uuid4()}.png"
        output_path = os.path.join(upload_folder, output_filename)
        
        # Save the image
        img = img.convert('RGB')  # Convert back to RGB for saving as PNG
        img.save(output_path)
        
        return {
            "image_path": f"/static/images/{output_filename}",
            "full_path": output_path,
            "success": True
        }
        
    except Exception as e:
        logger.exception(f"Error rendering text on image: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def wrap_text(text, font, max_width):
    """
    Wrap text to fit within a given width.
    
    Args:
        text: Text string to wrap
        font: Font object to calculate text width
        max_width: Maximum width in pixels
        
    Returns:
        Wrapped text with newline characters
    """
    words = text.split()
    wrapped_lines = []
    current_line = []
    
    for word in words:
        # Add the word to the current line
        current_line.append(word)
        
        # Check if the line is too long with the new word
        line_width = ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(
            ' '.join(current_line),
            font=font
        )
        
        if line_width > max_width:
            # If too long, remove the last word
            if len(current_line) > 1:
                current_line.pop()
                wrapped_lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # If it's just one word but too long, keep it anyway
                wrapped_lines.append(' '.join(current_line))
                current_line = []
    
    # Add the remaining line if it exists
    if current_line:
        wrapped_lines.append(' '.join(current_line))
    
    return '\n'.join(wrapped_lines)

def generate_storybook_pdf(
    pages,
    output_folder,
    title="Storybook",
    author="Story Generator"
):
    """
    Generate a PDF from multiple storybook pages.
    
    Args:
        pages: List of image paths to include in the PDF
        output_folder: Where to save the PDF
        title: Title of the PDF
        author: Author of the PDF
        
    Returns:
        Path to the generated PDF
    """
    try:
        # Create a unique filename for the PDF
        pdf_filename = f"storybook_{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(output_folder, pdf_filename)
        
        # Create a PDF with landscape orientation
        c = canvas.Canvas(pdf_path, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Set PDF metadata
        c.setTitle(title)
        c.setAuthor(author)
        
        # Add each page to the PDF
        for i, page_path in enumerate(pages):
            # Check if the path is a URL or local path
            if page_path.startswith("/static/"):
                # Convert to full path
                filename = page_path.split("/")[-1]
                full_path = os.path.join(output_folder, filename)
            else:
                full_path = page_path
                
            # Open the image
            img = Image.open(full_path)
            
            # If this is not the first page, add a new page
            if i > 0:
                c.showPage()
                
            # Calculate scaling to fit on the page while maintaining aspect ratio
            img_width, img_height = img.size
            scale_factor = min(width / img_width, height / img_height)
            new_width = img_width * scale_factor
            new_height = img_height * scale_factor
            
            # Calculate position to center the image on the page
            x_pos = (width - new_width) / 2
            y_pos = (height - new_height) / 2
            
            # Add the image to the PDF
            c.drawImage(full_path, x_pos, y_pos, width=new_width, height=new_height)
        
        # Save the PDF
        c.save()
        
        return {
            "pdf_path": f"/static/images/{pdf_filename}",
            "full_path": pdf_path,
            "success": True
        }
        
    except Exception as e:
        logger.exception(f"Error generating PDF: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
