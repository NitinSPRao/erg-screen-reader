"""
Erg Screen Reader

A tool for extracting structured workout data from rowing ergometer screen images.
Supports both OCR (Google Cloud Vision) and AI-powered (OpenAI) image processing.

Author: Nitin Rao
"""

import argparse
import asyncio
import base64
import io
import mimetypes
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import vision
from google.cloud.vision_v1 import types
from openai import AsyncOpenAI

# Local imports
from models import ReceiptDetails
from prompt_template import BASIC_PROMPT

# Load environment variables
load_dotenv()


class ErgScreenReader:
    """
    Main class for processing ergometer screen images and extracting workout data.
    
    This class provides methods to extract workout data from ergometer screen images
    using either OCR (Google Cloud Vision) or AI-powered image analysis (OpenAI).
    The extracted data includes summary statistics and detailed split breakdowns.
    """
    
    def __init__(self):
        """Initialize the ErgScreenReader with necessary clients."""
        self.openai_client = AsyncOpenAI()
        self.vision_client = vision.ImageAnnotatorClient()
    
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
    
    def extract_workout_data_ocr(self, image_path: str) -> tuple[dict, list]:
        """
        Extract workout data from an ergometer image using OCR.
        
        Args:
            image_path (str): Path to the ergometer screen image
            
        Returns:
            tuple[dict, list]: Summary data and list of split data
            
        Raises:
            FileNotFoundError: If the image file doesn't exist
            Exception: If OCR processing fails
        """
        # Read image content
        image_content = self._read_image_file(image_path)
        
        # Extract text using Google Cloud Vision
        extracted_text = self._perform_ocr(image_content)
        
        # Parse the extracted text into structured data
        summary, splits = self._parse_ocr_text(extracted_text)
        
        return summary, splits
    
    def _read_image_file(self, image_path: str) -> bytes:
        """
        Read image file and return its binary content.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            bytes: Binary content of the image file
        """
        with io.open(image_path, 'rb') as image_file:
            return image_file.read()
    
    def _perform_ocr(self, image_content: bytes) -> str:
        """
        Perform OCR on image content using Google Cloud Vision.
        
        Args:
            image_content (bytes): Binary image content
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            Exception: If OCR processing fails
        """
        image = types.Image(content=image_content)
        response = self.vision_client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"OCR processing failed: {response.error.message}")
        
        texts = response.text_annotations
        if not texts:
            print("No text detected in image")
            return ""
        
        extracted_text = texts[0].description
        print("Detected text:")
        print(extracted_text)
        
        return extracted_text
    
    def _parse_ocr_text(self, extracted_text: str) -> tuple[dict, list]:
        """
        Parse OCR-extracted text into structured workout data.
        
        Args:
            extracted_text (str): Raw text extracted from the image
            
        Returns:
            tuple[dict, list]: Summary data and list of split data
        """
        lines = [line.strip() for line in extracted_text.strip().split('\n') if line.strip()]
        
        # Extract summary data
        summary = self._extract_summary_data(lines)
        
        # Extract split data
        splits = self._extract_split_data(lines)
        
        return summary, splits
    
    def _extract_summary_data(self, lines: list[str]) -> dict:
        """
        Extract summary workout data from OCR text lines.
        
        Args:
            lines (list[str]): Lines of text from the image
            
        Returns:
            dict: Summary data with total time, distance, average split, rate, and HR
        """
        # Pattern for summary row: e.g., "6:29.1 2000 1:37.2 34 188"
        summary_pattern = re.compile(r"^(\d+:\d{2}\.\d)\s+(\d+)\s+(\d{1}:\d{2}\.\d)\s+(\d+)\s+(\d+)$")
        
        for line in lines:
            match = summary_pattern.match(line)
            if match:
                return {
                    'total_time': match.group(1),
                    'total_distance': match.group(2),
                    'average_split': match.group(3),
                    'average_rate': match.group(4),
                    'average_hr': match.group(5)
                }
        
        return {}
    
    def _extract_split_data(self, lines: list[str]) -> list[dict]:
        """
        Extract split workout data from OCR text lines.
        
        Args:
            lines (list[str]): Lines of text from the image
            
        Returns:
            list[dict]: List of split data dictionaries
        """
        splits = []
        split_number = 1
        
        # Define patterns for different split formats
        split_patterns = [
            # Colon-start format: e.g., ":48.2 250 1:36.4 36 177"
            re.compile(r"^:(\d{2}\.\d)\s+(\d+)\s+(\d{1}:\d{2}[\.,]\d)\s*(\d+)?\s*(\d+)?"),
            # Full-time format: e.g., "1:34.6 500 1:34.6 30 181"
            re.compile(r"^(\d{1}:\d{2}\.\d)\s+(\d+)\s+(\d{1}:\d{2}\.\d)\s+(\d+)\s+(\d+)$")
        ]
        
        for line in lines:
            split_data = self._parse_split_line(line, split_patterns, split_number)
            if split_data:
                splits.append(split_data)
                split_number += 1
            else:
                print(f"Unmatched split line: {line}")
        
        return splits
    
    def _parse_split_line(self, line: str, patterns: list, split_number: int) -> dict | None:
        """
        Parse a single split line using the provided patterns.
        
        Args:
            line (str): Text line to parse
            patterns (list): List of regex patterns to try
            split_number (int): Current split number
            
        Returns:
            dict | None: Parsed split data or None if no match
        """
        for pattern in patterns:
            match = pattern.match(line)
            if match:
                if pattern.pattern.startswith('^:'):
                    # Colon-start format
                    return {
                        'split_number': str(split_number),
                        'split_time': match.group(1),
                        'split_distance': match.group(2),
                        'split_pace': match.group(3).replace(',', '.'),
                        'rate': match.group(4) if match.group(4) else '',
                        'hr': match.group(5) if match.group(5) else ''
                    }
                else:
                    # Full-time format
                    return {
                        'split_number': str(split_number),
                        'split_time': match.group(1),
                        'split_distance': match.group(2),
                        'split_pace': match.group(3),
                        'rate': match.group(4),
                        'hr': match.group(5)
                    }
        
        return None
    
    def create_excel_report(self, summary: dict, splits: list, output_filename: str = "output.xlsx") -> None:
        """
        Create a well-formatted Excel report with workout data.
        
        Args:
            summary (dict): Summary workout data
            splits (list): List of split data dictionaries
            output_filename (str): Name of the output Excel file
        """
        # Convert Pydantic models to dictionaries if needed
        summary_dict = self._convert_to_dict(summary)
        splits_dict = [self._convert_to_dict(split) for split in splits] if splits else []
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            self._write_summary_sheet(writer, summary_dict)
            self._write_splits_sheet(writer, splits_dict)
        
        # Print success message
        print(f"Excel report created: {output_filename}")
        print(f"  - Summary sheet: {len(summary_dict) if summary_dict else 0} metrics")
        print(f"  - Splits sheet: {len(splits_dict)} splits")
    
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
    
    def _write_summary_sheet(self, writer: pd.ExcelWriter, summary_dict: dict) -> None:
        """
        Write summary data to Excel sheet.
        
        Args:
            writer (pd.ExcelWriter): Excel writer object
            summary_dict (dict): Summary data dictionary
        """
        if not summary_dict:
            return
        
        summary_data = {
            'Metric': [
                'Total Distance (m)',
                'Total Time',
                'Average Split',
                'Average Rate (spm)',
                'Average HR'
            ],
            'Value': [
                summary_dict.get('total_distance', ''),
                summary_dict.get('total_time', ''),
                summary_dict.get('average_split', ''),
                summary_dict.get('average_rate', ''),
                summary_dict.get('average_hr', 'N/A') if summary_dict.get('average_hr') else 'N/A'
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    def _write_splits_sheet(self, writer: pd.ExcelWriter, splits_dict: list) -> None:
        """
        Write splits data to Excel sheet.
        
        Args:
            writer (pd.ExcelWriter): Excel writer object
            splits_dict (list): List of split data dictionaries
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
                'HR': split.get('hr', 'N/A') if split.get('hr') else 'N/A'
            })
        
        splits_df = pd.DataFrame(splits_data)
        splits_df.to_excel(writer, sheet_name='Splits', index=False)


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
  %(prog)s erg.png                    # Use OCR processing
  %(prog)s erg.png --engine openai    # Use AI processing
  %(prog)s erg.png --output my_workout.xlsx  # Custom output filename
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
        choices=["ocr", "openai"],
        default="ocr",
        help="Processing engine to use (default: ocr)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output.xlsx",
        help="Output Excel filename (default: output.xlsx)"
    )
    
    args = parser.parse_args()
    
    # Initialize the reader
    reader = ErgScreenReader()
    
    try:
        # Process the image based on selected engine
        if args.engine == "openai":
            # Validate environment for AI processing
            validate_environment()
            
            print(f"Processing image with AI engine: {args.image_path}")
            receipt_details = await reader.extract_workout_data_ai(args.image_path)
            
            summary = receipt_details.summary
            splits = list(receipt_details.splits)
            
        else:  # OCR engine
            print(f"Processing image with OCR engine: {args.image_path}")
            summary, splits = reader.extract_workout_data_ocr(args.image_path)
        
        # Display extracted data
        print(f"\nExtracted Summary: {summary}")
        print(f"Extracted Splits: {splits}")
        
        # Generate Excel report
        reader.create_excel_report(summary, splits, args.output)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
