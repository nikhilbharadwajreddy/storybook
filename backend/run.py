#!/usr/bin/env python
"""
Backend Server Runner
--------------------

Script to run the Flask backend server for the Storybook application.
"""
import os
import sys
import argparse
import logging
from api.app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the Flask backend server."""
    parser = argparse.ArgumentParser(description="Run the Storybook Backend Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    logger.info(f"Starting Storybook Backend on {args.host}:{args.port}")
    
    # Directory paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    static_folder = os.path.join(os.path.dirname(base_dir), "static")
    
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Static folder: {static_folder}")
    
    # Start the Flask server
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == "__main__":
    main()
