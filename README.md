# Simplified Storybook Generator

A streamlined web application that generates personalized children's storybooks with AI-generated text and illustrations.

## Features

- Create personalized stories based on a child's name, theme, and traits
- Generate high-quality illustrations for each story scene
- Create background images for text pages
- Overlay text on themed backgrounds
- Export to PDF for easy reading and printing

## Project Structure

```
storybook-simplified/
├── app.py                 # Main Flask application 
├── templates/             # HTML templates
│   ├── index.html         # Input form
│   └── storybook.html     # Storybook viewer/download page
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript
│   ├── images/            # Generated images
│   ├── pdfs/              # Generated PDFs
│   └── references/        # Uploaded reference images
├── modules/               # Core modules
│   ├── story/             # Story generation
│   │   └── generator.py   # Story text generation
│   ├── image/             # Image generation
│   │   ├── generator.py   # Main scene illustrations
│   │   ├── background.py  # Background generation module
│   │   └── overlay.py     # Text overlay module
│   └── pdf/               # PDF generation module
│       └── creator.py     # PDF creation and formatting
├── utils/                 # Utility functions
│   ├── session.py         # Session management
│   └── helpers.py         # Miscellaneous helpers
└── requirements.txt       # Project dependencies
```

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key with access to:
  - GPT models (text generation)
  - Image generation models

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/nikhilbharadwajreddy/storybook.git
   cd storybook
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the application:
   ```
   python app.py
   ```

2. Open your browser and navigate to http://127.0.0.1:5000

## Usage

1. Enter the child's name, story theme, and personal traits
2. Optionally upload a reference image of the child
3. Enter your OpenAI API key
4. Click "Generate Story" to create a personalized story
5. For each scene, click "Generate Illustration" to create images
6. Once all illustrations are generated, click "Create PDF Storybook"
7. Download and enjoy your personalized storybook!

## Architecture

This application follows a modular architecture:

- **Story Generation Module**: Generates personalized story scenes using OpenAI's GPT models
- **Image Generation Modules**:
  - **Illustration Generator**: Creates illustrations for story scenes
  - **Background Generator**: Creates themed backgrounds for text pages
  - **Text Overlay**: Combines text with backgrounds for text pages
- **PDF Generator**: Creates downloadable PDF storybooks from generated content

## License

This project is licensed under the MIT License - see the LICENSE file for details.
