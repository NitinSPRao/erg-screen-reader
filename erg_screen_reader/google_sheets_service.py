"""
Google Sheets integration for ErgScreenReader.

Provides functionality to create and populate Google Sheets with workout data.
"""

import os
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

from erg_screen_reader.models import Summary, Split, IntervalSummary, Interval


class GoogleSheetsService:
    """Service for creating and managing Google Sheets with workout data."""
    
    # Google Sheets API scope
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    def __init__(self, credentials_path: Optional[str] = None, token_path: str = "token.json"):
        """Initialize Google Sheets service."""
        # Use environment variable or provided path, fallback to default
        if credentials_path:
            self.credentials_path = credentials_path
        else:
            self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        
        self.token_path = token_path
        self.service = None
        self.drive_service = None
        
    def authenticate(self) -> None:
        """Authenticate with Google Sheets API."""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Google credentials file not found: {self.credentials_path}\n"
                "Please download it from Google Cloud Console and place it in the project root."
            )
        
        # Check if this is a service account credentials file
        try:
            with open(self.credentials_path, 'r') as f:
                credentials_info = json.load(f)
            
            # If it's a service account, use service account credentials
            if credentials_info.get('type') == 'service_account':
                creds = ServiceAccountCredentials.from_service_account_file(
                    self.credentials_path, scopes=self.SCOPES)
            else:
                # Handle OAuth2 credentials (web/installed app)
                creds = None
                
                # Load existing token
                if os.path.exists(self.token_path):
                    creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                
                # If no valid credentials, request authorization
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                    
                    # Save credentials for future use
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
            
            # Build the services
            self.service = build('sheets', 'v4', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in credentials file: {self.credentials_path}")
        except Exception as e:
            raise Exception(f"Error authenticating with Google Sheets: {str(e)}")
    
    def create_spreadsheet(self, title: str) -> str:
        """Create a new Google Spreadsheet."""
        if not self.service:
            self.authenticate()
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result.get('spreadsheetId')
            
            # Make the spreadsheet publicly accessible
            self._make_public(spreadsheet_id)
            
            return spreadsheet_id
            
        except HttpError as error:
            raise Exception(f"Error creating spreadsheet: {error}")
    
    def _make_public(self, spreadsheet_id: str) -> None:
        """Make a spreadsheet publicly accessible."""
        try:
            permission = {
                'type': 'anyone',
                'role': 'writer'  # Allow anyone to edit
            }
            
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()
            
        except HttpError as error:
            print(f"Warning: Could not make spreadsheet public: {error}")
    
    def get_spreadsheet_url(self, spreadsheet_id: str) -> str:
        """Get the URL for a Google Spreadsheet."""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    
    def generate_sheet_name(self, base_name: Optional[str] = None) -> str:
        """Generate a sheet name with timestamp."""
        if base_name:
            return f"{base_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            return f"Erg Screen Reader - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    def populate_regular_workout(self, spreadsheet_id: str, summary: Summary, 
                                splits: List[Split], rower_name: str) -> None:
        """Populate a Google Sheet with regular workout data."""
        if not self.service:
            self.authenticate()
        
        try:
            # Prepare summary data
            summary_values = [
                ['Rower', 'Total Distance (m)', 'Total Time', 'Average Split', 'Average Rate (SPM)', 'Average HR', 'Average Watts'],
                [rower_name, summary.total_distance, summary.total_time, 
                 summary.average_split, summary.average_rate, summary.average_hr or 'N/A', summary.average_watts or 'N/A']
            ]
            
            # Update summary sheet
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1:G2',
                valueInputOption='RAW',
                body={'values': summary_values}
            ).execute()
            
            # Create splits breakdown sheet
            splits_sheet_title = f"{rower_name} Split Breakdown"
            self._add_sheet(spreadsheet_id, splits_sheet_title)
            
            # Prepare splits data
            splits_headers = ['Split', 'Distance (m)', 'Time', 'Pace', 'Rate (SPM)', 'HR', 'Watts']
            splits_values = [splits_headers]
            
            for split in splits:
                splits_values.append([
                    split.split_number,
                    split.split_distance,
                    split.split_time,
                    split.split_pace,
                    split.rate,
                    split.hr or 'N/A',
                    split.watts or 'N/A'
                ])
            
            # Update splits sheet
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"'{splits_sheet_title}'!A1:G{len(splits_values)}",
                valueInputOption='RAW',
                body={'values': splits_values}
            ).execute()
            
            # Format the sheets
            self._format_sheets(spreadsheet_id)
            
        except HttpError as error:
            raise Exception(f"Error populating spreadsheet: {error}")
    
    def populate_interval_workout(self, spreadsheet_id: str, summary: IntervalSummary, 
                                 intervals: List[Interval], rower_name: str) -> None:
        """Populate a Google Sheet with interval workout data."""
        if not self.service:
            self.authenticate()
        
        try:
            # Prepare summary data
            summary_values = [
                ['Rower', 'Total Distance (m)', 'Total Time', 'Average Split', 'Average Rate (SPM)', 
                 'Average HR', 'Average Watts', 'Total Intervals', 'Rest Time'],
                [rower_name, summary.total_distance, summary.total_time, 
                 summary.average_split, summary.average_rate, summary.average_hr or 'N/A', summary.average_watts or 'N/A',
                 summary.total_intervals, summary.rest_time or 'N/A']
            ]
            
            # Update summary sheet
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1:I2',
                valueInputOption='RAW',
                body={'values': summary_values}
            ).execute()
            
            # Create intervals breakdown sheet
            intervals_sheet_title = f"{rower_name} Interval Breakdown"
            self._add_sheet(spreadsheet_id, intervals_sheet_title)
            
            # Prepare intervals data
            intervals_headers = ['Interval', 'Distance (m)', 'Time', 'Pace', 'Rate (SPM)', 'HR', 'Watts', 'Rest Time']
            intervals_values = [intervals_headers]
            
            for interval in intervals:
                intervals_values.append([
                    interval.interval_number,
                    interval.interval_distance,
                    interval.interval_time,
                    interval.interval_pace,
                    interval.rate,
                    interval.hr or 'N/A',
                    interval.watts or 'N/A',
                    interval.rest_time or 'N/A'
                ])
            
            # Update intervals sheet
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"'{intervals_sheet_title}'!A1:H{len(intervals_values)}",
                valueInputOption='RAW',
                body={'values': intervals_values}
            ).execute()
            
            # Format the sheets
            self._format_sheets(spreadsheet_id)
            
        except HttpError as error:
            raise Exception(f"Error populating spreadsheet: {error}")
    
    def _add_sheet(self, spreadsheet_id: str, sheet_title: str) -> None:
        """Add a new sheet to the spreadsheet."""
        try:
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_title
                    }
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
        except HttpError as error:
            # If sheet already exists, that's okay
            if "already exists" not in str(error):
                raise Exception(f"Error adding sheet: {error}")
    
    def _format_sheets(self, spreadsheet_id: str) -> None:
        """Apply basic formatting to the sheets."""
        try:
            # Get sheet properties
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            requests = []
            
            # Format each sheet
            for sheet in spreadsheet.get('sheets', []):
                sheet_id = sheet.get('properties', {}).get('sheetId')
                
                # Bold headers
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat.bold'
                    }
                })
                
                # Auto-resize columns
                requests.append({
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS'
                        }
                    }
                })
            
            # Apply formatting
            if requests:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': requests}
                ).execute()
                
        except HttpError as error:
            print(f"Warning: Could not apply formatting: {error}")