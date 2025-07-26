"""
Command line interface for Erg Screen Reader.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from erg_screen_reader.core import ErgScreenReader, validate_environment
from erg_screen_reader.google_sheets_service import GoogleSheetsService


async def main():
    """Main entry point for the CLI application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Extract workout data from rowing ergometer screen images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s erg.png                                    # Process regular workout
  %(prog)s erg.png --workout-type interval            # Process interval workout
  %(prog)s erg.png --output my_workout.xlsx           # Custom output filename
  %(prog)s erg.png --name "Jane Smith"                # Custom rower name
  %(prog)s erg.png --sheets                           # Create Google Sheet
  %(prog)s erg.png --sheets --sheet-name "Training"   # Custom Google Sheet name
        """
    )
    
    parser.add_argument(
        "image_path",
        type=str,
        help="Path to the ergometer screen image"
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
            print(f"Processing interval workout image: {args.image_path}")
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
                
                sheet_url = sheets_service.get_spreadsheet_url(spreadsheet_id)
                print(f"Google Sheet created successfully: {sheet_url}")
            else:
                # Generate interval Excel report
                reader.create_interval_excel_report(summary, intervals, args.output, args.name)
                print(f"Excel report created: {args.output}")
            
        else:  # Regular workout
            print(f"Processing regular workout image: {args.image_path}")
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