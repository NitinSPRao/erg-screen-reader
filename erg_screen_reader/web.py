"""
FastAPI web interface for Erg Screen Reader.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from erg_screen_reader.core import ErgScreenReader, validate_environment
from erg_screen_reader.google_sheets_service import GoogleSheetsService

# Get the project root directory
project_root = Path(__file__).parent.parent

app = FastAPI(
    title="Erg Screen Reader",
    description="A tool for extracting structured workout data from rowing ergometer screen images",
    version="0.1.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory=project_root / "static"), name="static")
templates = Jinja2Templates(directory=project_root / "templates")

# Ensure directories exist
UPLOAD_FOLDER = project_root / "uploads"
OUTPUT_FOLDER = project_root / "outputs"
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to avoid conflicts."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_filename)
    return f"{name}_{timestamp}{ext}"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    workout_type: str = Form("regular"),
    name: str = Form("John C150"),
    output_format: str = Form("excel"),
    spreadsheet_option: Optional[str] = Form(None),
    existing_filename: Optional[str] = Form(None),
    sheet_action: Optional[str] = Form(None),
    sheet_name: Optional[str] = Form(None),
    sheet_url: Optional[str] = Form(None)
):
    """Handle file upload and processing."""
    
    try:
        # Validate environment
        validate_environment()
        
        # Validate file
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No file selected"}
            )
        
        if not allowed_file(file.filename):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Invalid file type"}
            )
        
        # Save uploaded file
        unique_filename = get_unique_filename(file.filename)
        file_path = UPLOAD_FOLDER / unique_filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Initialize the reader
        reader = ErgScreenReader()
        
        # Process the image based on workout type
        if workout_type == "interval":
            receipt_details = await reader.extract_interval_workout_data_ai(str(file_path))
            summary = receipt_details.summary
            intervals = list(receipt_details.intervals)
            
            # Convert to dict for JSON response
            data = {
                "workout_type": "interval",
                "summary": summary.model_dump(),
                "intervals": [interval.model_dump() for interval in intervals]
            }
            
            # Generate report based on output format
            if output_format == "sheets":
                sheets_service = GoogleSheetsService()
                sheet_name_final = sheet_name or sheets_service.generate_sheet_name(name)
                
                spreadsheet_id = sheets_service.create_spreadsheet(sheet_name_final)
                sheets_service.populate_interval_workout(spreadsheet_id, summary, intervals, name)
                sheet_url_final = sheets_service.get_spreadsheet_url(spreadsheet_id)
                
                return JSONResponse(content={
                    "success": True,
                    "data": data,
                    "sheet_url": sheet_url_final,
                    "message": "Interval workout processed successfully and Google Sheet created"
                })
            else:
                # Excel output
                output_filename = f"erg_workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                output_path = OUTPUT_FOLDER / output_filename
                
                reader.create_interval_excel_report(summary, intervals, str(output_path), name)
                
                return JSONResponse(content={
                    "success": True,
                    "data": data,
                    "output_filename": output_filename,
                    "message": "Interval workout processed successfully"
                })
        
        else:  # Regular workout
            receipt_details = await reader.extract_workout_data_ai(str(file_path))
            summary = receipt_details.summary
            splits = list(receipt_details.splits)
            
            # Convert to dict for JSON response
            data = {
                "workout_type": "regular",
                "summary": summary.model_dump(),
                "splits": [split.model_dump() for split in splits]
            }
            
            # Generate report based on output format
            if output_format == "sheets":
                sheets_service = GoogleSheetsService()
                sheet_name_final = sheet_name or sheets_service.generate_sheet_name(name)
                
                spreadsheet_id = sheets_service.create_spreadsheet(sheet_name_final)
                sheets_service.populate_regular_workout(spreadsheet_id, summary, splits, name)
                sheet_url_final = sheets_service.get_spreadsheet_url(spreadsheet_id)
                
                return JSONResponse(content={
                    "success": True,
                    "data": data,
                    "sheet_url": sheet_url_final,
                    "message": "Regular workout processed successfully and Google Sheet created"
                })
            else:
                # Excel output
                output_filename = f"erg_workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                output_path = OUTPUT_FOLDER / output_filename
                
                reader.create_excel_report(summary, splits, str(output_path), name)
                
                return JSONResponse(content={
                    "success": True,
                    "data": data,
                    "output_filename": output_filename,
                    "message": "Regular workout processed successfully"
                })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated Excel files."""
    file_path = OUTPUT_FOLDER / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.get("/files")
async def list_files():
    """List available files for selection."""
    try:
        files = []
        for file_path in OUTPUT_FOLDER.glob("*.xlsx"):
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        return JSONResponse(content={"files": files})
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


def main():
    """Main entry point for the web server."""
    print("🚣 Erg Screen Reader Web Interface")
    print("=" * 40)
    
    # Check environment
    try:
        validate_environment()
        print("✅ Environment variables are properly configured.")
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n🚀 Starting web server...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 40)
    
    uvicorn.run(
        "erg_screen_reader.web:app",
        host="0.0.0.0",
        port=8080,
        reload=False
    )


if __name__ == "__main__":
    main()