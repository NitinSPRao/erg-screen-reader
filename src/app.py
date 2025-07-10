#!/usr/bin/env python3
"""
Flask web application for Erg Screen Reader

Provides a web interface for uploading erg screenshots and processing them
with options to create new spreadsheets or add to existing ones.
"""

import os
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import our erg screen reader
from .erg_screen_reader import ErgScreenReader
from .google_sheets_service import GoogleSheetsService

# Get the parent directory (project root)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(project_root, 'outputs')

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_unique_filename(original_filename):
    """Generate a unique filename to avoid conflicts."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_filename)
    return f"{name}_{timestamp}{ext}"

@app.route('/')
def index():
    """Main page with upload form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload an image file.'}), 400
        
        # Get form data
        workout_type = request.form.get('workout_type', 'regular')
        name = request.form.get('name', 'John C150')
        output_format = request.form.get('output_format', 'excel')
        spreadsheet_option = request.form.get('spreadsheet_option', 'new')
        existing_filename = request.form.get('existing_filename', '')
        sheet_name = request.form.get('sheet_name', '')
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_filename = get_unique_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Determine output filename
        if spreadsheet_option == 'new':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"erg_workout_{timestamp}.xlsx"
        else:
            # Use existing filename
            if not existing_filename:
                return jsonify({'error': 'Please provide an existing spreadsheet filename'}), 400
            output_filename = existing_filename
        
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Process the image
        reader = ErgScreenReader()
        sheet_url = None
        
        if workout_type == 'interval':
            # Process interval workout
            receipt_details = asyncio.run(reader.extract_interval_workout_data_ai(filepath))
            summary = receipt_details.summary
            intervals = list(receipt_details.intervals)
            
            if output_format == 'sheets':
                # Create Google Sheet
                sheets_service = GoogleSheetsService()
                final_sheet_name = sheet_name or sheets_service.generate_sheet_name(name)
                
                spreadsheet_id = sheets_service.create_spreadsheet(final_sheet_name)
                sheets_service.populate_interval_workout(spreadsheet_id, summary, intervals, name)
                sheet_url = sheets_service.get_spreadsheet_url(spreadsheet_id)
            else:
                # Create Excel report
                reader.create_interval_excel_report(summary, intervals, output_path, name)
            
            result_data = {
                'summary': {
                    'total_distance': summary.total_distance,
                    'total_time': summary.total_time,
                    'average_split': summary.average_split,
                    'average_rate': summary.average_rate,
                    'average_hr': summary.average_hr,
                    'total_intervals': summary.total_intervals,
                    'rest_time': summary.rest_time
                },
                'intervals': [interval.model_dump() for interval in intervals],
                'workout_type': 'interval'
            }
        else:
            # Process regular workout
            receipt_details = asyncio.run(reader.extract_workout_data_ai(filepath))
            summary = receipt_details.summary
            splits = list(receipt_details.splits)
            
            if output_format == 'sheets':
                # Create Google Sheet
                sheets_service = GoogleSheetsService()
                final_sheet_name = sheet_name or sheets_service.generate_sheet_name(name)
                
                spreadsheet_id = sheets_service.create_spreadsheet(final_sheet_name)
                sheets_service.populate_regular_workout(spreadsheet_id, summary, splits, name)
                sheet_url = sheets_service.get_spreadsheet_url(spreadsheet_id)
            else:
                # Create Excel report
                reader.create_excel_report(summary, splits, output_path, name)
            
            result_data = {
                'summary': {
                    'total_distance': summary.total_distance,
                    'total_time': summary.total_time,
                    'average_split': summary.average_split,
                    'average_rate': summary.average_rate,
                    'average_hr': summary.average_hr
                },
                'splits': [split.model_dump() for split in splits],
                'workout_type': 'regular'
            }
        
        # Clean up uploaded file
        os.remove(filepath)
        
        response_data = {
            'success': True,
            'data': result_data
        }
        
        if sheet_url:
            response_data['message'] = f'Workout processed successfully! Google Sheet created: {final_sheet_name}'
            response_data['sheet_url'] = sheet_url
        else:
            response_data['message'] = f'Workout processed successfully! Excel file: {output_filename}'
            response_data['output_filename'] = output_filename
        
        return jsonify(response_data)
        
    except Exception as e:
        # Clean up uploaded file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download the generated Excel file."""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/files')
def list_files():
    """List available output files."""
    try:
        files = []
        output_dir = app.config['OUTPUT_FOLDER']
        for filename in os.listdir(output_dir):
            if filename.endswith('.xlsx'):
                file_path = os.path.join(output_dir, filename)
                file_size = os.path.getsize(file_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                files.append({
                    'name': filename,
                    'size': file_size,
                    'modified': file_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Erg Screen Reader API is running'})

if __name__ == '__main__':
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY environment variable is not set.")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
    
    app.run(debug=True, host='0.0.0.0', port=8080) 