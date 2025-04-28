#!/usr/bin/env python
"""
Helper script to copy Turn.js files to the static/js directory
"""
import os
import shutil
import sys

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Source paths
    turnjs_source_dir = os.path.join(base_dir, 'turn.js-master')
    turnjs_min_source = os.path.join(turnjs_source_dir, 'turn.min.js')
    
    # Destination paths
    static_js_dir = os.path.join(base_dir, 'static', 'js')
    turnjs_min_dest = os.path.join(static_js_dir, 'turn.min.js')
    
    # Check if source exists
    if not os.path.exists(turnjs_source_dir):
        print(f"Error: Turn.js source directory not found at {turnjs_source_dir}")
        return 1
    
    if not os.path.exists(turnjs_min_source):
        print(f"Error: turn.min.js not found at {turnjs_min_source}")
        return 1
    
    # Ensure the destination directory exists
    os.makedirs(static_js_dir, exist_ok=True)
    
    # Copy the files
    print(f"Copying Turn.js from {turnjs_min_source} to {turnjs_min_dest}")
    shutil.copy2(turnjs_min_source, turnjs_min_dest)
    
    print("Turn.js files copied successfully.")
    
    # Update the index.html to reference local copy
    index_html_path = os.path.join(base_dir, 'index.html')
    if os.path.exists(index_html_path):
        print("Updating index.html...")
        with open(index_html_path, 'r') as f:
            content = f.read()
        
        # Check for path patterns in the script tag for Turn.js
        if '/turn.js-master/turn.min.js' in content:
            print("Adding static/js/turn.min.js as a fallback")
            # Add a fallback to the local copy if the Turn.js script fails to load
            updated_content = content.replace(
                '<!-- Fallback to CDN if local file fails -->',
                '<!-- Try local copy -->\\n    <script>\\n        if (typeof $.fn.turn === "undefined") {\\n            console.log("Loading local Turn.js copy");\\n            document.write(\'<script src="static/js/turn.min.js"><\\/script>\');\\n        }\\n    </script>\\n    <!-- Fallback to CDN if local file fails -->'
            )
            
            with open(index_html_path, 'w') as f:
                f.write(updated_content)
                
            print("index.html updated successfully.")
        else:
            print("No Turn.js script tag found in index.html, no updates made.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
