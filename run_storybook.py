
import os
import sys
import subprocess
import webbrowser
import time
import logging
import argparse
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def get_base_dir():
    """Get the base directory of the application."""
    return os.path.dirname(os.path.abspath(__file__))

def create_required_directories():
    """Create required directories if they don't exist."""
    base_dir = get_base_dir()
    
    directories = [
        os.path.join(base_dir, "static", "images"),
        os.path.join(base_dir, "static", "pdfs"),
        os.path.join(base_dir, "backend", "cache"),
        os.path.join(base_dir, "backend", "reference_images")
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")

def copy_turn_js_files():
    """Copy turn.js files to static/js directory if needed."""
    base_dir = get_base_dir()
    source_dir = os.path.join(base_dir, "turn.js-master")
    target_dir = os.path.join(base_dir, "static", "js")
    
    # Check if source directory exists
    if not os.path.exists(source_dir):
        logger.warning("turn.js-master directory not found. Skipping copy.")
        return
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy turn.min.js if it doesn't exist in target
    source_file = os.path.join(source_dir, "turn.min.js")
    target_file = os.path.join(target_dir, "turn.min.js")
    
    if os.path.exists(source_file) and not os.path.exists(target_file):
        try:
            shutil.copy2(source_file, target_file)
            logger.info(f"Copied turn.min.js to {target_dir}")
        except Exception as e:
            logger.error(f"Failed to copy turn.min.js: {e}")

def clean_cache(max_age_days=30):
    """Clean old cache files."""
    try:
        cache_dir = os.path.join(get_base_dir(), "backend", "cache")
        if not os.path.exists(cache_dir):
            return
        
        # Import cache utility
        sys.path.append(os.path.join(get_base_dir(), "backend"))
        from utils.cache import clear_cache
        
        # Clear old cache files
        cleared = clear_cache(cache_dir, max_age_days)
        logger.info(f"Cleared {cleared} old cache files")
    except Exception as e:
        logger.error(f"Error cleaning cache: {e}")

def main():
    """Main function to run the application."""
    parser = argparse.ArgumentParser(description="Run the Storybook Application")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser window")
    parser.add_argument("--clean-cache", action="store_true", help="Clean old cache files")
    args = parser.parse_args()
    
    logger.info("Starting Storybook Application...")
    
    # Clean cache if requested
    if args.clean_cache:
        clean_cache()
    
    # Create required directories
    create_required_directories()
    
    # Copy turn.js files if needed
    copy_turn_js_files()
    
    # Get the base directory
    base_dir = get_base_dir()
    
    # Path to the backend run.py
    backend_path = os.path.join(base_dir, "backend", "run.py")
    
    if not os.path.exists(backend_path):
        logger.error(f"Backend script not found at {backend_path}")
        sys.exit(1)
    
    # Start the Flask server
    logger.info("Starting backend server...")
    
    # Use Python executable from current environment
    python_exe = sys.executable
    
    try:
        # Launch browser after a short delay (unless disabled)
        if not args.no_browser:
            def open_browser():
                time.sleep(2)  # Wait for server to start
                webbrowser.open(f"http://127.0.0.1:{args.port}")
                logger.info("Opening application in browser...")
            
            import threading
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
        
        # Start the Flask server (this will block until the server is stopped)
        result = subprocess.run(
            [python_exe, backend_path, "--port", str(args.port)],
            cwd=os.path.join(base_dir, "backend")
        )
        
        return result.returncode
        
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user.")
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
