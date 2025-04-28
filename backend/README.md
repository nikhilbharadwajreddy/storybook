# Storybook Application Backend

This is the backend for the Storybook application, which generates personalized story prompts and illustrations for children using OpenAI's GPT and GPT Image models.

## New Modular Structure

The codebase has been reorganized into a more maintainable modular structure:

```
/backend
  /api            # API routes and controllers
    - app.py      # Main Flask application
    
  /services       # Business logic services
    /image        # Image generation
      - service.py     # Image service (GPT Image only)
      - processing.py  # Image processing utilities
    
    /text         # Text generation
      - service.py     # Text generation service
      - parser.py      # Response parsing utilities
    
  /utils          # Utility functions
    - common.py   # Common utilities
    - cache.py    # Caching functionality
  
  /templates      # Prompt templates
  /cache          # Cache storage
  /reference_images # Uploaded reference images
  
  - run.py        # Application runner
  - requirements.txt
```

## GPT Image Focus

The application has been streamlined to exclusively use OpenAI's `gpt-image-1` model for image generation, which provides superior results for children's book illustrations. DALL-E code has been removed for simplicity.

## Running the Application

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python run.py
   ```

3. Access the application at http://127.0.0.1:5000

## Features

- Generate custom story prompts based on a child's name, theme, and personal traits
- Create high-quality illustrations using OpenAI's GPT Image model
- Support for reference images to personalize the illustrations
- Image caching to avoid regenerating identical images
- Cost tracking for API usage

## API Key

This application requires an OpenAI API key with access to GPT-4 and GPT Image. You'll need to provide your own API key when using the application.
