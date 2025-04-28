/**
 * Storybook Generator POC - Frontend Script
 * Made with ❤️ by Nikhil
 * 
 * Handles only UI interactions and API calls to Python backend.
 * All core functionality is implemented in the backend.
 */

// Constants
const API_BASE_URL = '/api';

// Global state - minimal, just for UI tracking
let sessionId = null;

/**
 * Initialize application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Storybook UI');
    
    // Initialize form
    initForm();
    
    // Load available models
    loadModels();
    
    // Test API connection
    testApiConnection();
});

/**
 * Initialize form and event listeners
 */
function initForm() {
    // Get form element
    const storyForm = document.getElementById('storyForm');
    if (storyForm) {
        storyForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Image model change event for quality selector
    const imageModel = document.getElementById('imageModel');
    if (imageModel) {
        imageModel.addEventListener('change', toggleQualitySelector);
    }
    
    // Refresh models button
    const refreshBtn = document.getElementById('refreshModelsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadModels);
    }
    
    // Create book button
    document.getElementById('createBookBtn')?.addEventListener('click', handleCreateBook);
    
    // Back to prompts button
    document.getElementById('backToPromptBtn')?.addEventListener('click', () => {
        document.getElementById('storybookContainer').classList.add('hidden');
        document.getElementById('promptsContainer').classList.remove('hidden');
        document.getElementById('createBookContainer').classList.remove('hidden');
    });
}

/**
 * Toggle quality selector based on selected image model
 */
function toggleQualitySelector() {
    const imageModel = document.getElementById('imageModel').value;
    const qualityContainer = document.getElementById('qualityContainer');
    
    if (imageModel === 'gpt-image-1') {
        qualityContainer.style.display = 'block';
    } else {
        qualityContainer.style.display = 'none';
    }
}

/**
 * Test API connection
 */
async function testApiConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/test`);
        
        if (!response.ok) {
            throw new Error(`API returned status ${response.status}`);
        }
        
        console.log('API connection successful');
    } catch (error) {
        console.error('API connection failed:', error);
        showError('Cannot connect to the API server. Please make sure it is running.');
    }
}

/**
 * Load available AI models from the API
 */
async function loadModels() {
    try {
        showLoading('Loading available models...');
        
        const response = await fetch(`${API_BASE_URL}/models`);
        if (!response.ok) {
            throw new Error(`Failed to load models: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Available models:', data);
        
        // Populate text models
        const textModelSelect = document.getElementById('textModel');
        if (textModelSelect) {
            // Clear existing options (except placeholder)
            while (textModelSelect.options.length > 1) {
                textModelSelect.remove(1);
            }
            
            // Add new options
            data.text.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                textModelSelect.appendChild(option);
            });
        }
        
        // Populate image models
        const imageModelSelect = document.getElementById('imageModel');
        if (imageModelSelect) {
            // Clear existing options (except placeholder)
            while (imageModelSelect.options.length > 1) {
                imageModelSelect.remove(1);
            }
            
            // Add new options
            data.image.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                imageModelSelect.appendChild(option);
            });
        }
        
        hideLoading();
        
    } catch (error) {
        console.error('Error loading models:', error);
        showError(`Failed to load models: ${error.message}`);
        hideLoading();
    }
}

/**
 * Handle form submission
 * @param {Event} e - Form submit event
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Simple UI validation
    const form = e.target;
    const childName = form.childName.value.trim();
    const theme = form.theme.value.trim();
    const traits = form.traits.value.trim();
    const apiKey = form.apiKey.value.trim();
    const textModel = form.textModel.value;
    
    if (!childName) {
        showError("Please enter the child's name");
        return;
    }
    
    if (!theme) {
        showError("Please enter a story theme");
        return;
    }
    
    if (!traits) {
        showError("Please enter traits about the child");
        return;
    }
    
    if (!apiKey) {
        showError("Please enter your OpenAI API key");
        return;
    }
    
    if (!textModel) {
        showError("Please select a text generation model");
        return;
    }
    
    try {
        showLoading('Generating story prompts...');
        hideError();
        
        // Create FormData for file upload
        const formData = new FormData(form);
        
        // Send request to backend
        const response = await fetch(`${API_BASE_URL}/generate-prompts`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Generated prompts:', data);
        
        // Store session ID
        sessionId = data.sessionId;
        
        // Display prompts
        displayPrompts(data.prompts);
        
        // Fetch cost info
        fetchCosts();
        
        hideLoading();
        
        // Show create book button
        document.getElementById('createBookContainer').classList.remove('hidden');
        
        // Scroll to prompts section
        document.getElementById('promptsContainer').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error generating prompts:', error);
        showError(error.message || 'Failed to generate prompts');
        hideLoading();
    }
}

/**
 * Display prompts in the UI
 * @param {Array} prompts - Array of prompts
 */
function displayPrompts(prompts) {
    const container = document.getElementById('promptsContainer');
    container.innerHTML = '<h2>Generated Story Prompts</h2>';
    
    prompts.forEach((prompt, index) => {
        const promptText = typeof prompt === 'string' ? prompt : prompt.prompt;
        
        const card = document.createElement('div');
        card.className = 'prompt-card';
        
        card.innerHTML = `
            <div class="prompt-text">
                <strong>Prompt ${index + 1}:</strong> ${promptText}
            </div>
            <div id="image-container-${index}" class="image-container">
                <p>Click "Generate Image" to create an illustration for this prompt.</p>
            </div>
            <div class="image-actions">
                <button id="generate-image-${index}" onclick="generateImage(${index})">Generate Image</button>
            </div>
        `;
        
        container.appendChild(card);
    });
    
    container.classList.remove('hidden');
}

/**
 * Generate image for a prompt
 * @param {number} promptIndex - Index of the prompt
 */
window.generateImage = async function(promptIndex) {
    if (!sessionId) {
        showError('No active session. Please generate prompts first.');
        return;
    }
    
    const apiKey = document.getElementById('apiKey').value.trim();
    if (!apiKey) {
        showError('API key is required to generate images');
        return;
    }
    
    // Get container and button
    const imageContainer = document.getElementById(`image-container-${promptIndex}`);
    const generateBtn = document.getElementById(`generate-image-${promptIndex}`);
    
    // Show loading state
    imageContainer.innerHTML = '<div class="spinner"></div><p>Generating image and text page...</p>';
    generateBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate-image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: sessionId,
                promptIndex: promptIndex,
                apiKey: apiKey
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Generated images:', data);
        
        // Display images
        imageContainer.innerHTML = `
            <div class="image-set">
                <div class="image-item">
                    <h4>Story Image</h4>
                    <img src="${data.imagePath}" alt="Generated illustration" class="prompt-image">
                </div>
                <div class="image-item">
                    <h4>Text Page</h4>
                    <img src="${data.textPath}" alt="Text with magical background" class="prompt-image">
                </div>
            </div>
            <p class="info-text">Both images will be included in your storybook!</p>
        `;
        
        // Update button
        generateBtn.textContent = 'Regenerate Images';
        generateBtn.disabled = false;
        
        // Update costs
        fetchCosts();
        
    } catch (error) {
        console.error('Error generating image:', error);
        imageContainer.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        generateBtn.disabled = false;
    }
}

/**
 * Handle create book button click
 */
async function handleCreateBook() {
    if (!sessionId) {
        showError('No active session. Please generate prompts first.');
        return;
    }
    
    try {
        showLoading('Creating your storybook...');
        
        const response = await fetch(`${API_BASE_URL}/create-storybook`, {
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
        console.log('Storybook created:', data);
        
        // Hide prompts container
        document.getElementById('promptsContainer').classList.add('hidden');
        document.getElementById('createBookContainer').classList.add('hidden');
        
        // Show preview container
        const previewContainer = document.getElementById('preview-container');
        previewContainer.innerHTML = `
            <h2>Your Storybook</h2>
            <div class="storybook-download">
                <p>Your storybook PDF is ready!</p>
                <a href="${data.downloadUrl}" class="download-button" target="_blank">Download Storybook PDF</a>
            </div>
            <div class="preview-controls">
                <button id="back-to-prompts-btn" class="secondary-button">Back to Prompts</button>
            </div>
        `;
        
        previewContainer.classList.remove('hidden');
        
        // Add event listener for back button
        document.getElementById('back-to-prompts-btn')?.addEventListener('click', () => {
            previewContainer.classList.add('hidden');
            document.getElementById('promptsContainer').classList.remove('hidden');
            document.getElementById('createBookContainer').classList.remove('hidden');
        });
        
        hideLoading();
        
    } catch (error) {
        console.error('Error creating storybook:', error);
        showError(error.message || 'Failed to create storybook');
        hideLoading();
    }
}

/**
 * Fetch costs for the current session
 */
async function fetchCosts() {
    if (!sessionId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/cost/${sessionId}`);
        
        if (!response.ok) {
            console.error('Failed to fetch costs:', response.statusText);
            return;
        }
        
        const data = await response.json();
        console.log('Session costs:', data);
        
        // Update cost display
        updateCostDisplay(data);
        
    } catch (error) {
        console.error('Error fetching costs:', error);
    }
}

/**
 * Update cost display in UI
 * @param {Object} costs - Cost data
 */
function updateCostDisplay(costs) {
    // Simple pricing calculations (rough estimates)
    let textCost = 0;
    let imageCost = 0;
    
    // Calculate text cost
    const textData = costs.text_generation || {};
    if (textData.model === 'gpt-4') {
        textCost = ((textData.input_tokens || 0) / 1000 * 0.03) + 
                   ((textData.output_tokens || 0) / 1000 * 0.06);
    } else if (textData.model === 'gpt-4-turbo') {
        textCost = ((textData.input_tokens || 0) / 1000 * 0.01) + 
                   ((textData.output_tokens || 0) / 1000 * 0.03);
    } else {
        textCost = ((textData.input_tokens || 0) / 1000 * 0.0015) + 
                   ((textData.output_tokens || 0) / 1000 * 0.002);
    }
    
    // Calculate image cost
    const imageData = costs.image_generation || [];
    imageCost = imageData.reduce((total, img) => {
        if (img.model === 'gpt-image-1') {
            // Fixed cost per quality
            const qualityCosts = {
                'low': 0.003,
                'medium': 0.006,
                'high': 0.009
            };
            return total + (qualityCosts[img.quality] || 0.009);
        } else {
            // Default DALL-E cost
            return total + 0.04;
        }
    }, 0);
    
    // Update UI
    document.getElementById('textCost').textContent = '$' + textCost.toFixed(4);
    document.getElementById('imageCost').textContent = '$' + imageCost.toFixed(4);
    document.getElementById('totalCost').textContent = '$' + (textCost + imageCost).toFixed(4);
    
    // Show cost display
    document.getElementById('costDisplay').classList.remove('hidden');
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

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }
}

/**
 * Hide error message
 */
function hideError() {
    const errorMessage = document.getElementById('errorMessage');
    
    if (errorMessage) {
        errorMessage.classList.add('hidden');
    }
}
