"""
PDF Creator Module
---------------
Creates a PDF storybook from generated content.
"""
import os
import logging
from typing import List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.pdfgen import canvas
from PIL import Image

logger = logging.getLogger(__name__)

def create_storybook_pdf(
    title: str,
    child_name: str,
    story_scenes: List[str],
    image_paths: List[str],
    output_path: str,
    author: Optional[str] = None,
    page_size: tuple = A4,
    margin: int = 50
) -> str:
    """
    Create a PDF storybook with text and images.
    
    Args:
        title: Title of the storybook
        child_name: Name of the child
        story_scenes: List of story scene texts
        image_paths: List of paths to images
        output_path: Path to save the PDF
        author: Author name (optional)
        page_size: Page size (default: A4)
        margin: Page margin in points
        
    Returns:
        Path to the generated PDF
    """
    logger.info(f"Creating storybook PDF: {title}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Set up the document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        rightMargin=margin,
        leftMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    
    # Create a custom style for story text
    story_style = ParagraphStyle(
        'StoryText',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=10
    )
    
    # Create document content
    content = []
    
    # Add title page
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 20))
    content.append(Paragraph(f"A personalized story for {child_name}", normal_style))
    
    if author:
        content.append(Spacer(1, 10))
        content.append(Paragraph(f"Created by {author}", normal_style))
    
    content.append(PageBreak())
    
    # Add story content - alternate between images and text
    # Ensure we don't exceed the available images or scenes
    for i, scene in enumerate(story_scenes):
        # Add scene title
        scene_title = f"Scene {i+1}"
        content.append(Paragraph(scene_title, styles['Heading2']))
        content.append(Spacer(1, 10))
        
        # Add scene text
        content.append(Paragraph(scene, story_style))
        content.append(Spacer(1, 20))
        
        # Find the corresponding image(s) for this scene
        # Assuming images are named with scene indices
        scene_images = [path for path in image_paths if f"scene_{i}" in path]
        
        # Add illustration image if available
        illustration = next((img for img in scene_images if "illustration" in img), None)
        if illustration and os.path.exists(illustration):
            try:
                img = process_image_for_pdf(illustration, max_width=doc.width)
                content.append(img)
                content.append(Spacer(1, 10))
            except Exception as e:
                logger.error(f"Error processing image {illustration}: {str(e)}")
        
        # Add page break after each scene except the last one
        if i < len(story_scenes) - 1:
            content.append(PageBreak())
    
    # Build the PDF
    try:
        doc.build(content)
        logger.info(f"PDF successfully created at {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating PDF: {str(e)}")
        raise

def process_image_for_pdf(image_path: str, max_width: int = 500, max_height: int = 700) -> RLImage:
    """
    Process an image for inclusion in a PDF.
    
    Args:
        image_path: Path to the image
        max_width: Maximum width in the PDF
        max_height: Maximum height in the PDF
        
    Returns:
        ReportLab Image object ready for inclusion in PDF
    """
    # Open the image to get its size
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    # Calculate scaling to fit within max dimensions while preserving aspect ratio
    width_ratio = max_width / img_width
    height_ratio = max_height / img_height
    scale_ratio = min(width_ratio, height_ratio)
    
    new_width = img_width * scale_ratio
    new_height = img_height * scale_ratio
    
    # Create ReportLab image with calculated dimensions
    pdf_image = RLImage(image_path, width=new_width, height=new_height)
    
    return pdf_image
