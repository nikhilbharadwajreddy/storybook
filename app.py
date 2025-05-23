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
from utils.user_tracker import save_user_data, get_all_users
from utils.fallback_init import initialize_all

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

# Initialize fallbacks and required resources
initialize_all()

@app.route('/')
def index():
    """Redirect to user details form or render main input form if coming from there."""
    if 'user_verified' in session:
        return render_template('index.html')
    return render_template('user_details.html')

@app.route('/submit-user-details', methods=['POST'])
def submit_user_details():
    """Process user details and redirect to main app."""
    try:
        # Get form data
        user_name = request.form.get('userName')
        user_email = request.form.get('userEmail')
        
        # Validate inputs
        if not all([user_name, user_email]):
            return render_template('user_details.html', error="Please provide both name and email")
        
        # Save user data
        save_user_data(user_name, user_email)
        
        # Mark user as verified in session
        session['user_verified'] = True
        session['user_name'] = user_name
        session['user_email'] = user_email
        
        # Redirect to main app
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.exception("Error processing user details")
        return render_template('user_details.html', error=str(e))

@app.route('/admin/users')
def admin_users():
    """Admin endpoint to view all user data.
    
    This is a simple endpoint that shows all users who have accessed the application.
    In a production environment, you would add proper authentication.
    """
    # Simple admin password protection (replace with proper auth in production)
    admin_key = request.args.get('key')
    if not admin_key or admin_key != 'admin123':
        return "Unauthorized", 401
    
    # Get all users
    users_data = get_all_users()
    
    # Format timestamps for display
    users = []
    for user in users_data:
        # Clone the user data
        formatted_user = user.copy()
        
        # Format the timestamp
        timestamp = user.get('timestamp', '')
        if timestamp:
            try:
                # Parse ISO format and convert to more readable format
                dt = datetime.fromisoformat(timestamp)
                formatted_user['formatted_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                formatted_user['formatted_time'] = timestamp
        else:
            formatted_user['formatted_time'] = 'Unknown'
            
        users.append(formatted_user)
    
    # Render template
    return render_template('admin_users.html', users=users)

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
        
        # Log request details for debugging
        logger.info(f"Generating illustration for session {session_id}, scene {scene_index}")
        logger.info(f"Using quality: {illustration_quality}")
        if reference_image_path:
            logger.info(f"Using reference image: {reference_image_path}")
        
        # Generate illustration
        try:
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
        except Exception as e:
            logger.exception(f"Error in illustration generation: {str(e)}")
            return jsonify({"error": f"Illustration generation failed: {str(e)}"}), 500
        
        # Create text overlay
        try:
            text_overlay_path = create_text_overlay(
                text=scene,
                background_image_path=background_image,
                session_id=session_id,
                scene_index=scene_index,
                output_dir=UPLOAD_FOLDER
            )
        except Exception as e:
            logger.exception(f"Error in text overlay creation: {str(e)}")
            return jsonify({"error": f"Text overlay creation failed: {str(e)}"}), 500
        
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
        # We need to ensure a specific sequence: illustration followed by text overlay for each scene
        image_paths = []
        
        # First, make sure we have a consistent ordering of scene indices
        scene_indices = sorted([int(idx) for idx in images.keys()])
        
        for i in scene_indices:
            scene_images = images.get(str(i), {})
            
            # Add illustration first, then text overlay
            # Only add if both exist to maintain proper pairing
            if 'illustration' in scene_images and 'text_overlay' in scene_images:
                image_paths.append(scene_images['illustration'])
                image_paths.append(scene_images['text_overlay'])
        
        logger.info(f"Adding {len(image_paths)} images to PDF in alternating illustration/text order")
        
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
