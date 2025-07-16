#!/usr/bin/env python3
"""
FIT File Analyzer - CLI tool for analyzing FIT files and generating graphs

Usage:
    python fit_analyzer.py <fit_file> [options]

Examples:
    python fit_analyzer.py workout.fit --metrics power,hr,speed --output graphs/
    python fit_analyzer.py workout.fit --all-metrics --save-csv
    python fit_analyzer.py workout.fit --power --intervals 1,5,10
"""

import argparse
import csv
import sys
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import tempfile

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Graphs will not be generated.")
    print("Install with: pip install matplotlib")

try:
    from fitparse import FitFile
    HAS_FITPARSE = True
except ImportError:
    HAS_FITPARSE = False
    print("Error: fitparse not installed. Install with: pip install fitparse")
    sys.exit(1)


class FitAnalyzer:
    """Analyzes FIT files and generates performance graphs."""
    
    def __init__(self, fit_file_path: str):
        """Initialize with FIT file path."""
        self.fit_file_path = Path(fit_file_path)
        if not self.fit_file_path.exists():
            raise FileNotFoundError(f"FIT file not found: {fit_file_path}")
        
        self.fitfile = FitFile(str(self.fit_file_path))
        self.data = []
        self.headers = []
        self._parse_fit_data()
    
    def _parse_fit_data(self):
        """Parse FIT file data into structured format."""
        headers_written = False
        
        for record in self.fitfile.get_messages('record'):
            data_row = []
            data_names = []
            
            for record_data in record:
                data_row.append(record_data.value)
                data_names.append(record_data.name)
            
            if not headers_written:
                self.headers = data_names
                headers_written = True
            
            if len(data_row) == len(self.headers):
                self.data.append(data_row)
    
    def get_column_data(self, column_name: str, keep_indices: bool = False) -> List[float]:
        """Get data for a specific column, filtering out None values."""
        if column_name not in self.headers:
            available = ", ".join(self.headers)
            raise ValueError(f"Column '{column_name}' not found. Available: {available}")
        
        col_index = self.headers.index(column_name)
        values = []
        indices = []
        
        for i, row in enumerate(self.data):
            if col_index < len(row) and row[col_index] is not None:
                try:
                    values.append(float(row[col_index]))
                    indices.append(i)
                except (ValueError, TypeError):
                    continue
        
        if keep_indices:
            return values, indices
        return values
    
    def get_timestamps(self) -> List[datetime]:
        """Get timestamp data."""
        if 'timestamp' not in self.headers:
            return []
        
        col_index = self.headers.index('timestamp')
        timestamps = []
        
        for row in self.data:
            if col_index < len(row) and row[col_index] is not None:
                timestamps.append(row[col_index])
        
        return timestamps
    
    def calculate_pace(self) -> List[float]:
        """Calculate pace in min/mile from distance and time data."""
        if 'distance' not in self.headers or 'timestamp' not in self.headers:
            return []
        
        timestamps = self.get_timestamps()
        distances = self.get_column_data('distance')
        
        if len(timestamps) != len(distances) or len(timestamps) < 2:
            return []
        
        paces = []
        for i in range(1, len(timestamps)):
            time_delta = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # hours
            distance_delta = (distances[i] - distances[i-1]) / 1609.34  # miles
            
            if time_delta > 0 and distance_delta > 0:
                speed_mph = distance_delta / time_delta
                pace_min_per_mile = 60 / speed_mph if speed_mph > 0 else float('inf')
                if pace_min_per_mile != float('inf'):
                    paces.append(pace_min_per_mile)
        
        return paces
    
    def calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a list of values."""
        if not values:
            return {}
        
        return {
            'avg': sum(values) / len(values),
            'max': max(values),
            'min': min(values),
            'count': len(values)
        }
    
    def calculate_best_intervals(self, values: List[float], intervals: List[int]) -> Dict[int, float]:
        """Calculate best average for given time intervals (in seconds)."""
        best_intervals = {}
        
        for interval_sec in intervals:
            if len(values) < interval_sec:
                continue
            
            max_avg = 0
            window_sum = sum(values[:interval_sec])
            max_avg = window_sum
            
            for i in range(interval_sec, len(values)):
                window_sum = window_sum - values[i - interval_sec] + values[i]
                max_avg = max(max_avg, window_sum)
            
            best_intervals[interval_sec] = max_avg / interval_sec
        
        return best_intervals
    
    def save_to_csv(self, output_path: str = None) -> str:
        """Save parsed data to CSV file."""
        if output_path is None:
            output_path = str(self.fit_file_path.with_suffix('.csv'))
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.headers)
            writer.writerows(self.data)
        
        return output_path
    
    def print_summary(self, metrics: List[str] = None):
        """Print summary statistics for specified metrics."""
        if metrics is None:
            metrics = ['power', 'heart_rate', 'speed', 'cadence']
        
        print(f"\\n=== FIT File Analysis: {self.fit_file_path.name} ===")
        print(f"Data points: {len(self.data)}")
        print(f"Duration: {self._get_workout_duration()}")
        print()
        
        for metric in metrics:
            self._print_metric_summary(metric)
    
    def _get_workout_duration(self) -> str:
        """Get workout duration as formatted string."""
        timestamps = self.get_timestamps()
        if len(timestamps) < 2:
            return "Unknown"
        
        duration = timestamps[-1] - timestamps[0]
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def _print_metric_summary(self, metric: str):
        """Print summary for a specific metric."""
        try:
            if metric == 'pace':
                values = self.calculate_pace()
                unit = "min/mile"
            else:
                # Map common metric names to FIT field names
                field_mapping = {
                    'power': 'power',
                    'hr': 'heart_rate',
                    'heart_rate': 'heart_rate',
                    'speed': 'speed',
                    'cadence': 'cadence',
                    'altitude': 'altitude',
                    'temperature': 'temperature'
                }
                
                field_name = field_mapping.get(metric, metric)
                values = self.get_column_data(field_name)
                unit = self._get_unit(field_name)
            
            if not values:
                print(f"{metric.upper()}: No data available")
                return
            
            stats = self.calculate_statistics(values)
            print(f"{metric.upper()}:")
            print(f"  Average: {stats['avg']:.1f} {unit}")
            print(f"  Maximum: {stats['max']:.1f} {unit}")
            print(f"  Minimum: {stats['min']:.1f} {unit}")
            
            # Best intervals for power and heart rate
            if metric in ['power', 'heart_rate', 'hr']:
                intervals = [60, 300, 600, 1200]  # 1min, 5min, 10min, 20min
                best = self.calculate_best_intervals(values, intervals)
                if best:
                    print("  Best intervals:")
                    for interval_sec, value in best.items():
                        minutes = interval_sec // 60
                        print(f"    {minutes} min: {value:.1f} {unit}")
            
            print()
            
        except Exception as e:
            print(f"{metric.upper()}: Error - {str(e)}")
            print()
    
    def _get_unit(self, field_name: str) -> str:
        """Get appropriate unit for a field."""
        units = {
            'power': 'W',
            'heart_rate': 'bpm',
            'speed': 'm/s',
            'cadence': 'rpm',
            'altitude': 'm',
            'temperature': '°C',
            'distance': 'm'
        }
        return units.get(field_name, '')
    
    def generate_graphs(self, metrics: List[str], output_dir: str = None, 
                       intervals: List[int] = None, show_plots: bool = True):
        """Generate graphs for specified metrics."""
        if not HAS_MATPLOTLIB:
            print("Error: matplotlib not installed. Cannot generate graphs.")
            return
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        timestamps = self.get_timestamps()
        if not timestamps:
            print("Error: No timestamp data found.")
            return
        
        # Convert timestamps to elapsed time in minutes
        start_time = timestamps[0]
        elapsed_minutes = [(ts - start_time).total_seconds() / 60 for ts in timestamps]
        
        for metric in metrics:
            try:
                self._create_metric_plot(metric, elapsed_minutes, output_dir, show_plots)
            except Exception as e:
                print(f"Error creating plot for {metric}: {str(e)}")
    
    def _create_metric_plot(self, metric: str, elapsed_minutes: List[float], 
                          output_dir: str = None, show_plot: bool = True):
        """Create a plot for a specific metric."""
        # Get data with proper alignment
        if metric == 'pace':
            values = self.calculate_pace()
            if not values:
                print(f"No data available for {metric}")
                return
            # For pace, we need aligned timestamps (pace has one less point)
            timestamps = self.get_timestamps()
            if len(timestamps) > len(values):
                start_time = timestamps[0]
                plot_times = [(timestamps[i+1] - start_time).total_seconds() / 60 for i in range(len(values))]
            else:
                plot_times = elapsed_minutes[:len(values)]
            unit = "min/mile"
            ylabel = "Pace (min/mile)"
        else:
            field_mapping = {
                'power': 'power',
                'hr': 'heart_rate',
                'heart_rate': 'heart_rate',
                'speed': 'speed',
                'cadence': 'cadence',
                'altitude': 'altitude',
                'temperature': 'temperature'
            }
            
            field_name = field_mapping.get(metric, metric)
            
            # Get data and corresponding indices
            try:
                values, indices = self.get_column_data(field_name, keep_indices=True)
            except:
                values = self.get_column_data(field_name)
                indices = list(range(len(values)))
            
            if not values:
                print(f"No data available for {metric}")
                return
            
            # Get corresponding timestamps for these data points
            timestamps = self.get_timestamps()
            if timestamps and len(timestamps) > max(indices):
                start_time = timestamps[0]
                plot_times = [(timestamps[i] - start_time).total_seconds() / 60 for i in indices]
            else:
                plot_times = elapsed_minutes[:len(values)]
            
            unit = self._get_unit(field_name)
            ylabel = f"{metric.title()} ({unit})"
        
        # Ensure arrays are same length
        min_length = min(len(plot_times), len(values))
        plot_times = plot_times[:min_length]
        values = values[:min_length]
        
        if not values:
            print(f"No data available for {metric}")
            return
        
        # Create plot
        plt.figure(figsize=(12, 6))
        plt.plot(plot_times, values, linewidth=1.5, alpha=0.8)
        plt.title(f"{metric.title()} vs Time - {self.fit_file_path.name}", fontsize=14, fontweight='bold')
        plt.xlabel("Time (minutes)", fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # Add statistics text box
        stats = self.calculate_statistics(values)
        stats_text = f"Avg: {stats['avg']:.1f} {unit}\\nMax: {stats['max']:.1f} {unit}\\nMin: {stats['min']:.1f} {unit}"
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        # Save plot
        if output_dir:
            output_path = os.path.join(output_dir, f"{metric}_{self.fit_file_path.stem}.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {output_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def create_summary_plot(self, output_dir: str = None, show_plot: bool = True):
        """Create a multi-panel summary plot with key metrics."""
        if not HAS_MATPLOTLIB:
            print("Error: matplotlib not installed. Cannot generate graphs.")
            return
        
        timestamps = self.get_timestamps()
        if not timestamps:
            print("Error: No timestamp data found.")
            return
        
        start_time = timestamps[0]
        elapsed_minutes = [(ts - start_time).total_seconds() / 60 for ts in timestamps]
        
        # Try to get data for common metrics
        metrics_data = {}
        common_metrics = [
            ('power', 'power', 'Power (W)'),
            ('heart_rate', 'heart_rate', 'Heart Rate (bpm)'),
            ('speed', 'speed', 'Speed (m/s)'),
            ('cadence', 'cadence', 'Cadence (rpm)')
        ]
        
        for metric_name, field_name, ylabel in common_metrics:
            try:
                values, indices = self.get_column_data(field_name, keep_indices=True)
                if values:
                    # Get corresponding timestamps
                    timestamps = self.get_timestamps()
                    if timestamps and len(timestamps) > max(indices):
                        start_time = timestamps[0]
                        plot_times = [(timestamps[i] - start_time).total_seconds() / 60 for i in indices]
                        metrics_data[metric_name] = (values, ylabel, plot_times)
                    else:
                        metrics_data[metric_name] = (values, ylabel)
            except:
                try:
                    values = self.get_column_data(field_name)
                    if values:
                        metrics_data[metric_name] = (values, ylabel)
                except:
                    continue
        
        # Add pace if possible
        try:
            pace_values = self.calculate_pace()
            if pace_values:
                pace_times = elapsed_minutes[1:len(pace_values)+1] if len(pace_values) < len(elapsed_minutes) else elapsed_minutes[:len(pace_values)]
                metrics_data['pace'] = (pace_values, 'Pace (min/mile)', pace_times)
        except:
            pass
        
        if not metrics_data:
            print("No data available for summary plot.")
            return
        
        # Create subplots
        num_metrics = len(metrics_data)
        fig, axes = plt.subplots(num_metrics, 1, figsize=(12, 3 * num_metrics))
        if num_metrics == 1:
            axes = [axes]
        
        fig.suptitle(f"Workout Summary - {self.fit_file_path.name}", fontsize=16, fontweight='bold')
        
        for i, (metric_name, data) in enumerate(metrics_data.items()):
            if len(data) == 3:  # with custom times
                values, ylabel, plot_times = data
            else:
                values, ylabel = data
                plot_times = elapsed_minutes[:len(values)]
            
            # Ensure arrays are same length
            min_length = min(len(plot_times), len(values))
            plot_times = plot_times[:min_length]
            values = values[:min_length]
            
            if values:  # Only plot if we have data
                axes[i].plot(plot_times, values, linewidth=1.5, alpha=0.8)
                axes[i].set_ylabel(ylabel, fontsize=10)
                axes[i].grid(True, alpha=0.3)
                axes[i].set_title(f"{metric_name.title()}", fontsize=12)
                
                # Add stats
                stats = self.calculate_statistics(values)
                unit = ylabel.split('(')[-1].rstrip(')') if '(' in ylabel else ''
                stats_text = f"Avg: {stats['avg']:.1f}\\nMax: {stats['max']:.1f}"
                axes[i].text(0.02, 0.98, stats_text, transform=axes[i].transAxes, 
                            verticalalignment='top', fontsize=8,
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        axes[-1].set_xlabel("Time (minutes)", fontsize=12)
        plt.tight_layout()
        
        # Save plot
        if output_dir:
            output_path = os.path.join(output_dir, f"summary_{self.fit_file_path.stem}.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {output_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Analyze FIT files and generate performance graphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s workout.fit --metrics power,hr,speed
  %(prog)s workout.fit --all-metrics --output graphs/
  %(prog)s workout.fit --summary --save-csv
  %(prog)s workout.fit --power --intervals 1,5,10,20
        """
    )
    
    parser.add_argument('fit_file', help='Path to FIT file')
    parser.add_argument('--metrics', '-m', help='Comma-separated list of metrics (power,hr,speed,pace,cadence,altitude)')
    parser.add_argument('--all-metrics', '-a', action='store_true', help='Analyze all available metrics')
    parser.add_argument('--summary', '-s', action='store_true', help='Create summary plot with multiple metrics')
    parser.add_argument('--output', '-o', help='Output directory for graphs')
    parser.add_argument('--save-csv', action='store_true', help='Save parsed data to CSV')
    parser.add_argument('--no-show', action='store_true', help="Don't display plots (only save)")
    parser.add_argument('--intervals', help='Comma-separated intervals in minutes for best effort analysis (e.g., 1,5,10,20)')
    parser.add_argument('--list-fields', action='store_true', help='List all available fields in the FIT file')
    
    # Individual metric flags
    parser.add_argument('--power', action='store_true', help='Analyze power data')
    parser.add_argument('--hr', action='store_true', help='Analyze heart rate data')
    parser.add_argument('--speed', action='store_true', help='Analyze speed data')
    parser.add_argument('--pace', action='store_true', help='Analyze pace data')
    parser.add_argument('--cadence', action='store_true', help='Analyze cadence data')
    parser.add_argument('--altitude', action='store_true', help='Analyze altitude data')
    
    args = parser.parse_args()
    
    try:
        analyzer = FitAnalyzer(args.fit_file)
        
        if args.list_fields:
            print("Available fields in FIT file:")
            for field in sorted(analyzer.headers):
                print(f"  {field}")
            return
        
        if args.save_csv:
            csv_path = analyzer.save_to_csv()
            print(f"Data saved to: {csv_path}")
        
        # Determine which metrics to analyze
        metrics_to_analyze = []
        
        if args.all_metrics:
            metrics_to_analyze = ['power', 'heart_rate', 'speed', 'pace', 'cadence', 'altitude']
        elif args.metrics:
            metrics_to_analyze = [m.strip() for m in args.metrics.split(',')]
        else:
            # Check individual flags
            if args.power:
                metrics_to_analyze.append('power')
            if args.hr:
                metrics_to_analyze.append('heart_rate')
            if args.speed:
                metrics_to_analyze.append('speed')
            if args.pace:
                metrics_to_analyze.append('pace')
            if args.cadence:
                metrics_to_analyze.append('cadence')
            if args.altitude:
                metrics_to_analyze.append('altitude')
        
        # Default to summary if no specific metrics requested
        if not metrics_to_analyze and not args.summary:
            args.summary = True
        
        # Print summary statistics
        if metrics_to_analyze:
            analyzer.print_summary(metrics_to_analyze)
        
        # Generate graphs
        if args.summary:
            analyzer.create_summary_plot(args.output, not args.no_show)
        elif metrics_to_analyze:
            analyzer.generate_graphs(metrics_to_analyze, args.output, show_plots=not args.no_show)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()