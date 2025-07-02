from pydantic import BaseModel
from typing import List, Optional

class Summary(BaseModel):
    total_distance: str
    total_time: str
    average_split: str
    average_rate: str
    average_hr: Optional[str] = None

class Split(BaseModel):
    split_number: str
    split_distance: str
    split_time: str
    split_pace: str
    rate: str
    hr: Optional[str] = None

class ErgData(BaseModel):
    summary: Summary
    splits: List[Split]

class ReceiptDetails(BaseModel):
    summary: Summary
    splits: List[Split] 