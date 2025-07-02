# ErgScreenReader
Reading Erg Screenshots and sending to Google Sheets

# Goals
Using ChatGPT API to convert images into a format that can then be sent to populate into a Google Sheets sheet for data analysis

## Features

- **OCR Engine**: Traditional OCR using Google Cloud Vision API
- **OpenAI Engine**: Structured parsing using OpenAI's `responses.parse` method with base64 image encoding (recommended)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

## Usage

### Command Line Interface

```bash
# Use OCR engine (default)
python src/ErgScreenReader.py erg.png

# Use OpenAI structured approach (recommended)
python src/ErgScreenReader.py erg.png --engine openai
```

### Programmatic Usage

```python
import asyncio
from src.ErgScreenReader import extract_receipt_details

async def process_erg_image():
    # Use the structured parsing approach
    receipt_details = await extract_receipt_details("erg.png", model="gpt-4o")
    
    # Access the extracted data
    summary = receipt_details.summary
    splits = receipt_details.splits
    
    print(f"Total Distance: {summary.total_distance}")
    print(f"Total Time: {summary.total_time}")
    print(f"Number of Splits: {len(splits)}")

# Run the async function
asyncio.run(process_erg_image())
```

### Test the New Functionality

```bash
python test_structured_parsing.py
```

## Engine Comparison

| Engine | Pros | Cons | Use Case |
|--------|------|------|----------|
| OCR | Fast, no API costs | Less accurate, requires regex parsing | Quick testing, offline use |
| OpenAI | Most accurate, reliable parsing | Requires OpenAI API | Production use |

## Data Structure

The extracted data follows this structure:

```python
class Summary:
    total_distance: str      # e.g., "2000"
    total_time: str          # e.g., "6:29.1"
    average_split: str       # e.g., "1:37.2"
    average_rate: str        # e.g., "34"
    average_hr: Optional[str] # e.g., "188"

class Split:
    split_number: str        # e.g., "1"
    split_distance: str      # e.g., "500"
    split_time: str          # e.g., "1:34.6"
    split_pace: str          # e.g., "1:34.6"
    rate: str                # e.g., "30"
    hr: Optional[str]        # e.g., "181"
```

## Output

The tool automatically uploads extracted data to Google Sheets and provides a shareable link. If Google Sheets upload fails, it creates a local Excel file as backup.
