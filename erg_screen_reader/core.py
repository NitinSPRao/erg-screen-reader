"""
Erg Screen Reader Core

A tool for extracting structured workout data from rowing ergometer screen images.
Supports AI-powered (OpenAI) image processing.
"""

import base64
import mimetypes
import os
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI

from erg_screen_reader.models import ReceiptDetails, IntervalReceiptDetails
from erg_screen_reader.prompt_template import BASIC_PROMPT, INTERVAL_PROMPT

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
            image_path: Path to the ergometer screen image
            model: OpenAI model to use for image analysis
            
        Returns:
            Structured workout data including summary and splits
            
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
            image_path: Path to the ergometer screen image
            model: OpenAI model to use for image analysis
            
        Returns:
            Structured interval workout data including summary and intervals
            
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
    
    def create_excel_report(self, summary: Dict, splits: List, output_filename: str = "output.xlsx", name: str = "John C150") -> None:
        """
        Create a well-formatted Excel report with workout data.
        
        Args:
            summary: Summary workout data
            splits: List of split data dictionaries
            output_filename: Name of the output Excel file
            name: Name of the rower
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
            unique_name = self._write_summary_sheet(writer, summary_dict, name, existing_summary_data)
            self._write_splits_sheet(writer, splits_dict, unique_name)
            
            # Write back all existing sheets (except the ones we just wrote)
            for sheet_name, sheet_data in existing_sheets_data.items():
                if sheet_name != f"{unique_name} Split Breakdown":
                    sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"Preserved existing sheet: {sheet_name}")
        
        # Print success message
        print(f"Excel report created: {output_filename}")
        print(f"  - Summary sheet: {len(summary_dict) if summary_dict else 0} metrics")
        print(f"  - {unique_name} Split Breakdown sheet: {len(splits_dict)} splits")
    
    def create_interval_excel_report(self, summary: Dict, intervals: List, output_filename: str = "interval_output.xlsx", name: str = "John C150") -> None:
        """
        Create a well-formatted Excel report with interval workout data.
        
        Args:
            summary: Summary interval workout data
            intervals: List of interval data dictionaries
            output_filename: Name of the output Excel file
            name: Name of the rower
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
            unique_name = self._write_interval_summary_sheet(writer, summary_dict, name, existing_summary_data)
            self._write_intervals_sheet(writer, intervals_dict, unique_name)
            
            # Write back all existing sheets (except the ones we just wrote)
            for sheet_name, sheet_data in existing_sheets_data.items():
                if sheet_name != f"{unique_name} Interval Breakdown":
                    sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"Preserved existing sheet: {sheet_name}")
        
        # Print success message
        print(f"Interval Excel report created: {output_filename}")
        print(f"  - Summary sheet: {len(summary_dict) if summary_dict else 0} metrics")
        print(f"  - {unique_name} Interval Breakdown sheet: {len(intervals_dict)} intervals")
    
    def _convert_to_dict(self, obj) -> dict:
        """Convert Pydantic model or dict to plain dictionary."""
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif isinstance(obj, dict):
            return obj
        else:
            return {}
    
    def _get_unique_name(self, name: str, existing_data: Optional[pd.DataFrame] = None) -> str:
        """Generate a unique name by adding a number suffix if the name already exists."""
        if existing_data is None or existing_data.empty:
            return name
        
        # Get existing names
        existing_names = existing_data['Name'].tolist() if 'Name' in existing_data.columns else []
        
        # If name doesn't exist, return as is
        if name not in existing_names:
            return name
        
        # Find the highest number suffix for this base name
        base_name = name
        max_suffix = 1
        
        for existing_name in existing_names:
            if existing_name == base_name:
                continue
            if existing_name.startswith(f"{base_name} "):
                suffix_part = existing_name[len(base_name) + 1:]
                try:
                    suffix_num = int(suffix_part)
                    max_suffix = max(max_suffix, suffix_num)
                except ValueError:
                    continue
        
        # Return the next available number
        return f"{base_name} {max_suffix + 1}"
    
    def _write_summary_sheet(self, writer: pd.ExcelWriter, summary_dict: dict, name: str, existing_data: Optional[pd.DataFrame] = None) -> str:
        """Write summary data to Excel sheet."""
        if not summary_dict:
            return name
        
        # Get unique name to avoid conflicts
        unique_name = self._get_unique_name(name, existing_data)
        
        # Create horizontal summary with unique name as first column
        new_summary_data = {
            'Name': [unique_name],
            'Total Distance (m)': [summary_dict.get('total_distance', '')],
            'Total Time': [summary_dict.get('total_time', '')],
            'Average Split': [summary_dict.get('average_split', '')],
            'Average Rate (spm)': [summary_dict.get('average_rate', '')],
            'Average HR': [summary_dict.get('average_hr', '') if summary_dict.get('average_hr') is not None else ''],
            'Average Watts': [summary_dict.get('average_watts', '') if summary_dict.get('average_watts') is not None else '']
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
            print(f"Appended new workout data for {unique_name} to existing summary")
        else:
            combined_df = new_summary_df
            print(f"Created new summary sheet with workout data for {unique_name}")
        
        combined_df.to_excel(writer, sheet_name='Summary', index=False)
        return unique_name
    
    def _write_splits_sheet(self, writer: pd.ExcelWriter, splits_dict: list, name: str) -> None:
        """Write splits data to Excel sheet."""
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
                'HR': split.get('hr', '') if split.get('hr') is not None else '',
                'Watts': split.get('watts', '') if split.get('watts') is not None else ''
            })
        
        splits_df = pd.DataFrame(splits_data)
        sheet_name = f"{name} Split Breakdown"
        splits_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _write_interval_summary_sheet(self, writer: pd.ExcelWriter, summary_dict: dict, name: str, existing_data: Optional[pd.DataFrame] = None) -> str:
        """Write interval summary data to Excel sheet."""
        if not summary_dict:
            return name
        
        # Get unique name to avoid conflicts
        unique_name = self._get_unique_name(name, existing_data)
        
        # Create horizontal summary with unique name as first column
        new_summary_data = {
            'Name': [unique_name],
            'Total Distance (m)': [summary_dict.get('total_distance', '')],
            'Total Time': [summary_dict.get('total_time', '')],
            'Average Split': [summary_dict.get('average_split', '')],
            'Average Rate (spm)': [summary_dict.get('average_rate', '')],
            'Average HR': [summary_dict.get('average_hr', '') if summary_dict.get('average_hr') is not None else ''],
            'Average Watts': [summary_dict.get('average_watts', '') if summary_dict.get('average_watts') is not None else ''],
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
            print(f"Appended new interval workout data for {unique_name} to existing summary")
        else:
            combined_df = new_summary_df
            print(f"Created new summary sheet with interval workout data for {unique_name}")
        
        combined_df.to_excel(writer, sheet_name='Summary', index=False)
        return unique_name
    
    def _write_intervals_sheet(self, writer: pd.ExcelWriter, intervals_dict: list, name: str) -> None:
        """Write intervals data to Excel sheet."""
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
                'Watts': interval.get('watts', '') if interval.get('watts') is not None else '',
                'Rest Time': interval.get('rest_time', '') if interval.get('rest_time') else ''
            })
        
        intervals_df = pd.DataFrame(intervals_data)
        sheet_name = f"{name} Interval Breakdown"
        intervals_df.to_excel(writer, sheet_name=sheet_name, index=False)


def validate_environment() -> None:
    """Validate that required environment variables are set."""
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError(
            "OPENAI_API_KEY environment variable is required for AI processing. "
            "Please set it with: export OPENAI_API_KEY='your-api-key'"
        )