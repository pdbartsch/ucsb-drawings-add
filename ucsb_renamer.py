#!/usr/bin/env python3
"""UCSB Drawing File Renamer

Takes a folder of extracted PDF drawing pages, parses the drawing index sheet,
and renames files to UCSB naming convention. Generates CSV for database import.

Naming convention:
    {locnum}_{drawnum}_{print_order}_{sheet_number_normalized}.pdf

    Sheet A3.5, 6th drawing in set 525-101:
        525_101_006_A_3_5.pdf

    Sheet L2, 74th drawing in set 235-108:
        235_108_074_L_2.pdf

All dots, dashes, and spaces in sheet numbers become underscores.
Underscores are the only special character allowed in output filenames.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

try:
    import pdfplumber

    HAS_PDF = True
except (ImportError, Exception):
    HAS_PDF = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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

VALID_EXTENSIONS = {".pdf"}


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------


def parse_input_filename(filename):
    """Parse an input filename like '525_101_003.pdf'.

    Returns dict with locnum, drawnum, print_order, ext or None if no match.
    """
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
# Sheet number handling
# ---------------------------------------------------------------------------


def normalize_sheet_number(sheet_num):
    """Convert sheet number to UCSB underscore-delimited format.

    All non-alphanumeric separators become underscores. Letter/digit
    boundaries also get underscores.

    A3.5   -> A_3_5
    A-2.05 -> A_2_05
    L2     -> L_2
    C1.1   -> C_1_1
    FP1.01 -> FP_1_01
    A 2_5  -> A_2_5
    """
    tokens = re.findall(r"[A-Za-z]+|\d+", sheet_num)
    return "_".join(t.upper() if t.isalpha() else t for t in tokens)


def get_discipline(sheet_num):
    """Extract discipline code and full name from a sheet number."""
    match = re.match(r"^([A-Za-z]+)", sheet_num)
    if match:
        code = match.group(1).upper()
        name = DISCIPLINES.get(code, "Unknown")
        return code, name
    return "", "Unknown"


# ---------------------------------------------------------------------------
# Drawing index parsing
# ---------------------------------------------------------------------------


def parse_index_text(text):
    """Parse drawing index text into (sheet_number, sheet_title) pairs.

    Handles various formats from different consulting firms:
        A-1.01   First Floor Plan
        A 2.5    Second Floor Reflected Ceiling
        C1.1     Site Plan
        L-1      Landscape Plan
    """
    entries = []

    # Match: 1-3 discipline letters, optional separator, number part,
    # then at least 2 whitespace chars before the title.
    pattern = re.compile(
        r"^\s*"
        r"([A-Za-z]{1,3})"  # discipline letters
        r"[\s\-\.]*"  # optional separator
        r"(\d+(?:[\.\-_\s]\d+)*)"  # number groups
        r"\s{2,}"  # column separator (2+ spaces)
        r"(.+?)\s*$"  # title text
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
# PDF text extraction
# ---------------------------------------------------------------------------


def extract_text_from_pdf(pdf_path, page_num=0):
    """Extract text from a specific page of a PDF (0-indexed)."""
    if not HAS_PDF:
        print(
            "Error: pdfplumber is required for PDF text extraction.\n"
            "Install with: pip install pdfplumber",
            file=sys.stderr,
        )
        sys.exit(1)

    with pdfplumber.open(pdf_path) as pdf:
        if page_num >= len(pdf.pages):
            raise ValueError(
                f"PDF has {len(pdf.pages)} pages, cannot access page {page_num + 1}"
            )
        return pdf.pages[page_num].extract_text() or ""


# ---------------------------------------------------------------------------
# New filename generation
# ---------------------------------------------------------------------------


def build_new_filename(locnum, drawnum, print_order, sheet_number, ext):
    """Build UCSB standard filename.

    Example: 525_101_006_A_3_5.pdf
    """
    normalized = normalize_sheet_number(sheet_number)
    return f"{locnum}_{drawnum}_{print_order}_{normalized}{ext}"


# ---------------------------------------------------------------------------
# Folder scanning
# ---------------------------------------------------------------------------


def scan_folder(folder_path):
    """Scan folder for drawing PDF files, sorted by name."""
    folder = Path(folder_path)
    recognized = []
    unrecognized = []

    for f in sorted(folder.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in VALID_EXTENSIONS:
            continue

        parsed = parse_input_filename(f.name)
        if parsed:
            recognized.append(parsed)
        else:
            unrecognized.append(f.name)

    return recognized, unrecognized


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def print_preview_table(mappings):
    """Print a formatted preview of proposed renames."""
    if not mappings:
        return

    w_order = 6
    w_old = max(len(m["original"]) for m in mappings) + 2
    w_new = max((len(m.get("newname", "---")) for m in mappings), default=20) + 2
    w_sheet = 12
    w_title = 30

    header = (
        f"{'#':<{w_order}}"
        f"{'Original':<{w_old}}"
        f"{'New Name':<{w_new}}"
        f"{'Sheet':<{w_sheet}}"
        f"{'Title':<{w_title}}"
    )
    print(header)
    print("-" * len(header))

    for i, m in enumerate(mappings, 1):
        newname = m.get("newname", m["original"])
        changed = " *" if newname != m["original"] else ""
        print(
            f"{i:<{w_order}}"
            f"{m['original']:<{w_old}}"
            f"{newname:<{w_new}}"
            f"{m.get('sheet_number', '---'):<{w_sheet}}"
            f"{m.get('sheet_title', '---'):<{w_title}}"
            f"{changed}"
        )


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


def export_csv(
    mappings,
    output_path,
    project_title="",
    drawing_date="",
    keywords="",
    notes="",
    contract_number="",
):
    """Export mappings to CSV for phpMyAdmin import into the `draw` table.

    Schema:
        ID              int AUTO_INCREMENT (omitted, DB generates it)
        NewName         varchar(255)   -- the renamed PDF filename
        LocationNumber  int
        DrawingNumber   float          -- e.g. 101 or 101.1
        ProjectTitle    varchar(255)
        DrawingDate     int            -- year as integer
        SheetTitle      varchar(255)
        Keywords        text
        SheetNumber     varchar(50)
        Discipline      varchar(100)
        Notes           varchar(500)   -- optional free-text notes
        ContractNumber  varchar(30)    -- optional contract number
    """
    fieldnames = [
        "NewName",
        "LocationNumber",
        "DrawingNumber",
        "ProjectTitle",
        "DrawingDate",
        "SheetTitle",
        "Keywords",
        "SheetNumber",
        "Discipline",
        "Notes",
        "ContractNumber",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for m in mappings:
            _code, disc_name = get_discipline(m.get("sheet_number", ""))
            writer.writerow(
                {
                    "NewName": m.get("newname", m["original"]),
                    "LocationNumber": int(m["locnum"]) if m.get("locnum") else "",
                    "DrawingNumber": (
                        float(m["drawnum"]) if m.get("drawnum") else ""
                    ),
                    "ProjectTitle": project_title,
                    "DrawingDate": drawing_date,
                    "SheetTitle": m.get("sheet_title", ""),
                    "Keywords": keywords,
                    "SheetNumber": m.get("sheet_number", ""),
                    "Discipline": disc_name,
                    "Notes": notes[:500] if notes else "",
                    "ContractNumber": contract_number[:30] if contract_number else "",
                }
            )

    print(f"\nCSV written to: {output_path}")


# ---------------------------------------------------------------------------
# Core rename logic
# ---------------------------------------------------------------------------


def build_mappings(recognized_files, index_entries, first_drawing):
    """Match files to index entries and build rename mappings.

    Args:
        recognized_files: Parsed file dicts sorted by print_order.
        index_entries: List of (sheet_number, sheet_title) from the index.
        first_drawing: 1-based print order of the first file that maps to
                       the first index entry.

    Returns:
        List of mapping dicts with newname, sheet_number, sheet_title added.
    """
    mappings = []

    for f in recognized_files:
        mapping = dict(f)
        order_num = int(f["print_order"])

        if index_entries and first_drawing is not None and order_num >= first_drawing:
            idx = order_num - first_drawing
            if idx < len(index_entries):
                sheet_num, sheet_title = index_entries[idx]
                mapping["sheet_number"] = sheet_num
                mapping["sheet_title"] = sheet_title
                mapping["newname"] = build_new_filename(
                    f["locnum"], f["drawnum"], f["print_order"], sheet_num, f["ext"]
                )

        if "newname" not in mapping:
            mapping["newname"] = f["original"]

        mappings.append(mapping)

    return mappings


def auto_detect_first_drawing(recognized_files, index_entries):
    """Try to detect which file is the first drawing matching the index.

    Checks common offsets (files 1, 2, 3 as non-drawing pages like
    cover sheet, index page, etc.).
    """
    n_files = len(recognized_files)
    n_entries = len(index_entries)

    if n_entries == 0:
        return None

    for offset in range(0, min(6, n_files)):
        remaining = n_files - offset
        if remaining == n_entries:
            first_order = int(recognized_files[offset]["print_order"])
            return first_order

    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="UCSB Drawing File Renamer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s ./525                           Preview with auto-detected index
  %(prog)s ./525 --index-page 2            Index is on page 2
  %(prog)s ./525 --index-file index.txt    Use pasted index text from file
  %(prog)s ./525 --rename --csv out.csv    Rename files and generate CSV
  %(prog)s ./525 --first-drawing 3         First drawing is file 003

workflow:
  1. Extract pages from a multi-page PDF into a folder
  2. Name files as {locnum}_{drawset}_{sequence}.pdf
  3. Run this tool to preview renames
  4. Add --rename to execute, --csv to export for database
""",
    )

    parser.add_argument("folder", help="Folder containing extracted drawing PDFs")
    parser.add_argument(
        "--index-page",
        type=int,
        default=2,
        help="Which file number contains the drawing index (default: 2)",
    )
    parser.add_argument(
        "--index-file",
        type=str,
        help="Path to text file or PDF with index content (instead of auto-detection)",
    )
    parser.add_argument(
        "--first-drawing",
        type=int,
        default=None,
        help="Print order of first file matching first index entry (auto-detected if omitted)",
    )
    parser.add_argument(
        "--rename",
        action="store_true",
        help="Actually rename files (default is dry-run preview)",
    )
    parser.add_argument(
        "--csv", type=str, help="Output CSV file path for database import"
    )
    parser.add_argument(
        "--project-title", type=str, default="", help="ProjectTitle for CSV export"
    )
    parser.add_argument(
        "--drawing-date",
        type=str,
        default="",
        help="DrawingDate (year as integer, e.g. 2024) for CSV export",
    )
    parser.add_argument(
        "--keywords", type=str, default="", help="Keywords for CSV export"
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Notes for CSV export (max 500 chars)",
    )
    parser.add_argument(
        "--contract-number",
        type=str,
        default="",
        help="Contract number for CSV export (max 30 chars)",
    )
    parser.add_argument(
        "--show-text",
        action="store_true",
        help="Print extracted index text for debugging",
    )

    args = parser.parse_args()
    folder = Path(args.folder)

    if not folder.is_dir():
        print(f"Error: '{folder}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # --- Scan folder ---
    print(f"\nScanning: {folder.resolve()}")
    recognized, unrecognized = scan_folder(folder)

    if not recognized:
        print("No recognized drawing files found.", file=sys.stderr)
        print(
            "Expected filenames like: 525_101_001.pdf (locnum_drawset_sequence.pdf)",
            file=sys.stderr,
        )
        if unrecognized:
            print(f"\nUnrecognized files in folder:", file=sys.stderr)
            for name in unrecognized:
                print(f"  {name}", file=sys.stderr)
        sys.exit(1)

    if unrecognized:
        print(f"\nUnrecognized files (skipped):")
        for name in unrecognized:
            print(f"  {name}")

    locnum = recognized[0]["locnum"]
    drawnum = recognized[0]["drawnum"]
    print(f"\nFound {len(recognized)} drawing files")
    print(f"Location: {locnum}, Drawing Set: {drawnum}")

    # --- Extract drawing index ---
    index_entries = []
    index_text = ""

    if args.index_file:
        index_path = Path(args.index_file)
        if index_path.suffix.lower() == ".pdf":
            print(f"\nExtracting index from PDF: {index_path.name}")
            index_text = extract_text_from_pdf(index_path, page_num=0)
        else:
            print(f"\nReading index from text file: {index_path.name}")
            index_text = index_path.read_text()
    else:
        # Find the file matching --index-page
        index_page_order = f"{args.index_page:03d}"
        index_pdf = None

        for f in recognized:
            if f["print_order"] == index_page_order:
                index_pdf = folder / f["original"]
                break

        if index_pdf and index_pdf.suffix.lower() == ".pdf":
            print(f"\nExtracting index from: {index_pdf.name} (page {args.index_page})")
            try:
                index_text = extract_text_from_pdf(index_pdf, page_num=0)
            except Exception as e:
                print(f"Warning: Could not extract text: {e}", file=sys.stderr)
        else:
            print(
                f"\nNo PDF found at page {args.index_page}. "
                "Use --index-file to provide index content.",
                file=sys.stderr,
            )

    if args.show_text and index_text:
        print(f"\n--- Extracted text ---\n{index_text}\n--- End ---")

    if index_text:
        index_entries = parse_index_text(index_text)

    if index_entries:
        print(f"\nParsed {len(index_entries)} index entries:")
        for i, (num, title) in enumerate(index_entries, 1):
            print(f"  {i:3d}. {num:<12s} {title}")
    else:
        print("\nNo index entries found. Use --show-text to debug extraction.")
        print("Files will keep their original names in the preview.")

    # --- Determine first drawing offset ---
    first_drawing = args.first_drawing

    if first_drawing is None and index_entries:
        first_drawing = auto_detect_first_drawing(recognized, index_entries)
        if first_drawing is not None:
            print(f"\nAuto-detected: first drawing at file #{first_drawing:03d}")
        else:
            print(
                f"\nCould not auto-detect first drawing offset."
                f"\n  Files: {len(recognized)}, Index entries: {len(index_entries)}"
                f"\n  Use --first-drawing N to specify manually."
            )

    # --- Build mappings ---
    mappings = build_mappings(recognized, index_entries, first_drawing)

    rename_count = sum(1 for m in mappings if m["newname"] != m["original"])

    print(f"\n{'=' * 80}")
    print(f"PROPOSED RENAMES ({rename_count} of {len(mappings)} files)")
    print(f"{'=' * 80}")
    print_preview_table(mappings)

    # --- Rename files ---
    if args.rename:
        if rename_count == 0:
            print("\nNothing to rename.")
        else:
            print(f"\nRenaming {rename_count} files...")
            for m in mappings:
                if m["newname"] != m["original"]:
                    src = folder / m["original"]
                    dst = folder / m["newname"]
                    if dst.exists():
                        print(f"  SKIP (already exists): {m['newname']}")
                    else:
                        src.rename(dst)
                        print(f"  {m['original']} -> {m['newname']}")
            print("Done.")
    else:
        if rename_count > 0:
            print(f"\nDry run. Use --rename to actually rename files.")

    # --- CSV export ---
    if args.csv:
        export_csv(
            mappings,
            args.csv,
            project_title=args.project_title,
            drawing_date=args.drawing_date,
            keywords=args.keywords,
            notes=args.notes,
            contract_number=args.contract_number,
        )


if __name__ == "__main__":
    main()
