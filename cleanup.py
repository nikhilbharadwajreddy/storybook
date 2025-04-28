#!/usr/bin/env python
"""
Storybook Project Cleanup Script
--------------------------------

This script cleans up the storybook project by:
1. Removing unnecessary files (.DS_Store, __pycache__, etc.)
2. Organizing images and cache files
3. Creating a proper project structure
"""
import os
import shutil
import glob
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def remove_files(base_dir, patterns, dry_run=False):
    """Remove files matching the specified patterns."""
    removed_count = 0
    
    for pattern in patterns:
        for file_path in glob.glob(os.path.join(base_dir, "**", pattern), recursive=True):
            if os.path.exists(file_path):
                logger.info(f"Removing: {file_path}")
                if not dry_run:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                removed_count += 1
    
    return removed_count

def ensure_directories(base_dir, directories, dry_run=False):
    """Ensure directories exist."""
    created_count = 0
    
    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        if not os.path.exists(dir_path):
            logger.info(f"Creating directory: {dir_path}")
            if not dry_run:
                os.makedirs(dir_path, exist_ok=True)
            created_count += 1
    
    return created_count

def move_turnjs_files(base_dir, dry_run=False):
    """Move turn.js files to static/js directory."""
    moved_count = 0
    
    source_dir = os.path.join(base_dir, "turn.js-master")
    target_dir = os.path.join(base_dir, "static", "js")
    
    if not os.path.exists(source_dir):
        logger.warning("turn.js-master directory not found")
        return 0
    
    if not os.path.exists(target_dir):
        logger.info(f"Creating directory: {target_dir}")
        if not dry_run:
            os.makedirs(target_dir, exist_ok=True)
    
    # Files to move
    files = ["turn.min.js"]
    
    for file in files:
        source_file = os.path.join(source_dir, file)
        target_file = os.path.join(target_dir, file)
        
        if os.path.exists(source_file) and not os.path.exists(target_file):
            logger.info(f"Moving: {source_file} -> {target_file}")
            if not dry_run:
                shutil.copy2(source_file, target_file)
            moved_count += 1
    
    return moved_count

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Clean up the Storybook project")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.dirname(__file__))
    logger.info(f"Cleaning up project in: {base_dir}")
    logger.info(f"Dry run: {args.dry_run}")
    
    # 1. Remove unnecessary files
    patterns = [
        ".DS_Store",
        "__pycache__",
        "*.pyc",
        ".vscode",
        ".idea",
        "*.bak"
    ]
    
    removed = remove_files(base_dir, patterns, args.dry_run)
    logger.info(f"Removed {removed} unnecessary files/directories")
    
    # 2. Ensure directories exist
    directories = [
        os.path.join("static", "images"),
        os.path.join("static", "js"),
        os.path.join("static", "css"),
        os.path.join("static", "pdfs"),
        os.path.join("backend", "cache"),
        os.path.join("backend", "reference_images")
    ]
    
    created = ensure_directories(base_dir, directories, args.dry_run)
    logger.info(f"Created {created} directories")
    
    # 3. Move turn.js files
    moved = move_turnjs_files(base_dir, args.dry_run)
    logger.info(f"Moved {moved} turn.js files")
    
    logger.info("Cleanup completed!")

if __name__ == "__main__":
    main()
