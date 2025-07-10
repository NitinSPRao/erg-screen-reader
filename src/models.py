from pydantic import BaseModel
from typing import List, Optional

class Summary(BaseModel):
    total_distance: int
    total_time: str
    average_split: str
    average_rate: int
    average_hr: Optional[int] = None

class Split(BaseModel):
    split_number: str
    split_distance: int
    split_time: str
    split_pace: str
    rate: int
    hr: Optional[int] = None

class ErgData(BaseModel):
    summary: Summary
    splits: List[Split]

class ReceiptDetails(BaseModel):
    summary: Summary
    splits: List[Split]

# New models for interval workouts
class IntervalSummary(BaseModel):
    total_distance: int
    total_time: str
    average_split: str
    average_rate: int
    average_hr: Optional[int] = None
    total_intervals: int
    rest_time: Optional[str] = None

class Interval(BaseModel):
    interval_number: str
    interval_distance: int
    interval_time: str
    interval_pace: str
    rate: int
    hr: Optional[int] = None
    rest_time: Optional[str] = None

class IntervalWorkoutData(BaseModel):
    summary: IntervalSummary
    intervals: List[Interval]

class IntervalReceiptDetails(BaseModel):
    summary: IntervalSummary
    intervals: List[Interval] 