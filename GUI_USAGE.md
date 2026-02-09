# UCSB Drawing File Mapper - GUI Tool

A web-based GUI for mapping drawing PDFs to sheet titles and generating renamed filenames.

## Quick Start with Docker

### Using Docker Compose (Recommended)

```bash
docker-compose up
```

Then open http://localhost:5000 in your browser.

### Using Docker Directly

```bash
docker build -t ucsb-drawings-gui .
docker run -p 5000:5000 ucsb-drawings-gui
```

### Local Development

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

## Workflow

### Step 1: Prepare Your Files

1. **Create a file list** from your drawing PDFs:
   ```bash
   ls *.pdf > files.txt
   ```
   Expected format (one filename per line):
   ```
   525_101_001.pdf
   525_101_002.pdf
   525_101_003.pdf
   ...
   ```

2. **Create a drawing index image**:
   - Take a screenshot or crop a PDF showing the drawing index/sheet list
   - Save as PNG, JPG, or PDF
   - Supported formats: PNG, JPG, JPEG, GIF, BMP, PDF

### Step 2: Use the GUI

1. Open http://localhost:5000
2. Upload the drawing index (screenshot or PDF)
3. Upload the file list (files.txt)
4. (Optional) Set "First Drawing Offset" if files 001-002 are cover/index pages
5. Click "Process Files"

### Step 3: Review Results

The tool will display a 4-column table:
| Column | Description |
|--------|-------------|
| Old Filename | Original filename |
| New Filename | Generated UCSB-convention filename |
| Sheet # | Sheet number from index (e.g., A1, L2) |
| Sheet Title | Sheet title from index |

## Input File Formats

### Drawing Index
- **PDF**: First page will be OCR'd (pdfplumber)
- **Image** (PNG/JPG/GIF/BMP): OCR'd using Tesseract

### File List
- Plain text file (.txt or .csv)
- One filename per line
- Lines starting with `#` are skipped (comments)
- Filenames should match pattern: `{locnum}_{drawnum}_{sequence}.pdf`

Example:
```
525_101_001.pdf
525_101_002.pdf
525_101_003.pdf
525_101_004.pdf
```

## Optional Parameters

### First Drawing Offset
- Set to the index of the first file that maps to the first index entry
- Default: 0 (first file is first drawing)
- Example: If 001-002 are cover/index, set to 2

## Output

The generated filenames follow UCSB naming convention:

```
{locnum}_{drawnum}_{print_order}_{sheet_number_normalized}.pdf
```

Example:
- Sheet `A3.5`, 6th drawing → `525_101_006_A_3_5.pdf`
- Sheet `L2`, 74th drawing → `235_108_074_L_2.pdf`

All dots, dashes, and spaces in sheet numbers become underscores.

## Technical Requirements

### Environment
- Docker (recommended)
- Python 3.11+ (for local development)
- Tesseract OCR (for image processing)

### Dependencies
- Flask 2.0+
- pdfplumber
- Pillow
- pytesseract
- Bootstrap 5 (CDN, included in templates)

## Troubleshooting

### "Could not extract text from drawing list"
- Ensure the image is clear and readable
- If using a screenshot, make sure the sheet list is visible
- For PDFs, verify it's a searchable/text-based PDF (not scanned image)
- Check that OCR is properly installed: `tesseract --version`

### "Could not parse any sheet entries"
- Verify the drawing index has the expected format:
  ```
  A-1        First Floor Plan
  A 2.5      Second Floor Ceiling
  A3.1       Roof Plan
  ```
  (Two or more spaces between sheet number and title)
- Try a cleaner crop of just the index portion
- Check OCR output with `--show-text` flag in CLI tool

### "Could not parse any filenames from file list"
- Verify file list is plain text, one filename per line
- Ensure filenames follow pattern: `{locnum}_{drawnum}_{sequence}.pdf`

## Limitations

- Index parsing expects 2+ spaces between sheet number and title
- Only handles single-column index layouts (not multi-column)
- Requires text-based PDFs (OCR needed for scanned images)
- File list must follow UCSB naming convention

## Next Steps

After mapping files in the GUI:
1. Use the displayed new filenames to rename your PDFs
2. The mapping table can be copied/exported for records
3. For database import, use the original CLI tool with `--csv` flag

## Support

For issues or feature requests, see the main README.md or check the CLI tool (`python ucsb_renamer.py --help`)
