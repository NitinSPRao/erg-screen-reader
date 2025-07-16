# ErgScreenReader
Convert erg rowing machine screenshots into structured workout data using AI, with output to Excel files or Google Sheets.

## Goals
Using OpenAI's Vision API to intelligently extract workout metrics from erg screenshots and automatically populate them into structured formats for data analysis and tracking.

## Features

- **AI-Powered Processing**: Advanced image analysis using OpenAI's Vision API with structured parsing
- **Workout Types**: Support for both regular workouts and interval workouts with automatic detection
- **Multiple Output Formats**: Generate Excel files or create/update Google Sheets
- **Google Sheets Integration**: Create new sheets or append to existing ones with automatic sharing
- **Web Interface**: Modern, responsive web interface with drag-and-drop file upload
- **Batch Processing**: Add multiple workouts to the same spreadsheet for team tracking
- **Columbia University Theme**: Custom styling for Columbia rowing team

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

3. Set up Google Sheets integration:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API and Google Drive API
   - Create a service account with the following steps:
     - Go to "IAM & Admin" > "Service Accounts"
     - Click "Create Service Account"
     - Give it a name and description
     - Click "Create and Continue"
     - Skip the role assignment (click "Continue")
     - Click "Done"
   - Generate credentials for the service account:
     - Click on the service account you just created
     - Go to the "Keys" tab
     - Click "Add Key" > "Create new key"
     - Choose "JSON" format and click "Create"
   - Download the JSON credentials file
   - Place the credentials file in your project directory (e.g., `/Users/yourusername/igneous-aleph-394703-550f3acb3017.json`)
   - Set the environment variable:
     ```bash
     export GOOGLE_CREDENTIALS_PATH="/path/to/your/credentials.json"
     ```

## Usage

### Web Interface (Recommended)

Start the web server:
```bash
python run_web.py
```

Or directly:
```bash
python src/app.py
```

Then open your browser and navigate to `http://localhost:8080`

**Features:**
- Drag and drop image upload with file preview
- Choose between regular and interval workouts
- Set custom rower names
- Output to Excel files or Google Sheets
- For Excel: Create new spreadsheets or add to existing ones
- For Google Sheets: Create new sheets or append to existing ones via URL
- Real-time processing with progress indicators
- Download generated Excel files or open Google Sheets directly
- Modern, responsive interface with Columbia University branding
- Error handling and validation

**How to use:**
1. Upload your erg screenshot by dragging and dropping or clicking "Choose File"
2. Select the workout type (Regular or Interval)
3. Enter the rower's name
4. Choose output format (Excel or Google Sheets)
5. For Excel: Choose whether to create a new spreadsheet or add to an existing one
6. For Google Sheets: 
   - Create New: Optionally enter a custom sheet name (auto-generates if empty)
   - Add to Existing: Paste the Google Sheets URL you want to append data to
7. Click "Process Workout" and wait for the AI to analyze the image
8. Review the extracted workout data in the results section
9. Download the Excel file or open the Google Sheet using the provided button

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
python src/erg_screen_reader.py workout.png --sheets --name "John C150"

# Add to existing spreadsheet (appends to summary and creates new breakdown sheet)
python src/erg_screen_reader.py workout2.png --name "Mike Johnson" --output existing_workouts.xlsx
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

## Output Formats

### Excel Files
The tool generates formatted Excel reports with the following structure:

**Regular Workout Reports:**
- **Summary Sheet**: Horizontal layout with rower name, total distance, time, average split, rate, and heart rate (all values in one row)
- **{Name} Split Breakdown Sheet**: Detailed breakdown of each split with distance, time, pace, rate, and heart rate

**Interval Workout Reports:**
- **Summary Sheet**: Horizontal layout with rower name, total distance, time, average split, rate, heart rate, total intervals, and rest time (all values in one row)
- **{Name} Interval Breakdown Sheet**: Detailed breakdown of each interval with distance, time, pace, rate, heart rate, and rest time

**Multi-Person Workouts:**
When processing multiple workouts with the same output file:
- New summary data is appended as rows to the existing Summary sheet
- Each person gets their own breakdown sheet (e.g., "John C150 Split Breakdown", "Jane Smith Split Breakdown")
- Existing breakdown sheets are preserved when adding new workouts

### Google Sheets
The tool creates Google Sheets with similar structure to Excel files:

**New Google Sheets:**
- Automatically generated with timestamp-based naming: `[Rower Name] - YYYY-MM-DD HH:MM:SS`
- Publicly accessible with edit permissions (configurable)
- Same sheet structure as Excel files (Summary + Breakdown sheets)

**Existing Google Sheets:**
- Appends new workout data to existing Summary sheet
- Creates new breakdown sheet for each rower
- Preserves existing data and formatting
- Supports any Google Sheets URL format

**Google Sheets Features:**
- Automatic formatting with bold headers
- Auto-resized columns for optimal viewing
- Public sharing enabled for team access
- Direct browser links for immediate access

All output files are automatically formatted and ready for analysis or sharing. The summary sheets use a horizontal format for easy data entry and comparison across multiple workouts.

## Requirements

- Python 3.7+
- OpenAI API key with GPT-4 Vision access
- Google Cloud Project with Sheets API and Drive API enabled (for Google Sheets functionality)
- Service account credentials JSON file (for Google Sheets functionality)

See `requirements.txt` for the complete list of Python dependencies.

## Troubleshooting

### Google Sheets Issues

**"No credentials file found":**
- Ensure your service account JSON file exists at the specified path
- Set the `GOOGLE_CREDENTIALS_PATH` environment variable to the correct file path
- Check that the file has proper read permissions

**"Client secrets must be for a web or installed app":**
- You're using OAuth2 credentials instead of service account credentials
- Download service account credentials (JSON) from Google Cloud Console instead
- Follow the service account setup instructions above

**"Unable to parse range: Summary!A1:F1":**
- The sheet you're trying to append to doesn't have a "Summary" sheet
- The tool will automatically use the first available sheet if "Summary" doesn't exist
- Ensure the Google Sheets URL is correct and accessible

**"Error accessing existing sheet":**
- Check that the Google Sheets URL is correct and properly formatted
- Ensure the service account has access to the sheet (sheet should be publicly editable or shared with the service account email)
- Verify the spreadsheet ID can be extracted from the URL

### Common Issues

**"Processing failed" errors:**
- Check that your OpenAI API key is set correctly
- Ensure the uploaded image is clear and contains erg workout data
- Try with a different image if the current one is unclear or corrupted

**Web interface not loading:**
- Check that you're navigating to the correct port (8080 by default)
- Ensure no other application is using the same port
- Try running `python src/app.py` directly to see error messages

**Excel file download issues:**
- Check that the `outputs` directory exists and has write permissions
- Ensure sufficient disk space for file creation
- Try processing a smaller image if memory is an issue

For additional support, check the debug output in the console when running the web application.
