#!/usr/bin/env python3
"""
Test script for the new structured parsing functionality in ErgScreenReader.
This demonstrates how to use the extract_receipt_details function.
"""

import asyncio
import os
from ErgScreenReader import extract_receipt_details

async def test_structured_parsing():
    """Test the new structured parsing approach."""
    
    # Check if we have an image to test with
    test_images = ["erg.png", "erg1.jpeg"]
    image_path = None
    
    for img in test_images:
        if os.path.exists(img):
            image_path = img
            break
    
    if not image_path:
        print("No test image found. Please ensure erg.png or erg1.jpeg exists in the current directory.")
        return
    
    print(f"Testing structured parsing with image: {image_path}")
    
    try:
        # Use the new structured parsing approach
        receipt_details = await extract_receipt_details(image_path, model="gpt-4o")
        
        print("\n=== EXTRACTION RESULTS ===")
        print(f"Summary:")
        print(f"  Total Distance: {receipt_details.summary.total_distance}")
        print(f"  Total Time: {receipt_details.summary.total_time}")
        print(f"  Average Split: {receipt_details.summary.average_split}")
        print(f"  Average Rate: {receipt_details.summary.average_rate}")
        if receipt_details.summary.average_hr:
            print(f"  Average HR: {receipt_details.summary.average_hr}")
        
        print(f"\nSplits ({len(receipt_details.splits)} total):")
        for i, split in enumerate(receipt_details.splits, 1):
            print(f"  Split {i}: {split.split_distance}m in {split.split_time} @ {split.split_pace} pace, {split.rate} spm", end="")
            if split.hr:
                print(f", HR: {split.hr}")
            else:
                print()
        
        print("\n✅ Structured parsing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during structured parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_structured_parsing()) 