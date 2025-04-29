#!/usr/bin/env python
"""
Storybook Generator POC - Main Flask Application
-------------------------------------------
A Proof of Concept web application that generates personalized children's storybooks
with AI-generated text and illustrations.

Made with ❤️ by Nikhil
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from datetime import datetime

# Import services
from modules.story.generator import generate_story
from modules.image.improved_generator import generate_illustration
from modules.image.improved_background import generate_background
from modules.image.final_overlay import create_text_overlay
from modules.pdf.super_simple import create_storybook_pdf
from utils.session import get_session_data, save_session_data
from utils.helpers import ensure_directories, allowed_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_' + str(uuid.uuid4()))

# Add basename filter for templates
@app.template_filter('basename')
def basename_filter(path):
    return os.path.basename(path) if path else ''

# Configure file paths
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'images')
PDF_FOLDER = os.path.join(STATIC_FOLDER, 'pdfs')
REFERENCE_FOLDER = os.path.join(STATIC_FOLDER, 'references')

# Ensure directories exist
ensure_directories([UPLOAD_FOLDER, PDF_FOLDER, REFERENCE_FOLDER])

@app.route('/')
def index():
    """Render the main input form."""
    return render_template('index.html')

@app.route('/api/generate-story', methods=['POST'])
def api_generate_story():
    """Generate story based on form input."""
    try:
        # Create a unique session ID
        session_id = str(uuid.uuid4())
        
        # Get form data
        child_name = request.form.get('childName')
        theme = request.form.get('theme')
        traits = request.form.get('traits')
        api_key = request.form.get('apiKey')
        illustration_quality = request.form.get('illustrationQuality', 'high')
        background_quality = request.form.get('backgroundQuality', 'medium')
        
        # Validate inputs
        if not all([child_name, theme, traits, api_key]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Process reference image if provided
        reference_image_path = None
        if 'referenceImage' in request.files:
            file = request.files['referenceImage']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{session_id}_{file.filename}")
                reference_image_path = os.path.join(REFERENCE_FOLDER, filename)
                file.save(reference_image_path)
        
        # Generate story
        story_scenes = generate_story(
            child_name=child_name,
            theme=theme,
            traits=traits,
            api_key=api_key
        )
        
        # Create a background image for the story
        background_path = generate_background(
            theme=theme,
            child_name=child_name,
            api_key=api_key,
            quality=background_quality,
            size="1024x1536",  # Match portrait orientation of illustrations
            output_dir=UPLOAD_FOLDER,
            session_id=session_id
        )
        
        # Save session data
        session_data = {
            'child_name': child_name,
            'theme': theme,
            'traits': traits,
            'story_scenes': story_scenes,
            'reference_image': reference_image_path,
            'background_image': background_path,
            'illustration_quality': illustration_quality,
            'background_quality': background_quality,
            'images': {},
            'created_at': datetime.now().isoformat()
        }
        
        save_session_data(session_id, session_data)
        
        # Return data to frontend
        return jsonify({
            'sessionId': session_id,
            'scenes': story_scenes
        })
        
    except Exception as e:
        logger.exception("Error generating story")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-illustration', methods=['POST'])
def api_generate_illustration():
    """Generate illustration for a story scene."""
    try:
        data = request.get_json()
        
        session_id = data.get('sessionId')
        scene_index = data.get('sceneIndex')
        api_key = data.get('apiKey')
        
        # Validate inputs
        if not all([session_id, api_key]) or scene_index is None:
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Get session data
        session_data = get_session_data(session_id)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404
        
        # Get story details
        child_name = session_data.get('child_name')
        story_scenes = session_data.get('story_scenes')
        reference_image_path = session_data.get('reference_image')
        background_image = session_data.get('background_image')
        illustration_quality = session_data.get('illustration_quality', 'high')
        
        # Validate scene index
        if scene_index < 0 or scene_index >= len(story_scenes):
            return jsonify({"error": "Invalid scene index"}), 400
        
        # Get scene text
        scene = story_scenes[scene_index]
        
        # Generate illustration
        illustration_path = generate_illustration(
            prompt=scene,
            session_id=session_id,
            scene_index=scene_index,
            child_name=child_name,
            reference_image_path=reference_image_path,
            api_key=api_key,
            quality=illustration_quality,
            output_dir=UPLOAD_FOLDER
        )
        
        # Create text overlay
        text_overlay_path = create_text_overlay(
            text=scene,
            background_image_path=background_image,
            session_id=session_id,
            scene_index=scene_index,
            output_dir=UPLOAD_FOLDER
        )
        
        # Update session data
        session_data['images'][str(scene_index)] = {
            'illustration': illustration_path,
            'text_overlay': text_overlay_path
        }
        save_session_data(session_id, session_data)
        
        # Return paths to frontend
        return jsonify({
            'illustrationPath': f"/static/images/{os.path.basename(illustration_path)}",
            'textOverlayPath': f"/static/images/{os.path.basename(text_overlay_path)}"
        })
        
    except Exception as e:
        logger.exception("Error generating illustration")
        return jsonify({"error": str(e)}), 500

@app.route('/api/create-pdf', methods=['POST'])
def api_create_pdf():
    """Create a PDF storybook from generated content."""
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        
        if not session_id:
            return jsonify({"error": "Missing session ID"}), 400
        
        # Get session data
        session_data = get_session_data(session_id)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404
        
        # Extract needed data
        child_name = session_data.get('child_name')
        theme = session_data.get('theme')
        story_scenes = session_data.get('story_scenes')
        images = session_data.get('images', {})
        
        # Prepare image paths in correct order
        image_paths = []
        for i in range(len(story_scenes)):
            scene_images = images.get(str(i), {})
            if 'illustration' in scene_images:
                image_paths.append(scene_images['illustration'])
            if 'text_overlay' in scene_images:
                image_paths.append(scene_images['text_overlay'])
        
        # Generate PDF
        pdf_filename = f"storybook_{session_id}.pdf"
        pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
        
        create_storybook_pdf(
            title=f"{child_name}'s {theme} Adventure",
            child_name=child_name,
            story_scenes=story_scenes,
            image_paths=image_paths,
            output_path=pdf_path
        )
        
        # Return PDF path
        return jsonify({
            'pdfPath': f"/static/pdfs/{pdf_filename}",
            'downloadUrl': f"/download-pdf/{pdf_filename}"
        })
        
    except Exception as e:
        logger.exception("Error creating PDF")
        return jsonify({"error": str(e)}), 500

@app.route('/download-pdf/<filename>')
def download_pdf(filename):
    """Download a generated PDF."""
    return send_from_directory(PDF_FOLDER, filename, as_attachment=True)

@app.route('/view-storybook/<session_id>')
def view_storybook(session_id):
    """View the generated storybook."""
    session_data = get_session_data(session_id)
    if not session_data:
        return redirect(url_for('index'))
    
    return render_template('storybook.html', 
                          session_id=session_id,
                          data=session_data,
                          os=os)  # Add os module to template context

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
