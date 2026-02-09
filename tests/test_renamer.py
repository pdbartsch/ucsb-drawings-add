"""Tests for ucsb_renamer.py"""

import csv
import os
import tempfile
from pathlib import Path

import pytest

# Add parent dir to path so we can import the module
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ucsb_renamer import (
    auto_detect_first_drawing,
    build_mappings,
    build_new_filename,
    export_csv,
    get_discipline,
    normalize_sheet_number,
    parse_index_text,
    parse_input_filename,
    scan_folder,
)


# ---------------------------------------------------------------------------
# parse_input_filename
# ---------------------------------------------------------------------------


class TestParseInputFilename:
    def test_standard_3digit(self):
        result = parse_input_filename("525_101_006.pdf")
        assert result == {
            "locnum": "525",
            "drawnum": "101",
            "print_order": "006",
            "ext": ".pdf",
            "original": "525_101_006.pdf",
        }

    def test_leading_zeros(self):
        result = parse_input_filename("003_001_001.pdf")
        assert result["locnum"] == "003"
        assert result["drawnum"] == "001"
        assert result["print_order"] == "001"

    def test_no_match_too_few_parts(self):
        assert parse_input_filename("525_101.pdf") is None

    def test_no_match_letters(self):
        assert parse_input_filename("abc_101_006.pdf") is None

    def test_no_match_wrong_ext(self):
        # Still parses - extension is just captured, not validated here
        result = parse_input_filename("525_101_006.txt")
        assert result is not None
        assert result["ext"] == ".txt"

    def test_four_digit_locnum(self):
        result = parse_input_filename("1234_101_006.pdf")
        assert result["locnum"] == "1234"


# ---------------------------------------------------------------------------
# normalize_sheet_number
# ---------------------------------------------------------------------------


class TestNormalizeSheetNumber:
    def test_dot_separator(self):
        assert normalize_sheet_number("A3.5") == "A_3_5"

    def test_dash_separator(self):
        assert normalize_sheet_number("A-2.05") == "A_2_05"

    def test_no_separator(self):
        assert normalize_sheet_number("L2") == "L_2"

    def test_dot_separator_two_parts(self):
        assert normalize_sheet_number("C1.1") == "C_1_1"

    def test_multi_letter_discipline(self):
        assert normalize_sheet_number("FP1.01") == "FP_1_01"

    def test_space_separator(self):
        assert normalize_sheet_number("A 2_5") == "A_2_5"

    def test_preserves_zero_padding(self):
        assert normalize_sheet_number("A-2.05") == "A_2_05"

    def test_uppercase_output(self):
        assert normalize_sheet_number("a3.5") == "A_3_5"

    def test_complex_number(self):
        assert normalize_sheet_number("A-1.01") == "A_1_01"


# ---------------------------------------------------------------------------
# get_discipline
# ---------------------------------------------------------------------------


class TestGetDiscipline:
    def test_architectural(self):
        code, name = get_discipline("A3.5")
        assert code == "A"
        assert name == "Architectural"

    def test_civil(self):
        code, name = get_discipline("C1.1")
        assert code == "C"
        assert name == "Civil"

    def test_landscape(self):
        code, name = get_discipline("L2")
        assert code == "L"
        assert name == "Landscape"

    def test_fire_protection(self):
        code, name = get_discipline("FP1.01")
        assert code == "FP"
        assert name == "Fire Protection"

    def test_unknown(self):
        code, name = get_discipline("Z1")
        assert code == "Z"
        assert name == "Unknown"

    def test_empty(self):
        code, name = get_discipline("123")
        assert code == ""
        assert name == "Unknown"


# ---------------------------------------------------------------------------
# build_new_filename
# ---------------------------------------------------------------------------


class TestBuildNewFilename:
    def test_standard(self):
        result = build_new_filename("525", "101", "006", "A3.5", ".pdf")
        assert result == "525_101_006_A_3_5.pdf"

    def test_landscape(self):
        result = build_new_filename("235", "108", "074", "L2", ".pdf")
        assert result == "235_108_074_L_2.pdf"

    def test_civil(self):
        result = build_new_filename("300", "042", "012", "C1.1", ".pdf")
        assert result == "300_042_012_C_1_1.pdf"


# ---------------------------------------------------------------------------
# parse_index_text
# ---------------------------------------------------------------------------


class TestParseIndexText:
    def test_basic_index(self):
        text = """DRAWING INDEX
SHEET NO.          SHEET TITLE
G-001              Cover Sheet
G-002              Sheet Index
A-1.01             First Floor Plan
A-1.02             Second Floor Plan
A-2.01             Exterior Elevations
"""
        entries = parse_index_text(text)
        assert len(entries) == 5
        assert entries[0] == ("G001", "Cover Sheet")
        assert entries[2] == ("A1.01", "First Floor Plan")

    def test_no_separator_format(self):
        text = """C1.1     Site Plan
C1.2     Grading Plan
L1       Landscape Plan
"""
        entries = parse_index_text(text)
        assert len(entries) == 3
        assert entries[0] == ("C1.1", "Site Plan")
        assert entries[2] == ("L1", "Landscape Plan")

    def test_skips_headers(self):
        text = """Drawing Index
Sheet No.    Sheet Title
---          ---
A-1.01       Floor Plan
"""
        entries = parse_index_text(text)
        assert len(entries) == 1
        assert entries[0] == ("A1.01", "Floor Plan")

    def test_title_case(self):
        text = """A-1.01       FIRST FLOOR PLAN
A-1.02       second floor plan
"""
        entries = parse_index_text(text)
        assert entries[0][1] == "First Floor Plan"
        assert entries[1][1] == "Second Floor Plan"

    def test_empty_text(self):
        assert parse_index_text("") == []

    def test_no_matches(self):
        text = "This is just some random text with no drawing entries"
        assert parse_index_text(text) == []


# ---------------------------------------------------------------------------
# build_mappings
# ---------------------------------------------------------------------------


class TestBuildMappings:
    def _make_files(self, count, locnum="525", drawnum="101", start=1):
        return [
            {
                "locnum": locnum,
                "drawnum": drawnum,
                "print_order": f"{i:03d}",
                "ext": ".pdf",
                "original": f"{locnum}_{drawnum}_{i:03d}.pdf",
            }
            for i in range(start, start + count)
        ]

    def test_basic_mapping(self):
        files = self._make_files(5)
        index = [("G-001", "Cover"), ("G-002", "Index"), ("A-1.01", "Plan")]
        mappings = build_mappings(files, index, first_drawing=3)

        # Files 001, 002 keep original names
        assert mappings[0]["newname"] == "525_101_001.pdf"
        assert mappings[1]["newname"] == "525_101_002.pdf"
        # File 003 maps to first index entry
        assert mappings[2]["newname"] == "525_101_003_G_001.pdf"
        assert mappings[2]["sheet_title"] == "Cover"

    def test_no_index(self):
        files = self._make_files(3)
        mappings = build_mappings(files, [], first_drawing=None)
        for m in mappings:
            assert m["newname"] == m["original"]

    def test_first_drawing_offset(self):
        files = self._make_files(4)
        index = [("A-1.01", "Floor Plan"), ("A-2.01", "Elevations")]
        mappings = build_mappings(files, index, first_drawing=3)

        assert mappings[2]["sheet_number"] == "A-1.01"
        assert mappings[3]["sheet_number"] == "A-2.01"

    def test_more_files_than_index(self):
        files = self._make_files(10)
        index = [("A-1.01", "Plan")]
        mappings = build_mappings(files, index, first_drawing=3)

        # Only file 003 gets renamed
        assert "sheet_number" in mappings[2]
        assert "sheet_number" not in mappings[3]


# ---------------------------------------------------------------------------
# auto_detect_first_drawing
# ---------------------------------------------------------------------------


class TestAutoDetect:
    def _make_files(self, count, start=1):
        return [
            {
                "locnum": "525",
                "drawnum": "101",
                "print_order": f"{i:03d}",
                "ext": ".pdf",
                "original": f"525_101_{i:03d}.pdf",
            }
            for i in range(start, start + count)
        ]

    def test_offset_2(self):
        # 10 files, 8 index entries -> first drawing at file 003
        files = self._make_files(10)
        index = [("A", "t")] * 8
        result = auto_detect_first_drawing(files, index)
        assert result == 3  # print_order of files[2]

    def test_offset_1(self):
        files = self._make_files(10)
        index = [("A", "t")] * 9
        result = auto_detect_first_drawing(files, index)
        assert result == 2

    def test_exact_match(self):
        files = self._make_files(10)
        index = [("A", "t")] * 10
        result = auto_detect_first_drawing(files, index)
        assert result == 1

    def test_no_match(self):
        files = self._make_files(10)
        index = [("A", "t")] * 20
        result = auto_detect_first_drawing(files, index)
        assert result is None

    def test_empty_index(self):
        files = self._make_files(5)
        result = auto_detect_first_drawing(files, [])
        assert result is None


# ---------------------------------------------------------------------------
# scan_folder
# ---------------------------------------------------------------------------


class TestScanFolder:
    def test_scan_pdfs(self, tmp_path):
        # Create test PDF files
        (tmp_path / "525_101_001.pdf").write_text("fake pdf")
        (tmp_path / "525_101_002.pdf").write_text("fake pdf")
        (tmp_path / "525_101_003.pdf").write_text("fake pdf")

        recognized, unrecognized = scan_folder(tmp_path)
        assert len(recognized) == 3
        assert len(unrecognized) == 0
        assert recognized[0]["print_order"] == "001"

    def test_ignores_non_pdf(self, tmp_path):
        (tmp_path / "525_101_001.pdf").write_text("fake pdf")
        (tmp_path / "notes.txt").write_text("some notes")
        (tmp_path / "photo.jpg").write_text("fake jpg")

        recognized, unrecognized = scan_folder(tmp_path)
        assert len(recognized) == 1
        assert len(unrecognized) == 0  # non-PDFs are ignored entirely

    def test_unrecognized_pdf(self, tmp_path):
        (tmp_path / "525_101_001.pdf").write_text("fake pdf")
        (tmp_path / "random_name.pdf").write_text("fake pdf")

        recognized, unrecognized = scan_folder(tmp_path)
        assert len(recognized) == 1
        assert len(unrecognized) == 1
        assert unrecognized[0] == "random_name.pdf"

    def test_sorted_output(self, tmp_path):
        (tmp_path / "525_101_003.pdf").write_text("fake pdf")
        (tmp_path / "525_101_001.pdf").write_text("fake pdf")
        (tmp_path / "525_101_002.pdf").write_text("fake pdf")

        recognized, _ = scan_folder(tmp_path)
        orders = [f["print_order"] for f in recognized]
        assert orders == ["001", "002", "003"]


# ---------------------------------------------------------------------------
# export_csv
# ---------------------------------------------------------------------------


class TestExportCsv:
    def test_csv_columns_match_schema(self, tmp_path):
        mappings = [
            {
                "original": "525_101_001.pdf",
                "newname": "525_101_001_A_1_01.pdf",
                "locnum": "525",
                "drawnum": "101",
                "print_order": "001",
                "sheet_number": "A1.01",
                "sheet_title": "Floor Plan",
                "ext": ".pdf",
            }
        ]
        csv_path = tmp_path / "test.csv"
        export_csv(
            mappings,
            str(csv_path),
            project_title="Test Project",
            drawing_date="2024",
            keywords="test",
            notes="Some notes here",
            contract_number="C-99887",
        )

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        row = rows[0]

        # Verify all columns match the draw table schema
        expected_columns = {
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
        }
        assert set(row.keys()) == expected_columns

        assert row["NewName"] == "525_101_001_A_1_01.pdf"
        assert row["LocationNumber"] == "525"
        assert row["DrawingNumber"] == "101.0"
        assert row["ProjectTitle"] == "Test Project"
        assert row["DrawingDate"] == "2024"
        assert row["SheetTitle"] == "Floor Plan"
        assert row["Keywords"] == "test"
        assert row["SheetNumber"] == "A1.01"
        assert row["Discipline"] == "Architectural"
        assert row["Notes"] == "Some notes here"
        assert row["ContractNumber"] == "C-99887"

    def test_csv_notes_truncated(self, tmp_path):
        mappings = [
            {
                "original": "525_101_001.pdf",
                "newname": "525_101_001.pdf",
                "locnum": "525",
                "drawnum": "101",
                "print_order": "001",
                "ext": ".pdf",
            }
        ]
        csv_path = tmp_path / "test.csv"
        long_notes = "x" * 600
        long_contract = "y" * 50
        export_csv(
            mappings,
            str(csv_path),
            notes=long_notes,
            contract_number=long_contract,
        )

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert len(row["Notes"]) == 500
        assert len(row["ContractNumber"]) == 30
