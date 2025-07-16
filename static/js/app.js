// Erg Screen Reader Web Interface JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeApp();
});

function initializeApp() {
    setupDragAndDrop();
    setupFormHandlers();
    loadExistingFiles();
}

// Drag and Drop Functionality
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('file');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);

    // Handle file input change
    fileInput.addEventListener('change', handleFileSelect);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    document.getElementById('uploadArea').classList.add('dragover');
}

function unhighlight(e) {
    document.getElementById('uploadArea').classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        displayFileInfo(file);
        document.getElementById('file').files = files;
    }
}

function displayFileInfo(file) {
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    
    fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
    fileInfo.classList.remove('d-none');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function clearFile() {
    document.getElementById('file').value = '';
    document.getElementById('fileInfo').classList.add('d-none');
}

// Form Handlers
function setupFormHandlers() {
    const form = document.getElementById('uploadForm');
    const spreadsheetOptions = document.querySelectorAll('input[name="spreadsheet_option"]');
    const outputFormatOptions = document.querySelectorAll('input[name="output_format"]');
    const sheetActionOptions = document.querySelectorAll('input[name="sheet_action"]');
    
    form.addEventListener('submit', handleFormSubmit);
    
    spreadsheetOptions.forEach(option => {
        option.addEventListener('change', handleSpreadsheetOptionChange);
    });
    
    outputFormatOptions.forEach(option => {
        option.addEventListener('change', handleOutputFormatChange);
    });
    
    sheetActionOptions.forEach(option => {
        option.addEventListener('change', handleSheetActionChange);
    });
}

function handleOutputFormatChange(e) {
    const excelOptions = document.getElementById('excelOptions');
    const sheetsOptions = document.getElementById('sheetsOptions');
    const existingFileSection = document.getElementById('existingFileSection');
    
    if (e.target.value === 'sheets') {
        excelOptions.classList.add('d-none');
        sheetsOptions.classList.remove('d-none');
        existingFileSection.classList.add('d-none');
    } else {
        excelOptions.classList.remove('d-none');
        sheetsOptions.classList.add('d-none');
        // Check if existing spreadsheet option is selected
        const existingOption = document.querySelector('input[name="spreadsheet_option"]:checked');
        if (existingOption && existingOption.value === 'existing') {
            existingFileSection.classList.remove('d-none');
        }
    }
}

function handleSheetActionChange(e) {
    const newSheetOptions = document.getElementById('newSheetOptions');
    const existingSheetOptions = document.getElementById('existingSheetOptions');
    
    if (e.target.value === 'existing') {
        newSheetOptions.classList.add('d-none');
        existingSheetOptions.classList.remove('d-none');
    } else {
        newSheetOptions.classList.remove('d-none');
        existingSheetOptions.classList.add('d-none');
    }
}

function handleSpreadsheetOptionChange(e) {
    const existingFileSection = document.getElementById('existingFileSection');
    if (e.target.value === 'existing') {
        existingFileSection.classList.remove('d-none');
        loadExistingFiles();
    } else {
        existingFileSection.classList.add('d-none');
    }
}

function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const file = document.getElementById('file').files[0];
    
    if (!file) {
        showError('Please select a file to upload.');
        return;
    }
    
    // Validate Google Sheets URL if "Add to Existing" is selected
    const outputFormat = formData.get('output_format');
    const sheetAction = formData.get('sheet_action');
    const sheetUrl = formData.get('sheet_url');
    
    if (outputFormat === 'sheets' && sheetAction === 'existing' && !sheetUrl) {
        showError('Please provide a Google Sheet URL when adding to existing sheet.');
        return;
    }
    
    formData.append('file', file);
    
    // Debug: Log form data
    console.log('Form submission data:');
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }
    
    // Show loading state
    showLoading(true);
    hideError();
    hideResults();
    
    // Submit form
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        if (data.success) {
            showResults(data);
        } else {
            showError(data.error || 'An error occurred while processing the file.');
        }
    })
    .catch(error => {
        showLoading(false);
        showError('Network error: ' + error.message);
    });
}

// File Management
function loadExistingFiles() {
    fetch('/files')
        .then(response => response.json())
        .then(data => {
            if (data.files) {
                populateExistingFilesList(data.files);
            }
        })
        .catch(error => {
            console.error('Error loading existing files:', error);
        });
}

function populateExistingFilesList(files) {
    const select = document.getElementById('existing_filename');
    select.innerHTML = '<option value="">Choose a file...</option>';
    
    files.forEach(file => {
        const option = document.createElement('option');
        option.value = file.name;
        option.textContent = `${file.name} (${formatFileSize(file.size)}) - ${file.modified}`;
        select.appendChild(option);
    });
}

// Results Display
function showResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    const downloadBtn = document.getElementById('downloadBtn');
    
    // Update button based on output type
    if (data.sheet_url) {
        downloadBtn.innerHTML = '<i class="fab fa-google me-2"></i>Open Google Sheet';
        downloadBtn.onclick = () => window.open(data.sheet_url, '_blank');
        downloadBtn.classList.remove('btn-success');
        downloadBtn.classList.add('btn-primary');
    } else {
        downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Download Excel File';
        downloadBtn.onclick = () => downloadFile(data.output_filename);
        downloadBtn.classList.remove('btn-primary');
        downloadBtn.classList.add('btn-success');
    }
    
    // Generate results HTML
    let html = `
        <div class="results-summary">
            <h6><i class="fas fa-chart-bar me-2"></i>Workout Summary</h6>
            <div class="summary-grid">
    `;
    
    const summary = data.data.summary;
    const workoutType = data.data.workout_type;
    
    // Add summary items
    html += `
        <div class="summary-item">
            <span class="value">${summary.total_distance}</span>
            <span class="label">Total Distance</span>
        </div>
        <div class="summary-item">
            <span class="value">${summary.total_time}</span>
            <span class="label">Total Time</span>
        </div>
        <div class="summary-item">
            <span class="value">${summary.average_split}</span>
            <span class="label">Average Split</span>
        </div>
        <div class="summary-item">
            <span class="value">${summary.average_rate}</span>
            <span class="label">Average Rate</span>
        </div>
    `;
    
    if (summary.average_hr) {
        html += `
            <div class="summary-item">
                <span class="value">${summary.average_hr}</span>
                <span class="label">Average HR</span>
            </div>
        `;
    }
    
    if (workoutType === 'interval' && summary.total_intervals) {
        html += `
            <div class="summary-item">
                <span class="value">${summary.total_intervals}</span>
                <span class="label">Total Intervals</span>
            </div>
            <div class="summary-item">
                <span class="value">${summary.rest_time}</span>
                <span class="label">Rest Time</span>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    // Add detailed data table
    if (workoutType === 'interval') {
        html += generateIntervalTable(data.data.intervals);
    } else {
        html += generateSplitsTable(data.data.splits);
    }
    
    resultsContent.innerHTML = html;
    resultsSection.classList.remove('d-none');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function generateSplitsTable(splits) {
    let html = `
        <div class="table-container">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Split #</th>
                            <th>Distance</th>
                            <th>Time</th>
                            <th>Split</th>
                            <th>Rate</th>
                            <th>HR</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    splits.forEach((split, index) => {
        html += `
            <tr>
                <td>${split.split_number}</td>
                <td>${split.split_distance}</td>
                <td>${split.split_time}</td>
                <td>${split.split_pace}</td>
                <td>${split.rate}</td>
                <td>${split.hr || 'N/A'}</td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

function generateIntervalTable(intervals) {
    let html = `
        <div class="table-container">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Interval #</th>
                            <th>Distance</th>
                            <th>Time</th>
                            <th>Split</th>
                            <th>Rate</th>
                            <th>HR</th>
                            <th>Rest</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    intervals.forEach((interval, index) => {
        html += `
            <tr>
                <td>${interval.interval_number}</td>
                <td>${interval.interval_distance}</td>
                <td>${interval.interval_time}</td>
                <td>${interval.interval_pace}</td>
                <td>${interval.rate}</td>
                <td>${interval.hr || 'N/A'}</td>
                <td>${interval.rest_time || 'N/A'}</td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

// Utility Functions
function showLoading(show) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const submitBtn = document.getElementById('submitBtn');
    
    if (show) {
        loadingSpinner.classList.remove('d-none');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    } else {
        loadingSpinner.classList.add('d-none');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-play me-2"></i>Process Workout';
    }
}

function showError(message) {
    const errorSection = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');
    
    errorMessage.textContent = message;
    errorSection.classList.remove('d-none');
    
    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
    document.getElementById('errorSection').classList.add('d-none');
}

function hideResults() {
    document.getElementById('resultsSection').classList.add('d-none');
}

function downloadFile(filename) {
    window.location.href = `/download/${filename}`;
}

function resetForm() {
    document.getElementById('uploadForm').reset();
    clearFile();
    hideResults();
    hideError();
    document.getElementById('existingFileSection').classList.add('d-none');
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
} 