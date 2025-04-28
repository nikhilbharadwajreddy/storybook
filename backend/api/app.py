"""
Flask backend for the Story Prompts Generator application.
Handles all core processing and business logic.
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
import uuid
import json
from werkzeug.utils import secure_filename
from PIL import Image

# Import services
from services.text.service import generate_prompts
from services.image.service import generate_image
from services.image.text_overlay_service import generate_text_image
from services.image.backdrop_service import generate_story_backdrop
from services.pdf.pdf_service import generate_storybook_pdf
from utils.common import allowed_file, get_prompt_text, ensure_directory_exists
from utils.cache import check_cache, save_to_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'), static_url_path='/static')
CORS(app)  # Enable CORS for all routes

# Setup necessary directories
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images')
PDF_FOLDER = os.path.join(BASE_DIR, 'static', 'pdfs')
CACHE_FOLDER = os.path.join(BASE_DIR, 'backend', 'cache')
REFERENCE_FOLDER = os.path.join(BASE_DIR, 'backend', 'reference_images')
TEMPLATES_FOLDER = os.path.join(BASE_DIR, 'backend', 'templates')

# Create directories if they don't exist
for directory in [UPLOAD_FOLDER, PDF_FOLDER, CACHE_FOLDER, REFERENCE_FOLDER]:
    os.makedirs(directory, exist_ok=True)

# Session data storage
session_data = {}

# Available models
AVAILABLE_MODELS = {
    "text": [
        {"id": "gpt-4", "name": "GPT-4"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (Fastest)"}
    ],
    "image": [
        {"id": "gpt-image-1", "name": "GPT Image (High Quality)"}
    ]
}

@app.route('/')
def index():
    """Serve the main index.html file."""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/test')
def test():
    """Test endpoint to verify API connectivity."""
    return jsonify({"status": "ok", "message": "API is running"})

@app.route('/api/models')
def models():
    """Return available OpenAI models."""
    logger.info("Models endpoint called")
    try:
        return jsonify(AVAILABLE_MODELS)
    except Exception as e:
        logger.exception(f"Error in models endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-prompts', methods=['POST'])
def api_generate_prompts():
    """Generate story prompts based on user input."""
    try:
        # Extract form data
        child_name = request.form.get('childName')
        theme = request.form.get('theme')
        num_prompts = int(request.form.get('numPrompts', 3))
        traits = request.form.get('traits')
        api_key = request.form.get('apiKey')
        text_model = request.form.get('textModel', 'gpt-4')
        
        # Validate inputs
        if not all([child_name, theme, traits, api_key, text_model]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Create a unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize session data
        session_data[session_id] = {
            "child_name": child_name,
            "theme": theme,
            "traits": traits,
            "images": {},
            "costs": {
                "text_generation": {},
                "image_generation": []
            }
        }
        
        # Process reference image if provided
        reference_image_path = None
        if 'referenceImage' in request.files:
            file = request.files['referenceImage']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                reference_image_path = os.path.join(REFERENCE_FOLDER, filename)
                file.save(reference_image_path)
                session_data[session_id]["reference_image"] = reference_image_path
        
        # Check cache first
        cache_key = f"{child_name}_{theme}_{num_prompts}_{traits}_{text_model}"
        cache_data = check_cache(cache_key, CACHE_FOLDER)
        
        if cache_data:
            logger.info(f"Cache hit for prompts with key: {cache_key}")
            prompts = cache_data.get("prompts", [])
            session_data[session_id]["prompts"] = prompts
            session_data[session_id]["costs"]["text_generation"] = cache_data.get("costs", {})
            from_cache = True
        else:
            # Generate new prompts
            result = generate_prompts(
                child_name=child_name,
                theme=theme,
                num_prompts=num_prompts,
                traits=traits,
                api_key=api_key,
                text_model=text_model,
                templates_folder=TEMPLATES_FOLDER,
                cache_folder=CACHE_FOLDER
            )
            
            prompts = result.get("prompts", [])
            costs = result.get("token_usage", {})
            
            # Store in session
            session_data[session_id]["prompts"] = prompts
            session_data[session_id]["costs"]["text_generation"] = costs
            
            # Save to cache
            cache_data = {
                "prompts": prompts,
                "costs": costs
            }
            save_to_cache(cache_key, cache_data, CACHE_FOLDER)
            from_cache = False
        
        # Generate backdrop image in the background
        try:
            # This will create the backdrop image and store it in the session
            generate_backdrop_for_session(session_id, api_key)
        except Exception as e:
            logger.error(f"Error generating backdrop: {str(e)}")
            # Continue even if backdrop generation fails
        
        # Return result
        return jsonify({
            "sessionId": session_id,
            "prompts": prompts,
            "fromCache": from_cache
        })
    
    except Exception as e:
        logger.exception("Error generating prompts")
        return jsonify({"error": str(e)}), 500

def generate_backdrop_for_session(session_id, api_key):
    """Generate a backdrop image for the session."""
    if session_id not in session_data:
        return
    
    session = session_data[session_id]
    theme = session.get("theme")
    child_name = session.get("child_name")
    traits = session.get("traits")
    reference_image_path = session.get("reference_image")
    
    # Generate backdrop image
    try:
        result = generate_story_backdrop(
            theme=theme,
            child_name=child_name,
            traits=traits,
            api_key=api_key,
            reference_image_path=reference_image_path,
            quality="high",
            size="1536x1024",
            templates_folder=TEMPLATES_FOLDER,
            upload_folder=UPLOAD_FOLDER,
            cache_folder=CACHE_FOLDER,
            session_id=session_id
        )
        
        # Store in session
        session_data[session_id]["backdrop_image"] = result.get("image_path")
        
        # Add to costs
        if "token_usage" in result:
            session_data[session_id]["costs"]["image_generation"].append(result["token_usage"])
            
        return result.get("image_path")
    except Exception as e:
        logger.exception(f"Error generating backdrop: {str(e)}")
        return None

@app.route('/api/generate-image', methods=['POST'])
def api_generate_image():
    """Generate images for a prompt."""
    try:
        data = request.get_json()
        
        session_id = data.get('sessionId')
        prompt_index = data.get('promptIndex')
        api_key = data.get('apiKey')
        
        # Validate inputs
        if not all([session_id, api_key]) or prompt_index is None:
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Check if session exists
        if session_id not in session_data:
            return jsonify({"error": "Session not found"}), 404
        
        # Get session data
        session = session_data[session_id]
        prompts = session.get("prompts", [])
        
        # Validate prompt index
        if prompt_index < 0 or prompt_index >= len(prompts):
            return jsonify({"error": "Invalid prompt index"}), 400
        
        # Get prompt
        prompt_data = prompts[prompt_index]
        
        # Generate images (story image and text image)
        result = generate_all_images_for_prompt(
            session_id=session_id,
            prompt_index=prompt_index,
            prompt_data=prompt_data,
            api_key=api_key
        )
        
        # Return image paths
        return jsonify(result)
    
    except Exception as e:
        logger.exception("Error generating images")
        return jsonify({"error": str(e)}), 500

def generate_all_images_for_prompt(session_id, prompt_index, prompt_data, api_key):
    """Generate both story image and text image for a prompt."""
    if session_id not in session_data:
        raise Exception("Session not found")
    
    session = session_data[session_id]
    child_name = session.get("child_name", "the child")
    theme = session.get("theme", "adventure")
    reference_image_path = session.get("reference_image")
    
    # Ensure backdrop exists
    backdrop_image = session.get("backdrop_image")
    if not backdrop_image:
        # Try to generate backdrop if missing
        backdrop_image = generate_backdrop_for_session(session_id, api_key)
        if not backdrop_image:
            raise Exception("Backdrop image not available")
    
    # Create session folder for images
    ensure_directory_exists(os.path.join(UPLOAD_FOLDER, session_id))
    
    # Generate story image (main illustration)
    story_result = generate_image(
        prompt_data=prompt_data,
        session_id=session_id,
        api_key=api_key,
        child_name=child_name,
        reference_image_path=reference_image_path,
        quality="high",
        size="1024x1536",
        templates_folder=TEMPLATES_FOLDER,
        upload_folder=UPLOAD_FOLDER,
        cache_folder=CACHE_FOLDER,
        prompt_index=prompt_index
    )
    
    # Extract prompt text for text image
    prompt_text = get_prompt_text(prompt_data)
    
    # Generate text image (text with magical background)
    text_result = generate_text_image(
        prompt_text=prompt_text,
        backdrop_image_path=backdrop_image,
        child_name=child_name,
        theme=theme,
        upload_folder=UPLOAD_FOLDER,
        session_id=session_id,
        prompt_index=prompt_index
    )
    
    # Store in session data
    session["images"][prompt_index] = {
        "story_image": story_result.get("image_path"),
        "text_image": text_result.get("image_path")
    }
    
    # Add to costs
    if "token_usage" in story_result:
        session["costs"]["image_generation"].append(story_result["token_usage"])
    
    # Return both paths
    return {
        "imagePath": story_result.get("image_path"),
        "textPath": text_result.get("image_path"),
        "fromCache": story_result.get("from_cache", False)
    }

@app.route('/api/create-storybook', methods=['POST'])
def api_create_storybook():
    """Create a complete storybook PDF."""
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        
        if not session_id:
            return jsonify({"error": "Missing session ID"}), 400
        
        # Check if session exists
        if session_id not in session_data:
            return jsonify({"error": "Session not found"}), 404
        
        # Create the PDF
        pdf_result = create_storybook_pdf(session_id)
        
        return jsonify({
            "pdfPath": pdf_result.get("pdf_path"),
            "downloadUrl": f"/api/download-pdf/{pdf_result.get('filename')}"
        })
    
    except Exception as e:
        logger.exception("Error creating storybook")
        return jsonify({"error": str(e)}), 500

def create_storybook_pdf(session_id):
    """Create a PDF storybook with all images."""
    if session_id not in session_data:
        raise Exception("Session not found")
    
    session = session_data[session_id]
    child_name = session.get("child_name", "the child")
    theme = session.get("theme", "adventure")
    
    # Create PDF filename
    pdf_filename = f"storybook_{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
    
    # Get all images for the storybook
    images = []
    
    # Add backdrop if available
    backdrop = session.get("backdrop_image")
    if backdrop:
        backdrop_path = backdrop.replace("/static/images/", "")
        images.append(os.path.join(UPLOAD_FOLDER, backdrop_path))
    
    # Add prompt images in order
    prompts = session.get("prompts", [])
    for i in range(len(prompts)):
        prompt_images = session.get("images", {}).get(i, {})
        
        # Add story image
        story_image = prompt_images.get("story_image")
        if story_image:
            story_path = story_image.replace("/static/images/", "")
            images.append(os.path.join(UPLOAD_FOLDER, story_path))
        
        # Add text image
        text_image = prompt_images.get("text_image")
        if text_image:
            text_path = text_image.replace("/static/images/", "")
            images.append(os.path.join(UPLOAD_FOLDER, text_path))
    
    # Generate PDF
    generate_storybook_pdf(
        title=f"{child_name}'s {theme} Adventure",
        image_paths=images,
        output_path=pdf_path,
        child_name=child_name
    )
    
    # Verify PDF was created
    if not os.path.exists(pdf_path):
        raise Exception("Failed to create PDF")
    
    return {
        "pdf_path": f"/static/pdfs/{pdf_filename}",
        "filename": pdf_filename
    }

@app.route('/api/download-pdf/<filename>', methods=['GET'])
def download_pdf(filename):
    """Download a generated PDF."""
    try:
        # Sanitize filename to prevent directory traversal
        safe_filename = secure_filename(filename)
        
        # Build complete path to the PDF
        pdf_path = os.path.join(PDF_FOLDER, safe_filename)
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found at: {pdf_path}")
            return jsonify({"error": "PDF file not found"}), 404
        
        # Return the file for download
        logger.info(f"Serving PDF file from: {pdf_path}")
        return send_from_directory(
            directory=PDF_FOLDER,
            path=safe_filename,
            as_attachment=True,
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.exception(f"Error downloading PDF: {str(e)}")
        return jsonify({"error": f"Failed to download PDF: {str(e)}"}), 500

@app.route('/api/cost/<session_id>')
def get_cost(session_id):
    """Get cost information for a session."""
    if session_id not in session_data:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify(session_data[session_id].get("costs", {
        "text_generation": {},
        "image_generation": []
    }))

@app.route('/api/session/<session_id>')
def get_session(session_id):
    """Get session details."""
    if session_id not in session_data:
        return jsonify({"error": "Session not found"}), 404
    
    # Return a sanitized version of the session data
    session = session_data[session_id]
    return jsonify({
        "childName": session.get("child_name", ""),
        "theme": session.get("theme", ""),
        "hasPrompts": bool(session.get("prompts", [])),
        "promptCount": len(session.get("prompts", [])),
        "hasBackdrop": bool(session.get("backdrop_image")),
        "generatedImages": list(session.get("images", {}).keys())
    })

if __name__ == '__main__':
    logger.info(f"Starting server with static folder: {app.static_folder}")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Cache folder: {CACHE_FOLDER}")
    logger.info(f"Templates folder: {TEMPLATES_FOLDER}")
    app.run(debug=True, host='0.0.0.0', port=5000)
