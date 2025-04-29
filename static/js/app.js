/**
 * Storybook Generator - Frontend JavaScript
 * -----------------------------------------
 * Handles user interactions and API calls for the storybook generator.
 */

// Store session data
let sessionId = null;
let scenes = [];

// Wait for DOM to be loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Storybook Generator initialized');
    
    // Initialize form
    const storyForm = document.getElementById('storyForm');
    if (storyForm) {
        storyForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Initialize create PDF button
    const createPdfBtn = document.getElementById('createPdfBtn');
    if (createPdfBtn) {
        createPdfBtn.addEventListener('click', handleCreatePdf);
    }
});

/**
 * Handle form submission to generate a story
 * @param {Event} e - Form submit event
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Get form data
    const form = e.target;
    const formData = new FormData(form);
    
    // Basic validation
    const childName = formData.get('childName').trim();
    const theme = formData.get('theme').trim();
    const traits = formData.get('traits').trim();
    const apiKey = formData.get('apiKey').trim();
    
    if (!childName || !theme || !traits || !apiKey) {
        showError('Please fill in all required fields');
        return;
    }
    
    try {
        // Show loading state
        showLoading('Generating your story...');
        hideError();
        
        // Call API to generate story
        const response = await fetch('/api/generate-story', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Story generated:', data);
        
        // Store session data
        sessionId = data.sessionId;
        scenes = data.scenes;
        
        // Display scenes
        displayScenes(scenes);
        
        // Hide loading and scroll to results
        hideLoading();
        document.getElementById('storyContainer').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error generating story:', error);
        showError(error.message || 'Failed to generate story');
        hideLoading();
    }
}

/**
 * Display story scenes in the UI
 * @param {Array} scenes - Array of scene texts
 */
function displayScenes(scenes) {
    const container = document.getElementById('scenesList');
    container.innerHTML = '';
    
    scenes.forEach((scene, index) => {
        const sceneCard = document.createElement('div');
        sceneCard.className = 'scene-card';
        
        sceneCard.innerHTML = `
            <div class="scene-header">
                <h3>Scene ${index + 1}</h3>
            </div>
            <div class="scene-content">
                <p class="scene-text">${scene}</p>
                <div id="scene-${index}-images" class="scene-images">
                    <div class="image-container">
                        <p>Click "Generate Illustration" to create an image for this scene.</p>
                    </div>
                </div>
            </div>
            <div class="scene-actions">
                <button type="button" onclick="generateIllustration(${index})">Generate Illustration</button>
            </div>
        `;
        
        container.appendChild(sceneCard);
    });
    
    // Show story container
    document.getElementById('storyContainer').classList.remove('hidden');
}

/**
 * Generate an illustration for a specific scene
 * @param {number} sceneIndex - Index of the scene
 */
async function generateIllustration(sceneIndex) {
    if (!sessionId) {
        showError('No active session. Please generate a story first.');
        return;
    }
    
    const apiKey = document.getElementById('apiKey').value.trim();
    if (!apiKey) {
        showError('API key is required to generate illustrations');
        return;
    }
    
    // Get image container
    const imageContainer = document.getElementById(`scene-${sceneIndex}-images`);
    const actionButton = document.querySelector(`.scene-actions button[onclick="generateIllustration(${sceneIndex})"]`);
    
    // Show loading state
    imageContainer.innerHTML = '<div class="spinner"></div><p>Generating illustration...</p>';
    actionButton.disabled = true;
    
    try {
        // Call API to generate illustration
        const response = await fetch('/api/generate-illustration', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: sessionId,
                sceneIndex: sceneIndex,
                apiKey: apiKey
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Illustration generated:', data);
        
        // Display images
        imageContainer.innerHTML = `
            <div class="image-container">
                <h4>Illustration</h4>
                <img src="${data.illustrationPath}" alt="Scene ${sceneIndex + 1} Illustration">
            </div>
            <div class="image-container">
                <h4>Text Overlay</h4>
                <img src="${data.textOverlayPath}" alt="Scene ${sceneIndex + 1} Text">
            </div>
        `;
        
        // Update button
        actionButton.textContent = 'Regenerate Illustration';
        actionButton.disabled = false;
        
    } catch (error) {
        console.error('Error generating illustration:', error);
        imageContainer.innerHTML = `<p class="error">Error: ${error.message || 'Failed to generate illustration'}</p>`;
        actionButton.disabled = false;
    }
}

/**
 * Handle creating a PDF storybook
 */
async function handleCreatePdf() {
    if (!sessionId) {
        showError('No active session. Please generate a story first.');
        return;
    }
    
    try {
        showLoading('Creating your storybook PDF...');
        
        // Call API to create PDF
        const response = await fetch('/api/create-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: sessionId
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('PDF created:', data);
        
        // Redirect to storybook view
        window.location.href = '/view-storybook/' + sessionId;
        
    } catch (error) {
        console.error('Error creating PDF:', error);
        showError(error.message || 'Failed to create PDF');
        hideLoading();
    }
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }
}

/**
 * Hide error message
 */
function hideError() {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.classList.add('hidden');
    }
}

/**
 * Show loading indicator
 * @param {string} message - Loading message
 */
function showLoading(message = 'Loading...') {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const loadingMessage = document.getElementById('loadingMessage');
    
    if (loadingMessage) {
        loadingMessage.textContent = message;
    }
    
    if (loadingIndicator) {
        loadingIndicator.classList.remove('hidden');
    }
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    if (loadingIndicator) {
        loadingIndicator.classList.add('hidden');
    }
}
