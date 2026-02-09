# UCSB Drawing File Renamer - Project Wiki

## Project Goals

1. **Replace the Google Sheets workflow** for adding metadata to scanned UCSB record drawings with a standalone, repeatable CLI tool
2. **Automate file renaming** from generic sequential names (`525_101_001.pdf`) to the UCSB naming convention (`525_101_001_G_001.pdf`) using data extracted from drawing index sheets
3. **Generate CSV output** matching the `draw` database table schema for direct import via phpMyAdmin
4. **Reduce manual data entry** by programmatically extracting sheet numbers, titles, and discipline codes from PDF drawing index pages
5. **Maintain consistency** across 52,000+ existing drawing records by enforcing the standard naming convention

## Methods of Automating Metadata Collection

### Currently Implemented

| Metadata Field    | Source                          | Method                                              |
|-------------------|---------------------------------|-----------------------------------------------------|
| LocationNumber    | Folder name / input filename    | Parsed from first 3+ digits of filename             |
| DrawingNumber     | Input filename                  | Parsed from second 3+ digit group in filename       |
| Print Order       | Input filename                  | Parsed from third 3+ digit group (sequential order) |
| SheetNumber       | Drawing index page (PDF)        | Text extraction via pdfplumber, regex parsing        |
| SheetTitle        | Drawing index page (PDF)        | Text extraction, auto-converted to Title Case       |
| Discipline        | Sheet number prefix             | Derived from letter prefix (A=Architectural, etc.)  |
| NewName           | All above fields combined       | Auto-generated per UCSB naming convention           |

### Planned / Potential Automation

| Metadata Field    | Potential Source                | Approach                                            |
|-------------------|---------------------------------|-----------------------------------------------------|
| ProjectTitle      | Project records / folder meta   | Could cross-reference existing `drawfile` table     |
| DrawingDate       | PDF metadata / project records  | Extract from PDF creation date or file properties   |
| Keywords          | Sheet titles + OCR              | Auto-generate from sheet titles and content         |
| ContractNumber    | Project records                 | Lookup from existing project database               |

### Index Sheet Parsing Strategy

The drawing index sheet (typically page 2 of a set) contains a table of sheet numbers and titles. The tool handles various formatting inconsistencies from different consulting firms:

- **Separator variations**: `A-1.01`, `A 1.01`, `A1.01` all normalize to `A_1_01`
- **Case normalization**: `FIRST FLOOR PLAN` becomes `First Floor Plan`
- **Multi-letter disciplines**: `FP1.01` (Fire Protection) parsed correctly
- **Fallback**: When PDF text extraction fails (raster scans), user can paste index text from a file

### Auto-Detection

The tool auto-detects the offset between file numbering and index entries. For example, if a set has 50 files and 48 index entries, it infers that the first 2 files (cover + index) precede the actual drawings.

## Technology Stack

### Current

| Technology      | Purpose                              | Why                                                  |
|-----------------|--------------------------------------|------------------------------------------------------|
| **Python 3**    | Core language                        | Widely available, strong text processing, existing ecosystem in this project |
| **pdfplumber**  | PDF text extraction                  | Best layout-preserving text extraction for tabular PDF content; handles the columnar format of drawing indexes well |
| **argparse**    | CLI interface                        | Standard library, no extra dependencies; sufficient for the current option set |
| **csv**         | CSV generation                       | Standard library; generates output compatible with phpMyAdmin import |
| **re**          | Regex parsing                        | Standard library; handles the variety of sheet number formats across consulting firms |
| **pathlib**     | File system operations               | Standard library; clean API for path manipulation and file renaming |
| **pytest**      | Testing                             | Already used in the parent project; 45 tests covering parsing, normalization, mapping, and CSV export |

### Database (Existing)

| Technology       | Purpose                             | Why                                                  |
|------------------|--------------------------------------|------------------------------------------------------|
| **MySQL/InnoDB** | Production database                  | Existing infrastructure with 52,625 records          |
| **phpMyAdmin**   | Database management / CSV import     | Existing workflow for bulk record insertion           |

### Under Consideration

| Technology        | Potential Use                       | Tradeoffs                                            |
|-------------------|--------------------------------------|------------------------------------------------------|
| **Tesseract OCR** | Extract text from raster/scanned PDFs | Would handle older scanned drawings where pdfplumber can't extract text; adds complexity and dependency |
| **SQLAlchemy**    | Direct database writes               | Would eliminate the CSV + phpMyAdmin step; already used in the Flask app |
| **Click**         | Enhanced CLI                         | Richer CLI features (prompts, colors, progress bars); adds a dependency vs argparse |

---

## Human Notes

_This section is for project owner notes, TODOs, bugs, and preferred technologies._

### TODOs

-

### Bugs

-

### Preferred Technologies

-

### Other Notes

-
