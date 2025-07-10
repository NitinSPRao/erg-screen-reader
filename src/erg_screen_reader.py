"""
Erg Screen Reader

A tool for extracting structured workout data from rowing ergometer screen images.
Supports both OCR (Google Cloud Vision) and AI-powered (OpenAI) image processing.

Author: Nitin Rao
"""

import argparse
import asyncio
import base64
import mimetypes
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Local imports
from .models import ReceiptDetails, IntervalReceiptDetails
from .prompt_template import BASIC_PROMPT, INTERVAL_PROMPT
from .google_sheets_service import GoogleSheetsService

# Load environment variables
load_dotenv()


class ErgScreenReader:
    """
    Main class for processing ergometer screen images and extracting workout data.
    
    This class provides methods to extract workout data from ergometer screen images
    using AI-powered image analysis (OpenAI). The extracted data includes summary 
    statistics and detailed split/interval breakdowns.
    """
    
    def __init__(self):
        """Initialize the ErgScreenReader with necessary clients."""
        self.openai_client = AsyncOpenAI()
    
    async def extract_workout_data_ai(self, image_path: str, model: str = "gpt-4o") -> ReceiptDetails:
        """
        Extract workout data from an ergometer image using OpenAI's AI vision.
        
        Args:
            image_path (str): Path to the ergometer screen image
            model (str): OpenAI model to use for image analysis
            
        Returns:
            ReceiptDetails: Structured workout data including summary and splits
            
        Raises:
            FileNotFoundError: If the image file doesn't exist
            ValueError: If the image format is not supported
        """
        # Validate image file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Determine image MIME type for data URI
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            raise ValueError(f"Could not determine MIME type for: {image_path}")
        
        # Read and encode image as base64
        image_bytes = Path(image_path).read_bytes()
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:{mime_type};base64,{b64_image}"
        
        # Process image with OpenAI
        response = await self.openai_client.responses.parse(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": BASIC_PROMPT},
                        {"type": "input_image", "image_url": image_data_url},
                    ],
                }
            ],
            text_format=ReceiptDetails,
        )
        
        return response.output_parsed
    
    async def extract_interval_workout_data_ai(self, image_path: str, model: str = "gpt-4o") -> IntervalReceiptDetails:
        """
        Extract interval workout data from an ergometer image using OpenAI's AI vision.
        
        Args:
            image_path (str): Path to the ergometer screen image
            model (str): OpenAI model to use for image analysis
            
        Returns:
            IntervalReceiptDetails: Structured interval workout data including summary and intervals
            
        Raises:
            FileNotFoundError: If the image file doesn't exist
            ValueError: If the image format is not supported
        """
        # Validate image file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Determine image MIME type for data URI
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            raise ValueError(f"Could not determine MIME type for: {image_path}")
        
        # Read and encode image as base64
        image_bytes = Path(image_path).read_bytes()
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:{mime_type};base64,{b64_image}"
        
        # Process image with OpenAI
        response = await self.openai_client.responses.parse(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": INTERVAL_PROMPT},
                        {"type": "input_image", "image_url": image_data_url},
                    ],
                }
            ],
            text_format=IntervalReceiptDetails,
        )
        
        return response.output_parsed
    

    
    def create_excel_report(self, summary: dict, splits: list, output_filename: str = "output.xlsx", name: str = "John C150") -> None:
        """
        Create a well-formatted Excel report with workout data.
        
        Args:
            summary (dict): Summary workout data
            splits (list): List of split data dictionaries
            output_filename (str): Name of the output Excel file
            name (str): Name of the rower (default: "John C150")
        """
        # Convert Pydantic models to dictionaries if needed
        summary_dict = self._convert_to_dict(summary)
        splits_dict = [self._convert_to_dict(split) for split in splits] if splits else []
        
        # Check if file exists and load existing data
        existing_summary_data = None
        existing_sheets_data = {}
        if os.path.exists(output_filename):
            try:
                # Read all existing data before we start writing
                excel_file = pd.ExcelFile(output_filename)
                existing_summary_data = pd.read_excel(output_filename, sheet_name='Summary')
                print(f"Found existing summary data with {len(existing_summary_data)} rows")
                
                # Store all existing sheets data
                for sheet_name in excel_file.sheet_names:
                    if sheet_name != 'Summary':
                        existing_sheets_data[sheet_name] = pd.read_excel(output_filename, sheet_name=sheet_name)
                        print(f"Found existing sheet: {sheet_name}")
            except Exception as e:
                print(f"Could not read existing data: {e}")
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(output_filename, engine='openpyxl', mode='w') as writer:
            self._write_summary_sheet(writer, summary_dict, name, existing_summary_data)
            self._write_splits_sheet(writer, splits_dict, name)
            
            # Write back all existing sheets (except the ones we just wrote)
            for sheet_name, sheet_data in existing_sheets_data.items():
                if sheet_name != f"{name} Split Breakdown":
                    sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"Preserved existing sheet: {sheet_name}")
        
        # Print success message
        print(f"Excel report created: {output_filename}")
        print(f"  - Summary sheet: {len(summary_dict) if summary_dict else 0} metrics")
        print(f"  - {name} Split Breakdown sheet: {len(splits_dict)} splits")
    
    def create_interval_excel_report(self, summary: dict, intervals: list, output_filename: str = "interval_output.xlsx", name: str = "John C150") -> None:
        """
        Create a well-formatted Excel report with interval workout data.
        
        Args:
            summary (dict): Summary interval workout data
            intervals (list): List of interval data dictionaries
            output_filename (str): Name of the output Excel file
            name (str): Name of the rower (default: "John C150")
        """
        # Convert Pydantic models to dictionaries if needed
        summary_dict = self._convert_to_dict(summary)
        intervals_dict = [self._convert_to_dict(interval) for interval in intervals] if intervals else []
        
        # Check if file exists and load existing data
        existing_summary_data = None
        existing_sheets_data = {}
        if os.path.exists(output_filename):
            try:
                # Read all existing data before we start writing
                excel_file = pd.ExcelFile(output_filename)
                existing_summary_data = pd.read_excel(output_filename, sheet_name='Summary')
                print(f"Found existing summary data with {len(existing_summary_data)} rows")
                
                # Store all existing sheets data
                for sheet_name in excel_file.sheet_names:
                    if sheet_name != 'Summary':
                        existing_sheets_data[sheet_name] = pd.read_excel(output_filename, sheet_name=sheet_name)
                        print(f"Found existing sheet: {sheet_name}")
            except Exception as e:
                print(f"Could not read existing data: {e}")
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(output_filename, engine='openpyxl', mode='w') as writer:
            self._write_interval_summary_sheet(writer, summary_dict, name, existing_summary_data)
            self._write_intervals_sheet(writer, intervals_dict, name)
            
            # Write back all existing sheets (except the ones we just wrote)
            for sheet_name, sheet_data in existing_sheets_data.items():
                if sheet_name != f"{name} Interval Breakdown":
                    sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"Preserved existing sheet: {sheet_name}")
        
        # Print success message
        print(f"Interval Excel report created: {output_filename}")
        print(f"  - Summary sheet: {len(summary_dict) if summary_dict else 0} metrics")
        print(f"  - {name} Interval Breakdown sheet: {len(intervals_dict)} intervals")
    
    def _convert_to_dict(self, obj) -> dict:
        """
        Convert Pydantic model or dict to plain dictionary.
        
        Args:
            obj: Object to convert (Pydantic model or dict)
            
        Returns:
            dict: Plain dictionary representation
        """
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif isinstance(obj, dict):
            return obj
        else:
            return {}
    
    def _write_summary_sheet(self, writer: pd.ExcelWriter, summary_dict: dict, name: str = "John C150", existing_data: pd.DataFrame = None) -> None:
        """
        Write summary data to Excel sheet in horizontal format, appending to existing data if present.
        
        Args:
            writer (pd.ExcelWriter): Excel writer object
            summary_dict (dict): Summary data dictionary
            name (str): Name of the rower
            existing_data (pd.DataFrame): Existing summary data to append to
        """
        if not summary_dict:
            return
        
        # Create horizontal summary with name as first column
        new_summary_data = {
            'Name': [name],
            'Total Distance (m)': [summary_dict.get('total_distance', '')],
            'Total Time': [summary_dict.get('total_time', '')],
            'Average Split': [summary_dict.get('average_split', '')],
            'Average Rate (spm)': [summary_dict.get('average_rate', '')],
            'Average HR': [summary_dict.get('average_hr', '') if summary_dict.get('average_hr') is not None else '']
        }
        
        new_summary_df = pd.DataFrame(new_summary_data)
        
        # If existing data exists, append the new row
        if existing_data is not None:
            # Ensure columns match
            for col in new_summary_df.columns:
                if col not in existing_data.columns:
                    existing_data[col] = 'N/A'
            
            # Append new data to existing data
            combined_df = pd.concat([existing_data, new_summary_df], ignore_index=True)
            print(f"Appended new workout data for {name} to existing summary")
        else:
            combined_df = new_summary_df
            print(f"Created new summary sheet with workout data for {name}")
        
        combined_df.to_excel(writer, sheet_name='Summary', index=False)
    
    def _write_splits_sheet(self, writer: pd.ExcelWriter, splits_dict: list, name: str = "John C150") -> None:
        """
        Write splits data to Excel sheet with person's name in title.
        
        Args:
            writer (pd.ExcelWriter): Excel writer object
            splits_dict (list): List of split data dictionaries
            name (str): Name of the rower
        """
        if not splits_dict:
            return
        
        splits_data = []
        for split in splits_dict:
            splits_data.append({
                'Split #': split.get('split_number', ''),
                'Distance (m)': split.get('split_distance', ''),
                'Time': split.get('split_time', ''),
                'Pace': split.get('split_pace', ''),
                'Rate (spm)': split.get('rate', ''),
                'HR': split.get('hr', '') if split.get('hr') is not None else ''
            })
        
        splits_df = pd.DataFrame(splits_data)
        sheet_name = f"{name} Split Breakdown"
        splits_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _write_interval_summary_sheet(self, writer: pd.ExcelWriter, summary_dict: dict, name: str = "John C150", existing_data: pd.DataFrame = None) -> None:
        """
        Write interval summary data to Excel sheet in horizontal format, appending to existing data if present.
        
        Args:
            writer (pd.ExcelWriter): Excel writer object
            summary_dict (dict): Summary data dictionary
            name (str): Name of the rower
            existing_data (pd.DataFrame): Existing summary data to append to
        """
        if not summary_dict:
            return
        
        # Create horizontal summary with name as first column
        new_summary_data = {
            'Name': [name],
            'Total Distance (m)': [summary_dict.get('total_distance', '')],
            'Total Time': [summary_dict.get('total_time', '')],
            'Average Split': [summary_dict.get('average_split', '')],
            'Average Rate (spm)': [summary_dict.get('average_rate', '')],
            'Average HR': [summary_dict.get('average_hr', '') if summary_dict.get('average_hr') is not None else ''],
            'Total Intervals': [summary_dict.get('total_intervals', '')],
            'Rest Time': [summary_dict.get('rest_time', '') if summary_dict.get('rest_time') else '']
        }
        
        new_summary_df = pd.DataFrame(new_summary_data)
        
        # If existing data exists, append the new row
        if existing_data is not None:
            # Ensure columns match
            for col in new_summary_df.columns:
                if col not in existing_data.columns:
                    existing_data[col] = 'N/A'
            
            # Append new data to existing data
            combined_df = pd.concat([existing_data, new_summary_df], ignore_index=True)
            print(f"Appended new interval workout data for {name} to existing summary")
        else:
            combined_df = new_summary_df
            print(f"Created new summary sheet with interval workout data for {name}")
        
        combined_df.to_excel(writer, sheet_name='Summary', index=False)
    
    def _write_intervals_sheet(self, writer: pd.ExcelWriter, intervals_dict: list, name: str = "John C150") -> None:
        """
        Write intervals data to Excel sheet with person's name in title.
        
        Args:
            writer (pd.ExcelWriter): Excel writer object
            intervals_dict (list): List of interval data dictionaries
            name (str): Name of the rower
        """
        if not intervals_dict:
            return
        
        intervals_data = []
        for interval in intervals_dict:
            intervals_data.append({
                'Interval #': interval.get('interval_number', ''),
                'Distance (m)': interval.get('interval_distance', ''),
                'Time': interval.get('interval_time', ''),
                'Pace': interval.get('interval_pace', ''),
                'Rate (spm)': interval.get('rate', ''),
                'HR': interval.get('hr', '') if interval.get('hr') is not None else '',
                'Rest Time': interval.get('rest_time', '') if interval.get('rest_time') else ''
            })
        
        intervals_df = pd.DataFrame(intervals_data)
        sheet_name = f"{name} Interval Breakdown"
        intervals_df.to_excel(writer, sheet_name=sheet_name, index=False)


def validate_environment() -> None:
    """
    Validate that required environment variables are set.
    
    Raises:
        ValueError: If required environment variables are missing
    """
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError(
            "OPENAI_API_KEY environment variable is required for AI processing. "
            "Please set it with: export OPENAI_API_KEY='your-api-key'"
        )


async def main():
    """
    Main entry point for the Erg Screen Reader application.
    
    Parses command line arguments, processes the image, and generates an Excel report.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Extract workout data from rowing ergometer screen images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s erg.png                                    # Process regular workout with AI
  %(prog)s erg.png --workout-type interval            # Process as interval workout with AI
  %(prog)s erg.png --output my_workout.xlsx           # Custom output filename
  %(prog)s erg.png --name "Jane Smith"                # Custom rower name
  %(prog)s erg.png --sheets                           # Create Google Sheet instead of Excel
  %(prog)s erg.png --sheets --sheet-name "Weekly Training" # Custom Google Sheet name
        """
    )
    
    parser.add_argument(
        "image_path",
        type=str,
        help="Path to the ergometer screen image"
    )
    
    parser.add_argument(
        "--engine",
        type=str,
        choices=["openai"],
        default="openai",
        help="Processing engine to use (default: openai)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output.xlsx",
        help="Output Excel filename (default: output.xlsx)"
    )
    
    parser.add_argument(
        "--workout-type",
        type=str,
        choices=["regular", "interval"],
        default="regular",
        help="Type of workout to process (default: regular)"
    )
    
    parser.add_argument(
        "--name",
        type=str,
        default="John C150",
        help="Name of the rower (default: John C150)"
    )
    
    parser.add_argument(
        "--sheets",
        action="store_true",
        help="Create a Google Sheet instead of Excel file"
    )
    
    parser.add_argument(
        "--sheet-name",
        type=str,
        help="Name for the Google Sheet (defaults to 'Erg Screen Reader <date/time>')"
    )
    
    args = parser.parse_args()
    
    # Initialize the reader
    reader = ErgScreenReader()
    
    try:
        # Validate environment for AI processing
        validate_environment()
        
        # Process the image based on workout type
        if args.workout_type == "interval":
            print(f"Processing interval workout image with AI engine: {args.image_path}")
            receipt_details = await reader.extract_interval_workout_data_ai(args.image_path)
            
            summary = receipt_details.summary
            intervals = list(receipt_details.intervals)
            
            # Display extracted data
            print(f"\nExtracted Interval Summary: {summary}")
            print(f"Extracted Intervals: {intervals}")
            
            # Generate report based on output type
            if args.sheets:
                # Create Google Sheet
                sheets_service = GoogleSheetsService()
                sheet_name = args.sheet_name or sheets_service.generate_sheet_name(args.name)
                
                print(f"Creating Google Sheet: {sheet_name}")
                spreadsheet_id = sheets_service.create_spreadsheet(sheet_name)
                
                print("Populating Google Sheet with interval workout data...")
                sheets_service.populate_interval_workout(spreadsheet_id, summary, intervals, args.name)
                
                sheet_url = sheets_service.get_spreadsheet_url(spreadsheet_id)
                print(f"Google Sheet created successfully: {sheet_url}")
            else:
                # Generate interval Excel report
                reader.create_interval_excel_report(summary, intervals, args.output, args.name)
                print(f"Excel report created: {args.output}")
            
        else:  # Regular workout
            print(f"Processing regular workout image with AI engine: {args.image_path}")
            receipt_details = await reader.extract_workout_data_ai(args.image_path)
            
            summary = receipt_details.summary
            splits = list(receipt_details.splits)
            
            # Display extracted data
            print(f"\nExtracted Summary: {summary}")
            print(f"Extracted Splits: {splits}")
            
            # Generate report based on output type
            if args.sheets:
                # Create Google Sheet
                sheets_service = GoogleSheetsService()
                sheet_name = args.sheet_name or sheets_service.generate_sheet_name(args.name)
                
                print(f"Creating Google Sheet: {sheet_name}")
                spreadsheet_id = sheets_service.create_spreadsheet(sheet_name)
                
                print("Populating Google Sheet with regular workout data...")
                sheets_service.populate_regular_workout(spreadsheet_id, summary, splits, args.name)
                
                sheet_url = sheets_service.get_spreadsheet_url(spreadsheet_id)
                print(f"Google Sheet created successfully: {sheet_url}")
            else:
                # Generate Excel report
                reader.create_excel_report(summary, splits, args.output, args.name)
                print(f"Excel report created: {args.output}")
        
    except Exception as e:
        print(f"Error processing image: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
