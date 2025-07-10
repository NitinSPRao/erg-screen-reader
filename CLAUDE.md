# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ErgScreenReader is a Python application that extracts structured workout data from rowing ergometer screen images using AI-powered image analysis. It supports both regular workouts and interval workouts, generating formatted Excel reports with summary statistics and detailed breakdowns.

## Common Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your-openai-api-key"
```

### Running the Application
```bash
# Start web interface (recommended)
python run_web.py
# or
python app.py

# Command line interface
python src/erg_screen_reader.py image.png
python src/erg_screen_reader.py image.png --workout-type interval
python src/erg_screen_reader.py image.png --name "Rower Name" --output report.xlsx
python src/erg_screen_reader.py image.png --sheets --sheet-name "Custom Name"
```

### Testing
```bash
# Run the test script
python src/test_structured_parsing.py
```

## Architecture

### Core Components

1. **ErgScreenReader** (`src/erg_screen_reader.py`): Main processing class that handles AI-powered image analysis using OpenAI's vision models
2. **GoogleSheetsService** (`src/google_sheets_service.py`): Service for creating and managing Google Sheets with workout data
3. **Data Models** (`src/models.py`): Pydantic models defining the structure for workout data:
   - `Summary`/`IntervalSummary`: Overall workout statistics
   - `Split`/`Interval`: Individual split/interval data
   - `ReceiptDetails`/`IntervalReceiptDetails`: Complete workout data containers
4. **Prompt Templates** (`src/prompt_template.py`): AI prompts for structured data extraction from images
5. **Web Interface** (`app.py`): Flask application providing drag-and-drop upload and processing

### Data Flow

1. Image uploaded via web interface or command line
2. Image encoded as base64 and sent to OpenAI's vision model with structured prompts
3. AI extracts workout data using `openai.responses.parse()` with Pydantic models
4. Data formatted into Excel reports with summary and detailed breakdown sheets
5. Multiple workouts can be appended to the same Excel file

### Key Features

- **Dual Workout Types**: Regular workouts (split-based) and interval workouts (with rest periods)
- **AI-Powered Processing**: Uses OpenAI's structured parsing with base64 image encoding
- **Dual Output Formats**: Excel files or Google Sheets
- **Excel Generation**: Formatted reports with horizontal summary layout and detailed breakdowns
- **Google Sheets Integration**: Creates publicly accessible sheets with auto-generated names
- **Multi-Person Support**: Append multiple workouts to single Excel file with separate breakdown sheets
- **Web Interface**: Modern Flask-based UI with drag-and-drop upload

### File Structure

- `src/`: Core application code
- `static/`: Web interface assets (CSS, JS)
- `templates/`: HTML templates for Flask app
- `run_web.py`: Web server entry point
- `app.py`: Flask application definition

## Development Notes

- Uses async/await pattern for OpenAI API calls
- Pydantic models ensure type safety for extracted data
- OpenAI API key required via environment variable
- Google Sheets integration requires OAuth2 credentials (`credentials.json`)
- Web interface supports files up to 16MB
- Excel files use openpyxl for formatting and multi-sheet support
- Google Sheets are created with public write access for easy sharing