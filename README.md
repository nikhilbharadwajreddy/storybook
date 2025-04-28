# Storybook Generator POC

A web application that generates personalized children's storybooks with AI-generated text and illustrations.

Made with ❤️ by Nikhil

## Features

- Create personalized stories based on a child's name, theme, and traits
- Generate high-quality illustrations for each story scene
- Create beautifully formatted text pages with themed backgrounds
- Export to PDF for easy reading and printing
- Cache stories and images to reduce API costs

## Project Structure

```
storybook/
├── backend/                # Python backend processing
│   ├── api/                # Flask API endpoints
│   ├── services/           # Core services
│   │   ├── image/          # Image generation
│   │   ├── pdf/            # PDF creation
│   │   └── text/           # Text generation
│   ├── templates/          # Prompt templates
│   └── utils/              # Utility functions
├── static/                 # Frontend assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript
│   ├── images/             # Generated images
│   └── pdfs/               # Generated PDFs
├── cleanup.py              # Project cleanup utility
├── index.html              # Main HTML page
└── run_storybook.py        # Application runner
```

## Architecture

This application follows a backend-focused architecture:

- **Python Backend**: Handles all core processing and business logic
  - Text generation with OpenAI API
  - Image creation with OpenAI API
  - PDF generation
  - Session management and caching

- **Simple Frontend**: Provides user interface with minimal logic
  - Form for user input
  - Display of generated content
  - API calls to backend services

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key with access to:
  - GPT models (text generation)
  - Image generation models

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/storybook.git
   cd storybook
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r backend/requirements.txt
   ```

4. Run the cleanup script to ensure proper directory structure:
   ```
   python cleanup.py
   ```

### Running the Application

1. Start the application:
   ```
   python run_storybook.py
   ```

2. The application will automatically open in your default web browser at http://127.0.0.1:5000

### Command Line Options

The `run_storybook.py` script accepts the following options:

- `--port PORT`: Specify the port (default: 5000)
- `--no-browser`: Don't open browser window automatically
- `--clean-cache`: Clean old cache files before starting

## Usage

1. Enter the child's name, story theme, and personal traits
2. Select text and image generation models
3. Enter your OpenAI API key
4. Click "Generate Prompts" to create story prompts
5. Generate images for each prompt
6. Create a complete storybook PDF
7. Download and enjoy!

## API Usage and Costs

This application uses the following OpenAI APIs:

- **Text Generation**: GPT-3.5 Turbo, GPT-4, or GPT-4 Turbo
- **Image Generation**: GPT Image model

The application implements caching to reduce API costs. Identical prompts and image requests will use cached results when available.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [turn.js](http://www.turnjs.com/) for the page flip effect
- OpenAI for the text and image generation APIs
