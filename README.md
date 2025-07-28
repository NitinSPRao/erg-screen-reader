# Erg Screen Reader

A modern Python tool for extracting structured workout data from rowing ergometer screen images using AI, with support for both Excel and Google Sheets output.

## Features

### Erg Screenshot Analysis
- **AI-Powered Processing**: Advanced image analysis using OpenAI's Vision API with structured parsing
- **Watts Calculation**: Automatic power calculation using the standard formula: `watts = 2.80/pace³`
- **Name Deduplication**: Automatic handling of duplicate names (e.g., "John C150", "John C150 2")
- **Workout Types**: Support for both regular workouts and interval workouts
- **Multiple Output Formats**: Generate Excel files or create/update Google Sheets
- **Web Interface**: Modern, responsive FastAPI web interface with drag-and-drop upload
- **Batch Processing**: Add multiple workouts to the same spreadsheet for team tracking

### FIT File Analysis
- **Smart Activity Detection**: Automatically shows pace for running, speed for cycling
- **TrainingPeaks-Style Interface**: Multi-panel synchronized graphs with crosshair cursor
- **Interactive Analysis**: Hover anywhere to see all metrics at that time point
- **Best Effort Intervals**: Analyze 1min, 5min, 10min, 20min power/pace efforts
- **Rich Terminal Output**: Beautiful CLI with progress indicators and colored output
- **Multiple Export Formats**: Interactive HTML, CSV data export, JSON format

## Quick Start

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and setup**:
```bash
git clone <repository-url>
cd erg-screen-reader
python scripts/setup.py
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Quick Commands

```bash
# Start the web interface
uv run erg-web
# or
make web

# Use the CLI
uv run erg-reader image.png --name "John Doe"

# Development mode (with hot reload)
python scripts/dev.py
```

## Detailed Setup

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required for AI processing
OPENAI_API_KEY=your_openai_api_key_here

# Optional for Google Sheets integration
GOOGLE_CREDENTIALS_PATH=credentials.json
```

### Google Sheets Setup (Optional)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API and Google Drive API
4. Create a service account and download the credentials JSON file
5. Place the credentials file in your project root as `credentials.json`

## Usage

### Web Interface

1. Start the web server:
```bash
uv run erg-web
```

2. Open your browser to `http://localhost:8080`

3. Upload an erg screenshot and configure output options

### Command Line Interface

Process a regular workout:
```bash
uv run erg-reader screenshot.png --name "John Doe"
```

Process an interval workout:
```bash
uv run erg-reader screenshot.png --workout-type interval --name "Jane Smith"
```

Create a Google Sheet:
```bash
uv run erg-reader screenshot.png --sheets --sheet-name "Team Training"
```

### Development

Start development server with hot reload:
```bash
python scripts/dev.py
```

Run tests and checks:
```bash
make test      # Run tests
make lint      # Check code quality
make format    # Format code
make check     # Run all checks
```

## Project Structure

```
erg-screen-reader/
├── erg_screen_reader/          # Main package
│   ├── __init__.py
│   ├── core.py                 # Core ErgScreenReader class
│   ├── models.py               # Pydantic data models
│   ├── web.py                  # FastAPI web application
│   ├── cli.py                  # Command line interface
│   ├── google_sheets_service.py # Google Sheets integration
│   └── prompt_template.py      # AI prompts
├── templates/                  # HTML templates
├── static/                     # CSS, JS, images
├── scripts/                    # Development scripts
├── pyproject.toml              # Modern Python configuration
├── uv.lock                     # Dependency lock file
└── README.md
```

## Dependencies

This project uses modern Python tooling:

- **uv**: Fast Python package installer and resolver
- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI web server
- **Pydantic**: Data validation using Python type annotations
- **OpenAI**: AI-powered image analysis
- **Google APIs**: Google Sheets and Drive integration
- **Pandas**: Excel file generation and data manipulation

## Contributing

1. Install development dependencies: `make dev`
2. Run tests: `make test`
3. Format code: `make format`
4. Check code quality: `make lint`

