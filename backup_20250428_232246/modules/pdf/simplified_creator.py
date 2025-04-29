"""
Simplified PDF Creator Module
--------------------------
Creates a simplified PDF storybook from generated content.
Focus on just including the images in order without complex layout.
"""
import os
import logging
from typing import List
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, PageBreak
from PIL import Image

logger = logging.getLogger(__name__)

def create_storybook_pdf(
    title: str,
    child_name: str,
    story_scenes: List[str],  # We'll keep this parameter for compatibility
    image_paths: List[str],
    output_path: str
) -> str:
    """
    Create a simplified PDF storybook that just includes the images in order.
    
    Args:
        title: Title of the storybook (used for PDF metadata)
        child_name: Name of the child (used for PDF metadata)
        story_scenes: List of story scenes (not used in simplified version)
        image_paths: List of paths to images to include
        output_path: Path to save the PDF
        
    Returns:
        Path to the generated PDF
    """
    logger.info(f"Creating simplified storybook PDF: {title}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Set up the document with landscape orientation for better image viewing
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        title=title,
        author=f"Storybook for {child_name}"
    )
    
    # Create document content - just images
    content = []
    
    # Process each image
    for i, image_path in enumerate(image_paths):
        if os.path.exists(image_path):
            try:
                # Add the image to the PDF at appropriate size
                img = process_image_for_pdf(image_path)
                content.append(img)
                
                # Add page break after each image except the last one
                if i < len(image_paths) - 1:
                    content.append(PageBreak())
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {str(e)}")
        else:
            logger.warning(f"Image not found: {image_path}")
    
    # Build the PDF
    try:
        doc.build(content)
        logger.info(f"PDF successfully created at {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating PDF: {str(e)}")
        raise

def process_image_for_pdf(image_path: str) -> RLImage:
    """
    Process an image for inclusion in a PDF, scaling it to fit the page.
    
    Args:
        image_path: Path to the image
        
    Returns:
        ReportLab Image object ready for inclusion in PDF
    """
    # Open the image to get its size
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    # Get page size (A4 dimensions)
    page_width, page_height = A4
    
    # Allow for margins (20 points on each side)
    margin = 40
    max_width = page_width - margin
    max_height = page_height - margin
    
    # Calculate scaling to fit within page dimensions while preserving aspect ratio
    width_ratio = max_width / img_width
    height_ratio = max_height / img_height
    scale_ratio = min(width_ratio, height_ratio)
    
    new_width = img_width * scale_ratio
    new_height = img_height * scale_ratio
    
    # Create ReportLab image with calculated dimensions
    pdf_image = RLImage(image_path, width=new_width, height=new_height)
    
    return pdf_image
