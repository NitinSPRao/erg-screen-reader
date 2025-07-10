# ErgScreenReader
Reading Erg Screenshots and sending to Google Sheets

# Goals
Using ChatGPT API to convert images into a format that can then be sent to populate into a Google Sheets sheet for data analysis

## Features

- **AI-Powered Processing**: Structured parsing using OpenAI's `responses.parse` method with base64 image encoding
- **Workout Types**: Support for both regular workouts and interval workouts
- **Excel Reports**: Automatic generation of formatted Excel reports with summary and detailed breakdowns
- **Web Interface**: Modern web-based interface for easy upload and processing

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

3. (Optional) Set up Google Sheets integration:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API and Google Drive API
   - Create credentials (OAuth 2.0 Client ID for Desktop Application)
   - Download the credentials file and save it as `credentials.json` in the project root
   - The first time you use Google Sheets, you'll be prompted to authorize the application

## Usage

### Web Interface (Recommended)

Start the web server:
```bash
python run_web.py
```

Or directly:
```bash
python app.py
```

Then open your browser and navigate to `http://localhost:5000`

**Features:**
- Drag and drop image upload
- Choose between regular and interval workouts
- Set custom rower names
- Output to Excel files or Google Sheets
- Create new spreadsheets or add to existing ones (Excel only)
- Real-time processing with progress indicators
- Download generated Excel files or open Google Sheets
- Modern, responsive interface

**How to use:**
1. Upload your erg screenshot by dragging and dropping or clicking "Choose File"
2. Select the workout type (Regular or Interval)
3. Enter the rower's name
4. Choose output format (Excel or Google Sheets)
5. For Excel: Choose whether to create a new spreadsheet or add to an existing one
6. For Google Sheets: Optionally enter a custom sheet name
7. Click "Process Workout" and wait for the AI to analyze the image
8. Review the results and download the Excel file or open the Google Sheet

### Command Line Interface

```bash
# Process regular workout with AI
python src/erg_screen_reader.py workout.png

# Process interval workout with AI
python src/erg_screen_reader.py interval_workout.png --workout-type interval

# Custom output filename
python src/erg_screen_reader.py workout.png --output my_workout.xlsx

# Custom rower name
python src/erg_screen_reader.py workout.png --name "Jane Smith"

# Create Google Sheet instead of Excel
python src/erg_screen_reader.py workout.png --sheets

# Custom Google Sheet name
python src/erg_screen_reader.py workout.png --sheets --sheet-name "Weekly Training Log"

# Add to existing spreadsheet (appends to summary and creates new breakdown sheet)
python src/erg_screen_reader.py workout2.png --name "Mike Johnson" --output existing_workouts.xlsx

### Programmatic Usage

```python
import asyncio
from src.erg_screen_reader import ErgScreenReader

async def process_regular_workout():
    reader = ErgScreenReader()
    
    # Process regular workout with AI
    receipt_details = await reader.extract_workout_data_ai("erg.png")
    
    # Access the extracted data
    summary = receipt_details.summary
    splits = receipt_details.splits
    
    print(f"Total Distance: {summary.total_distance}")
    print(f"Total Time: {summary.total_time}")
    print(f"Number of Splits: {len(splits)}")
    
    # Create Excel report
    reader.create_excel_report(summary, list(splits), "workout_report.xlsx", "John C150")

async def process_interval_workout():
    reader = ErgScreenReader()
    
    # Process interval workout with AI
    receipt_details = await reader.extract_interval_workout_data_ai("IMG_1922.png")
    
    # Access the extracted data
    summary = receipt_details.summary
    intervals = receipt_details.intervals
    
    print(f"Total Distance: {summary.total_distance}")
    print(f"Total Intervals: {summary.total_intervals}")
    print(f"Number of Intervals: {len(intervals)}")
    
    # Create Excel report
    reader.create_interval_excel_report(summary, list(intervals), "interval_report.xlsx", "John C150")

# Run the async functions
asyncio.run(process_regular_workout())
asyncio.run(process_interval_workout())
```

### Testing

```bash
# Test regular workout processing
python src/test_structured_parsing.py
```

## Data Structure

The extracted data follows these structures:

### Regular Workout Data

```python
class Summary:
    total_distance: int      # e.g., 2000
    total_time: str          # e.g., "6:29.1"
    average_split: str       # e.g., "1:37.2"
    average_rate: int        # e.g., 34
    average_hr: Optional[int] # e.g., 188

class Split:
    split_number: str        # e.g., "1"
    split_distance: int      # e.g., 500
    split_time: str          # e.g., "1:34.6"
    split_pace: str          # e.g., "1:34.6"
    rate: int                # e.g., 30
    hr: Optional[int]        # e.g., 181
```

### Interval Workout Data

```python
class IntervalSummary:
    total_distance: int      # e.g., 2000
    total_time: str          # e.g., "6:29.1"
    average_split: str       # e.g., "1:37.2"
    average_rate: int        # e.g., 34
    average_hr: Optional[int] # e.g., 188
    total_intervals: int     # e.g., 4
    rest_time: Optional[str] # e.g., "2:00"

class Interval:
    interval_number: str     # e.g., "1"
    interval_distance: int   # e.g., 500
    interval_time: str       # e.g., "1:34.6"
    interval_pace: str       # e.g., "1:34.6"
    rate: int                # e.g., 30
    hr: Optional[int]        # e.g., 181
    rest_time: Optional[str] # e.g., "1:00"
```

## Output

The tool generates formatted Excel reports with the following structure:

### Regular Workout Reports
- **Summary Sheet**: Horizontal layout with rower name, total distance, time, average split, rate, and heart rate (all values in one row)
- **{Name} Split Breakdown Sheet**: Detailed breakdown of each split with distance, time, pace, rate, and heart rate

### Interval Workout Reports
- **Summary Sheet**: Horizontal layout with rower name, total distance, time, average split, rate, heart rate, total intervals, and rest time (all values in one row)
- **{Name} Interval Breakdown Sheet**: Detailed breakdown of each interval with distance, time, pace, rate, heart rate, and rest time

### Multi-Person Workouts
When processing multiple workouts with the same output file:
- New summary data is appended as rows to the existing Summary sheet
- Each person gets their own breakdown sheet (e.g., "John C150 Split Breakdown", "Jane Smith Split Breakdown")
- Existing breakdown sheets are preserved when adding new workouts

The Excel files are automatically formatted and ready for analysis or sharing. The summary sheets use a horizontal format for easy data entry and comparison across multiple workouts.
