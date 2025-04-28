"""
PDF generation service for the Storybook application.
Creates PDF files from storybook images.
"""
import os
import logging
import uuid
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

def generate_storybook_pdf(title, image_paths, output_path, child_name):
    """
    Generate a PDF file from a list of image paths.
    
    Args:
        title: Title of the storybook
        image_paths: List of paths to images
        output_path: Path to save the PDF
        child_name: Child's name for personalization
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create the PDF canvas
        c = canvas.Canvas(output_path, pagesize=letter)
        
        # Set document information
        c.setTitle(title)
        c.setAuthor("Storybook Generator")
        c.setSubject(f"A storybook for {child_name}")
        
        # Get page dimensions
        page_width, page_height = letter
        
        # Create cover page
        c.setFont("Helvetica-Bold", 36)
        title_width = c.stringWidth(title, "Helvetica-Bold", 36)
        title_x = (page_width - title_width) / 2
        title_y = page_height - 200
        c.drawString(title_x, title_y, title)
        
        c.setFont("Helvetica", 24)
        subtitle = "A personalized storybook"
        subtitle_width = c.stringWidth(subtitle, "Helvetica", 24)
        subtitle_x = (page_width - subtitle_width) / 2
        subtitle_y = title_y - 50
        c.drawString(subtitle_x, subtitle_y, subtitle)
        
        # Add each image as a page
        for i, image_path in enumerate(image_paths):
            if i > 0:  # Skip first page (already created cover)
                c.showPage()
            
            try:
                # Check if image exists
                if not os.path.exists(image_path):
                    logger.warning(f"Image not found: {image_path}")
                    continue
                
                # Open image and get dimensions
                img = Image.open(image_path)
                img_width, img_height = img.size
                
                # Calculate scaling to fit on page
                width_ratio = (page_width - 50) / img_width  # 25px margin on each side
                height_ratio = (page_height - 100) / img_height  # 50px margin top/bottom
                ratio = min(width_ratio, height_ratio)
                
                # Calculate new dimensions
                new_width = img_width * ratio
                new_height = img_height * ratio
                
                # Calculate centered position
                x = (page_width - new_width) / 2
                y = (page_height - new_height) / 2
                
                # Draw the image
                c.drawImage(image_path, x, y, width=new_width, height=new_height)
                
                # Add page number and attribution (except for cover)
                if i > 0:
                    c.setFont("Helvetica", 10)
                    # Page number
                    c.drawString(page_width - 50, 30, str(i))
                    # Attribution
                    c.setFont("Helvetica-Italic", 8)
                    c.drawString(30, 30, "Storybook Generator POC - Made with ❤️ by Nikhil")
            except Exception as e:
                logger.error(f"Error adding image to PDF: {str(e)}")
                continue
        
        # Save the PDF
        c.save()
        logger.info(f"PDF created successfully at {output_path}")
        return True
        
    except Exception as e:
        logger.exception(f"Error creating PDF: {str(e)}")
        return False
