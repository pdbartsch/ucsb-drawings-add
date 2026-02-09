#!/usr/bin/env python3
"""UCSB Drawing GUI Tool - Web interface for mapping drawing files to sheet titles."""

import os
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import tempfile

try:
    import pdfplumber
    HAS_PDF = True
except (ImportError, Exception):
    HAS_PDF = False

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except (ImportError, Exception):
    HAS_OCR = False

# ---------------------------------------------------------------------------
# Flask Setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp'}
ALLOWED_TEXT_EXTENSIONS = {'.txt', '.csv'}

DISCIPLINES = {
    "A": "Architectural",
    "AD": "Architectural Demo",
    "C": "Civil",
    "D": "Demolition",
    "E": "Electrical",
    "EL": "Electrical",
    "F": "Fire Protection",
    "FP": "Fire Protection",
    "G": "General",
    "H": "Hazardous Materials",
    "I": "Interiors",
    "ID": "Interior Design",
    "IR": "Irrigation",
    "L": "Landscape",
    "M": "Mechanical",
    "P": "Plumbing",
    "S": "Structural",
    "T": "Telecommunications",
    "X": "Other",
}


# ---------------------------------------------------------------------------
# Filename Parsing
# ---------------------------------------------------------------------------


def parse_filename(filename):
    """Parse filename like '525_101_003.pdf' into components."""
    stem = Path(filename).stem
    ext = Path(filename).suffix

    match = re.match(r"^(\d{3,})_(\d{3,})_(\d{3,})$", stem)
    if match:
        return {
            "locnum": match.group(1),
            "drawnum": match.group(2),
            "print_order": match.group(3),
            "ext": ext,
            "original": filename,
        }
    return None


# ---------------------------------------------------------------------------
# Sheet Number Handling
# ---------------------------------------------------------------------------


def normalize_sheet_number(sheet_num):
    """Convert sheet number to UCSB underscore-delimited format."""
    tokens = re.findall(r"[A-Za-z]+|\d+", sheet_num)
    return "_".join(t.upper() if t.isalpha() else t for t in tokens)


def get_discipline(sheet_num):
    """Extract discipline code and full name from sheet number."""
    match = re.match(r"^([A-Za-z]+)", sheet_num)
    if match:
        code = match.group(1).upper()
        name = DISCIPLINES.get(code, "Unknown")
        return code, name
    return "", "Unknown"


# ---------------------------------------------------------------------------
# Drawing Index Parsing
# ---------------------------------------------------------------------------


def parse_index_text(text):
    """Parse drawing index text into (sheet_number, sheet_title) pairs."""
    entries = []

    pattern = re.compile(
        r"^\s*"
        r"([A-Za-z]{1,3})"
        r"[\s\-\.]*"
        r"(\d+(?:[\.\-_\s]\d+)*)"
        r"\s{2,}"
        r"(.+?)\s*$"
    )

    skip_phrases = [
        "drawing index",
        "sheet no",
        "sheet title",
        "abbreviat",
        "symbol",
        "legend",
        "---",
        "===",
        "table of contents",
    ]

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        lower = line.lower()
        if any(skip in lower for skip in skip_phrases):
            continue

        match = pattern.match(line)
        if match:
            letters = match.group(1)
            numbers = match.group(2).strip()
            title = match.group(3).strip()

            sheet_num = f"{letters}{numbers}"
            sheet_title = title.title()

            entries.append((sheet_num, sheet_title))

    return entries


# ---------------------------------------------------------------------------
# File Processing
# ---------------------------------------------------------------------------


def extract_text_from_pdf(pdf_path):
    """Extract text from first page of PDF."""
    if not HAS_PDF:
        return None
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                return pdf.pages[0].extract_text() or ""
    except Exception:
        pass
    return None


def extract_text_from_image(image_path):
    """Extract text from image using OCR."""
    if not HAS_OCR:
        return None
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception:
        pass
    return None


def extract_text_from_file(file_path):
    """Extract text from uploaded file (PDF or image)."""
    ext = Path(file_path).suffix.lower()

    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}:
        return extract_text_from_image(file_path)

    return None


def parse_file_list(file_path):
    """Parse text file containing list of filenames, one per line."""
    filenames = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    filenames.append(line)
    except Exception:
        pass
    return filenames


def build_new_filename(locnum, drawnum, print_order, sheet_number, ext):
    """Build UCSB standard filename."""
    normalized = normalize_sheet_number(sheet_number)
    return f"{locnum}_{drawnum}_{print_order}_{normalized}{ext}"


def build_mappings(file_list, index_entries, first_drawing_offset=0):
    """Match files to index entries and build mappings.

    Args:
        file_list: List of filenames to process
        index_entries: List of (sheet_number, sheet_title) tuples
        first_drawing_offset: Offset in file_list where first index entry appears

    Returns:
        List of mapping dicts with columns for the output table
    """
    mappings = []

    for i, filename in enumerate(file_list):
        parsed = parse_filename(filename)
        if not parsed:
            continue

        mapping = {
            "old_file_name": filename,
            "file_name": filename,
            "sheet_number": "",
            "sheet_title": "",
        }

        # Try to match to index entry
        index_idx = i - first_drawing_offset
        if 0 <= index_idx < len(index_entries):
            sheet_num, sheet_title = index_entries[index_idx]
            mapping["sheet_number"] = sheet_num
            mapping["sheet_title"] = sheet_title

            # Generate new filename
            new_filename = build_new_filename(
                parsed["locnum"],
                parsed["drawnum"],
                parsed["print_order"],
                sheet_num,
                parsed["ext"]
            )
            mapping["file_name"] = new_filename

        mappings.append(mapping)

    return mappings


# ---------------------------------------------------------------------------
# Flask Routes
# ---------------------------------------------------------------------------


@app.route('/')
def index():
    """Render upload form."""
    return render_template('index.html', has_ocr=HAS_OCR, has_pdf=HAS_PDF)


@app.route('/process', methods=['POST'])
def process():
    """Process uploaded files and return mappings."""
    try:
        # Validate files uploaded
        if 'drawing_list' not in request.files or 'file_list' not in request.files:
            return jsonify({'error': 'Missing required files'}), 400

        drawing_file = request.files['drawing_list']
        file_list_file = request.files['file_list']

        if drawing_file.filename == '' or file_list_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400

        # Validate file types
        drawing_ext = Path(drawing_file.filename).suffix.lower()
        file_list_ext = Path(file_list_file.filename).suffix.lower()

        if drawing_ext not in ALLOWED_EXTENSIONS:
            return jsonify({'error': f'Drawing file type not allowed: {drawing_ext}'}), 400

        if file_list_ext not in ALLOWED_TEXT_EXTENSIONS:
            return jsonify({'error': f'File list type not allowed: {file_list_ext}'}), 400

        # Save temporary files
        drawing_path = Path(app.config['UPLOAD_FOLDER']) / secure_filename(drawing_file.filename)
        file_list_path = Path(app.config['UPLOAD_FOLDER']) / secure_filename(file_list_file.filename)

        drawing_file.save(str(drawing_path))
        file_list_file.save(str(file_list_path))

        # Extract text from drawing list
        index_text = extract_text_from_file(str(drawing_path))
        if not index_text:
            return jsonify({'error': 'Could not extract text from drawing list'}), 400

        # Parse index
        index_entries = parse_index_text(index_text)
        if not index_entries:
            return jsonify({'error': 'Could not parse any sheet entries from drawing list'}), 400

        # Parse file list
        file_list = parse_file_list(str(file_list_path))
        if not file_list:
            return jsonify({'error': 'Could not parse any filenames from file list'}), 400

        # Get first_drawing offset from form
        first_drawing = request.form.get('first_drawing', 0, type=int)

        # Build mappings
        mappings = build_mappings(file_list, index_entries, first_drawing)

        # Clean up temp files
        drawing_path.unlink(missing_ok=True)
        file_list_path.unlink(missing_ok=True)

        return jsonify({
            'success': True,
            'mappings': mappings,
            'index_entries': [(num, title) for num, title in index_entries],
            'file_list_count': len(file_list),
            'index_entries_count': len(index_entries),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
