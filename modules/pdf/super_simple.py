"""
Super Simple PDF Creator
----------------------
Just takes images and puts them in a PDF. Nothing else.
Fixed for proper scaling to prevent layout errors.
"""
import os
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak
from PIL import Image as PILImage

logger = logging.getLogger(__name__)

def create_storybook_pdf(title, child_name, story_scenes, image_paths, output_path):
    """Just takes images and puts them in a PDF. That's it."""
    
    logger.info(f"Creating PDF with {len(image_paths)} images")
    
    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF document with letter size (more compatible than A4)
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=letter,
        title=title,
        author=f"Storybook for {child_name}",
        rightMargin=36,  # 0.5 inch margins
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # Get available page size (accounting for margins)
    page_width = doc.width
    page_height = doc.height
    
    # Add a safety margin to prevent layout errors
    safe_width = page_width * 0.95  # 95% of available width
    safe_height = page_height * 0.95  # 95% of available height
    
    # Build content - just images, one per page
    content = []
    
    for i, image_path in enumerate(image_paths):
        if os.path.exists(image_path):
            try:
                # Get image size
                img = PILImage.open(image_path)
                img_width, img_height = img.size
                
                # Calculate scaling to fit safely within page
                width_ratio = safe_width / img_width
                height_ratio = safe_height / img_height
                ratio = min(width_ratio, height_ratio)
                
                # Calculate new dimensions
                new_width = img_width * ratio
                new_height = img_height * ratio
                
                logger.info(f"Image {i+1}: Original size {img_width}x{img_height}, scaled to {new_width:.1f}x{new_height:.1f}")
                
                # Add to PDF
                img_obj = Image(image_path, width=new_width, height=new_height)
                content.append(img_obj)
                
                # Add page break after each image except the last one
                if i < len(image_paths) - 1:
                    content.append(PageBreak())
                    
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {str(e)}")
        else:
            logger.warning(f"Image not found: {image_path}")
    
    # Build PDF
    try:
        doc.build(content)
        logger.info(f"PDF successfully created at {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating PDF: {str(e)}")
        # Try with even smaller scaling if we get a layout error
        if "LayoutError" in str(e) or "too large on page" in str(e):
            logger.info("Trying with reduced image sizes...")
            return create_fallback_pdf(title, child_name, story_scenes, image_paths, output_path)
        raise

def create_fallback_pdf(title, child_name, story_scenes, image_paths, output_path):
    """Fallback method with extra-small images if normal method fails."""
    
    # Create PDF document with letter size and larger margins
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=letter,
        title=title,
        author=f"Storybook for {child_name}",
        rightMargin=50,  # Larger margins
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    # Get available page size (accounting for margins)
    page_width = doc.width
    page_height = doc.height
    
    # Add an extra safety margin
    safe_width = page_width * 0.8  # Only 80% of available width
    safe_height = page_height * 0.8  # Only 80% of available height
    
    # Build content - just images, one per page with extra small sizing
    content = []
    
    for i, image_path in enumerate(image_paths):
        if os.path.exists(image_path):
            try:
                # Get image size
                img = PILImage.open(image_path)
                img_width, img_height = img.size
                
                # Calculate scaling to fit safely within page
                width_ratio = safe_width / img_width
                height_ratio = safe_height / img_height
                ratio = min(width_ratio, height_ratio)
                
                # Calculate new dimensions
                new_width = img_width * ratio
                new_height = img_height * ratio
                
                logger.info(f"Fallback mode - Image {i+1}: scaled to {new_width:.1f}x{new_height:.1f}")
                
                # Add to PDF
                img_obj = Image(image_path, width=new_width, height=new_height)
                content.append(img_obj)
                
                # Add page break after each image except the last one
                if i < len(image_paths) - 1:
                    content.append(PageBreak())
                    
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {str(e)}")
        else:
            logger.warning(f"Image not found: {image_path}")
    
    # Build PDF with the smaller images
    doc.build(content)
    logger.info(f"Fallback PDF successfully created at {output_path}")
    return output_path
