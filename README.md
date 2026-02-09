````markdown
# UCSB Drawing File Renamer - Project Context

## What This Tool Does

Replaces a manual Google Sheets workflow for processing scanned UCSB campus construction/architectural drawings. The university has 52,000+ drawing records in a MySQL database.

## The Manual Workflow Being Replaced

1. Receive a multi-page PDF of a construction drawing set
2. Extract pages into individual files, named `{locnum}_{drawset}_{sequence}.pdf`
3. Put them in a folder named after the location number
4. Run `ls > files.txt`, paste into Google Sheets
5. Manually find the drawing index page (usually page 2), copy its text
6. Use Sheets formulas to parse sheet numbers and titles
7. Export CSV, import via phpMyAdmin into the `draw` table

## The Automated Workflow

```bash
python ucsb_renamer.py ./525 --rename --csv output.csv \
    --project-title "Library Renovation" --drawing-date 2024
```
````

The tool scans the folder, extracts text from the index PDF page, parses sheet numbers and titles, renames files, and exports a CSV ready for phpMyAdmin.

## UCSB Naming Convention

```
{locnum}_{drawnum}_{print_order}_{sheet_number_normalized}.pdf
```

- Sheet `A3.5`, 6th in set 525-101 → `525_101_006_A_3_5.pdf`
- Sheet `L2`, 74th in set 235-108 → `235_108_074_L_2.pdf`
- All dots, dashes, spaces in sheet numbers become underscores
- Letter/digit boundaries also get underscores

## Database Schema (`draw` table, MySQL/InnoDB)

| Column         | Type               | Notes                       |
| -------------- | ------------------ | --------------------------- |
| ID             | int AUTO_INCREMENT | DB generates                |
| NewName        | varchar(255)       | Renamed filename            |
| LocationNumber | int                | Building/site number        |
| DrawingNumber  | float              | Drawing set number          |
| ProjectTitle   | varchar(255)       |                             |
| DrawingDate    | int                | Year only                   |
| SheetTitle     | varchar(255)       | From index, Title Case      |
| Keywords       | text               |                             |
| SheetNumber    | varchar(50)        | Original format (e.g. A3.5) |
| Discipline     | varchar(100)       | Derived from sheet prefix   |
| Notes          | varchar(500)       |                             |
| ContractNumber | varchar(30)        |                             |

## Current State of the Code

- `ucsb_renamer.py` — working CLI, 45 passing tests
- Lives in `pdbartsch/ucsb-drawings-add` repo (local) and `pdbartsch/assign_draw_num` branch `claude/ucsb-drawing-file-renamer-ND8kW` (pushed)
- The user wants this to be a **standalone tool** in `pdbartsch/ucsb-drawings-add`, separate from the Flask app in `assign_draw_num`
- PR needs to be created on `ucsb-drawings-add` — push access was not available in the initial session

## Tips for Future Agents

### Environment

- **pdfplumber import can panic** (pyo3/cryptography issue in some environments). The import uses a broad `except (ImportError, Exception)` — don't narrow it
- **Git commit signing fails** — always run `git config --local commit.gpgsign false`
- **GitHub pushes intermittently 500/502/504** — retry with exponential backoff (2s, 4s, 8s, 16s)
- **Proxy authorization** is per-repo. Check `git remote -v` on an already-working repo to get the correct `http://local_proxy@127.0.0.1:{port}/git/` URL format

### Architecture Decisions

- Single-file script (`ucsb_renamer.py`), not a package — the user wants it simple and standalone
- `pdfplumber` is the only external dependency — keep it minimal
- Dry-run is the default; `--rename` flag required to actually rename files
- The `--index-file` flag accepts both `.txt` (pasted text) and `.pdf` (single-page extracted PDF)
- CSV output matches the exact `draw` table column names for direct phpMyAdmin import

### Known Limitations / Future Work

- Index text parsing uses a regex heuristic (`2+ spaces` between sheet number and title) — works for most consulting firms but may need tuning for unusual layouts
- No OCR support yet — only works with vector/text-based PDFs (Tesseract OCR is under consideration)
- No direct database writes — CSV + phpMyAdmin is the current workflow
- Multi-column index sheets (two columns of entries side by side) are not handled
- The tool assumes files are already extracted from the multi-page PDF and named correctly

### User Preferences

- The user manages UCSB campus drawings professionally
- They prefer practical tools over over-engineered solutions
- They use phpMyAdmin for database operations
- They want PRs, not direct pushes to main
- The code should eventually live in `pdbartsch/ucsb-drawings-add`, not `assign_draw_num`

```

```
