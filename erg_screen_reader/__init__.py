"""
Erg Screen Reader - A tool for extracting structured workout data from rowing ergometer screen images.
"""

from erg_screen_reader.core import ErgScreenReader
from erg_screen_reader.google_sheets_service import GoogleSheetsService
from erg_screen_reader.models import Summary, Split, IntervalSummary, Interval, ReceiptDetails, IntervalReceiptDetails

__version__ = "0.1.0"

__all__ = [
    'ErgScreenReader',
    'GoogleSheetsService', 
    'Summary',
    'Split',
    'IntervalSummary',
    'Interval',
    'ReceiptDetails',
    'IntervalReceiptDetails'
]