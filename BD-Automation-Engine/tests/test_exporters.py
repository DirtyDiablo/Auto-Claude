"""
Unit tests for Exporters module.
Tests Notion CSV and n8n JSON export formatting.
"""

import sys
import json
import csv
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine2_ProgramMapping.scripts.exporters import (
    NotionCSVExporter,
    N8nWebhookExporter,
    export_batch,
)


# Sample job data for testing
SAMPLE_JOB = {
    "Job Title/Position": "Network Engineer",
    "Date Posted": "2025-01-10",
    "Location": "San Diego, CA",
    "Position Overview": "Support network infrastructure for DCGS program.",
    "Key Responsibilities": [
        "Design networks",
        "Maintain systems",
        "Troubleshoot issues",
    ],
    "Required Qualifications": ["CCNA", "5+ years experience", "TS/SCI clearance"],
    "Security Clearance": "TS/SCI",
    "Project Duration": "Contract",
    "Rate/Pay Rate": "$100/hour",
    "Program Hints": ["DCGS"],
    "Client Hints": ["Air Force"],
    "Technologies": ["Cisco", "Linux", "VMware"],
    "Certifications Required": ["CCNA", "Security+"],
    "_mapping": {
        "program_name": "AF DCGS - PACAF",
        "match_confidence": 0.85,
        "match_type": "direct",
        "bd_priority_score": 85,
        "priority_tier": "Hot",
        "signals": ["Location match", "DCGS keyword"],
        "secondary_candidates": ["AF DCGS - Langley"],
    },
    "_scoring": {
        "BD Priority Score": 85,
        "Priority Tier": "Hot",
        "Score Breakdown": {"base_score": 50, "clearance_boost": 25, "location_boost": 10},
        "Recommendations": ["Immediate outreach recommended"],
    },
}


class TestNotionCSVExporter:
    """Tests for Notion CSV export."""

    def test_exporter_creates_output_dir_on_export(self):
        """Should create output directory when exporting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "notion_output"
            exporter = NotionCSVExporter(str(output_dir))
            exporter.export_jobs([SAMPLE_JOB])
            assert output_dir.exists()

    def test_exporter_creates_csv_file(self):
        """Should create CSV file with jobs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = NotionCSVExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB], "test_export.csv")

            assert Path(result.file_path).exists()
            assert result.file_path.endswith(".csv")
            assert result.success

    def test_csv_has_header_row(self):
        """CSV should have header row with column names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = NotionCSVExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB])

            with open(result.file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)

            assert "Job Title" in header or "Job Title/Position" in header
            assert "Location" in header

    def test_csv_has_correct_columns(self):
        """CSV should have expected number of columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = NotionCSVExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB])

            with open(result.file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)

            assert len(header) == len(exporter.column_order)

    def test_csv_contains_job_data(self):
        """CSV should contain job field values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = NotionCSVExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB])

            with open(result.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "Network Engineer" in content
            assert "San Diego" in content

    def test_csv_handles_none_values(self):
        """Should handle None values gracefully."""
        job = {
            "Job Title/Position": "Engineer",
            "Location": None,
            "Position Overview": None,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = NotionCSVExporter(tmpdir)
            result = exporter.export_jobs([job])
            assert result.success

    def test_csv_multiple_jobs(self):
        """Should export multiple jobs."""
        jobs = [SAMPLE_JOB, {**SAMPLE_JOB, "Job Title/Position": "Systems Engineer"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = NotionCSVExporter(tmpdir)
            result = exporter.export_jobs(jobs)

            with open(result.file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            # Header + 2 data rows
            assert len(rows) == 3
            assert result.record_count == 2


class TestN8nWebhookExporter:
    """Tests for n8n JSON export."""

    def test_exporter_creates_output_dir_on_export(self):
        """Should create output directory when exporting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "n8n_output"
            exporter = N8nWebhookExporter(str(output_dir))
            exporter.export_jobs([SAMPLE_JOB])
            assert output_dir.exists()

    def test_exporter_creates_json_file(self):
        """Should create JSON file with jobs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = N8nWebhookExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB], "test_export.json")

            assert Path(result.file_path).exists()
            assert result.file_path.endswith(".json")
            assert result.success

    def test_json_is_valid(self):
        """Should create valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = N8nWebhookExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB])

            with open(result.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert isinstance(data, dict)

    def test_json_has_jobs_array(self):
        """JSON should have 'jobs' array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = N8nWebhookExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB])

            with open(result.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "jobs" in data
            assert isinstance(data["jobs"], list)
            assert len(data["jobs"]) == 1

    def test_json_has_metadata(self):
        """JSON should have metadata object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = N8nWebhookExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB])

            with open(result.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "metadata" in data
            assert "total_count" in data["metadata"]
            assert data["metadata"]["total_count"] == 1

    def test_json_jobs_have_mapping(self):
        """Jobs should have _mapping object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = N8nWebhookExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB])

            with open(result.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            job = data["jobs"][0]
            assert "_mapping" in job
            assert "program_name" in job["_mapping"]

    def test_json_jobs_have_scoring(self):
        """Jobs should have _scoring object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = N8nWebhookExporter(tmpdir)
            result = exporter.export_jobs([SAMPLE_JOB])

            with open(result.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            job = data["jobs"][0]
            assert "_scoring" in job

    def test_export_single_method(self):
        """export_single should return dict without writing file."""
        exporter = N8nWebhookExporter()
        payload = exporter.export_single(SAMPLE_JOB)

        assert isinstance(payload, dict)
        assert "_mapping" in payload
        assert "_scoring" in payload
        assert "_webhook_metadata" in payload


class TestExportBatch:
    """Tests for batch export function."""

    def test_export_batch_both_formats(self):
        """Should export to both Notion CSV and n8n JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = export_batch([SAMPLE_JOB], output_dir=tmpdir)

            assert "notion" in results
            assert "n8n" in results
            assert Path(results["notion"].file_path).exists()
            assert Path(results["n8n"].file_path).exists()

    def test_export_batch_notion_only(self):
        """Should export only Notion CSV when n8n disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = export_batch(
                [SAMPLE_JOB], output_dir=tmpdir, formats=["notion"]
            )

            assert "notion" in results
            assert "n8n" not in results

    def test_export_batch_n8n_only(self):
        """Should export only n8n JSON when Notion disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = export_batch(
                [SAMPLE_JOB], output_dir=tmpdir, formats=["n8n"]
            )

            assert "n8n" in results
            assert "notion" not in results
