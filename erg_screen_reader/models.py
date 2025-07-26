from pydantic import BaseModel, computed_field
from typing import List, Optional
import re

def time_to_seconds(time_str: str) -> float:
    """Convert time string (e.g., '2:05.1') to seconds."""
    try:
        # Handle formats like "2:05.1", "2:05", "1:25.4"
        if '.' in time_str:
            main_part, decimal_part = time_str.split('.')
            decimal_seconds = float(f"0.{decimal_part}")
        else:
            main_part = time_str
            decimal_seconds = 0.0
        
        if ':' in main_part:
            parts = main_part.split(':')
            if len(parts) == 2:
                minutes, seconds = parts
                total_seconds = int(minutes) * 60 + int(seconds) + decimal_seconds
            else:
                # Handle unexpected format
                total_seconds = float(time_str.replace(':', ''))
        else:
            total_seconds = float(main_part) + decimal_seconds
        
        return total_seconds
    except (ValueError, AttributeError):
        return 0.0

def calculate_watts(pace_time: str, distance: int) -> Optional[float]:
    """Calculate watts using formula: watts = 2.80/pace^3 where pace = time_in_seconds/distance_in_meters."""
    try:
        if not pace_time or distance <= 0:
            return None
        
        time_seconds = time_to_seconds(pace_time)
        if time_seconds <= 0:
            return None
        
        # Calculate pace as time per meter
        pace = time_seconds / distance
        
        # Apply the watts formula: watts = 2.80/pace^3
        watts = 2.80 / (pace ** 3)
        
        return round(watts, 1)
    except (ValueError, ZeroDivisionError):
        return None

class Summary(BaseModel):
    total_distance: int
    total_time: str
    average_split: str
    average_rate: int
    average_hr: Optional[int] = None
    average_watts: Optional[float] = None

class Split(BaseModel):
    split_number: str
    split_distance: int  # This is cumulative distance
    split_time: str
    split_pace: str
    rate: int
    hr: Optional[int] = None
    _actual_split_distance: Optional[int] = None  # Will be set by ErgData
    
    def set_actual_split_distance(self, distance: int) -> None:
        """Set the actual split distance (current - previous cumulative distance)."""
        self._actual_split_distance = distance
    
    @computed_field
    @property
    def watts(self) -> Optional[float]:
        """Calculate watts from split pace and actual split distance."""
        # Use the actual split distance if set, otherwise fall back to assuming 500m
        distance = self._actual_split_distance if self._actual_split_distance is not None else 500
        return calculate_watts(self.split_pace, distance)

class ErgData(BaseModel):
    summary: Summary
    splits: List[Split]
    
    def __post_init__(self):
        """Calculate actual split distances after initialization."""
        self._calculate_actual_split_distances()
    
    def model_post_init(self, __context) -> None:
        """Calculate actual split distances after Pydantic initialization."""
        self._calculate_actual_split_distances()
    
    def _calculate_actual_split_distances(self) -> None:
        """Calculate actual split distances (current - previous cumulative distance)."""
        prev_distance = 0
        for split in self.splits:
            actual_distance = split.split_distance - prev_distance
            split.set_actual_split_distance(actual_distance)
            prev_distance = split.split_distance
        
        # Calculate average watts after setting split distances
        self._calculate_average_watts()
    
    def _calculate_average_watts(self) -> None:
        """Calculate average watts from all splits."""
        watts_values = [split.watts for split in self.splits if split.watts is not None]
        if watts_values:
            self.summary.average_watts = round(sum(watts_values) / len(watts_values), 1)

class ReceiptDetails(BaseModel):
    summary: Summary
    splits: List[Split]
    
    def model_post_init(self, __context) -> None:
        """Calculate actual split distances after Pydantic initialization."""
        self._calculate_actual_split_distances()
    
    def _calculate_actual_split_distances(self) -> None:
        """Calculate actual split distances (current - previous cumulative distance)."""
        prev_distance = 0
        for split in self.splits:
            actual_distance = split.split_distance - prev_distance
            split.set_actual_split_distance(actual_distance)
            prev_distance = split.split_distance
        
        # Calculate average watts after setting split distances
        self._calculate_average_watts()
    
    def _calculate_average_watts(self) -> None:
        """Calculate average watts from all splits."""
        watts_values = [split.watts for split in self.splits if split.watts is not None]
        if watts_values:
            self.summary.average_watts = round(sum(watts_values) / len(watts_values), 1)

# New models for interval workouts
class IntervalSummary(BaseModel):
    total_distance: int
    total_time: str
    average_split: str
    average_rate: int
    average_hr: Optional[int] = None
    average_watts: Optional[float] = None
    total_intervals: int
    rest_time: Optional[str] = None

class Interval(BaseModel):
    interval_number: str
    interval_distance: int  # This is cumulative distance
    interval_time: str
    interval_pace: str
    rate: int
    hr: Optional[int] = None
    rest_time: Optional[str] = None
    _actual_interval_distance: Optional[int] = None  # Will be set by IntervalWorkoutData
    
    def set_actual_interval_distance(self, distance: int) -> None:
        """Set the actual interval distance (current - previous cumulative distance)."""
        self._actual_interval_distance = distance
    
    @computed_field
    @property
    def watts(self) -> Optional[float]:
        """Calculate watts from interval pace and actual interval distance."""
        # Use the actual interval distance if set, otherwise fall back to using the stored distance
        distance = self._actual_interval_distance if self._actual_interval_distance is not None else self.interval_distance
        return calculate_watts(self.interval_pace, distance)

class IntervalWorkoutData(BaseModel):
    summary: IntervalSummary
    intervals: List[Interval]
    
    def model_post_init(self, __context) -> None:
        """Calculate actual interval distances after Pydantic initialization."""
        self._calculate_actual_interval_distances()
    
    def _calculate_actual_interval_distances(self) -> None:
        """Calculate actual interval distances (current - previous cumulative distance)."""
        prev_distance = 0
        for interval in self.intervals:
            actual_distance = interval.interval_distance - prev_distance
            interval.set_actual_interval_distance(actual_distance)
            prev_distance = interval.interval_distance
        
        # Calculate average watts after setting interval distances
        self._calculate_average_watts()
    
    def _calculate_average_watts(self) -> None:
        """Calculate average watts from all intervals."""
        watts_values = [interval.watts for interval in self.intervals if interval.watts is not None]
        if watts_values:
            self.summary.average_watts = round(sum(watts_values) / len(watts_values), 1)

class IntervalReceiptDetails(BaseModel):
    summary: IntervalSummary
    intervals: List[Interval]
    
    def model_post_init(self, __context) -> None:
        """Calculate actual interval distances after Pydantic initialization."""
        self._calculate_actual_interval_distances()
    
    def _calculate_actual_interval_distances(self) -> None:
        """Calculate actual interval distances (current - previous cumulative distance)."""
        prev_distance = 0
        for interval in self.intervals:
            actual_distance = interval.interval_distance - prev_distance
            interval.set_actual_interval_distance(actual_distance)
            prev_distance = interval.interval_distance
        
        # Calculate average watts after setting interval distances
        self._calculate_average_watts()
    
    def _calculate_average_watts(self) -> None:
        """Calculate average watts from all intervals."""
        watts_values = [interval.watts for interval in self.intervals if interval.watts is not None]
        if watts_values:
            self.summary.average_watts = round(sum(watts_values) / len(watts_values), 1)