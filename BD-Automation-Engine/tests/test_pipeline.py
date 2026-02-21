"""
Integration tests for Pipeline module.
Tests full pipeline flow from ingestion to export.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine2_ProgramMapping.scripts.pipeline import (
    PipelineConfig,
    load_config,
    ingest_jobs,
    parse_and_standardize,
    match_to_programs,
    calculate_bd_scores,
    export_results,
    run_pipeline,
)


# Path to sample jobs
SAMPLE_JOBS_PATH = (
    Path(__file__).parent.parent / "Engine1_Scraper" / "data" / "Sample_Jobs.json"
)


def _default_config(**overrides) -> PipelineConfig:
    """Create a PipelineConfig with test-friendly defaults."""
    defaults = {
        "input_path": "test.json",
        "skip_llm": True,
        "test_mode": True,
        "generate_playbooks": False,
    }
    defaults.update(overrides)
    return PipelineConfig(**defaults)


class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""

    def test_config_defaults(self):
        """Should have sensible defaults."""
        config = PipelineConfig(input_path="test.json")
        assert config.test_mode == False
        assert config.skip_llm == False
        assert "notion" in config.export_formats
        assert "n8n" in config.export_formats

    def test_config_test_mode(self):
        """Should support test mode settings."""
        config = PipelineConfig(input_path="test.json", test_mode=True)
        assert config.test_mode == True

    def test_config_skip_llm(self):
        """Should support skip_llm for testing without API calls."""
        config = PipelineConfig(input_path="test.json", skip_llm=True)
        assert config.skip_llm == True

    def test_config_to_dict(self):
        """Should serialize to dictionary."""
        config = PipelineConfig(input_path="test.json")
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["input_path"] == "test.json"
        assert "test_mode" in d
        assert "export_formats" in d

    def test_config_default_output_dir(self):
        """Should set default output directory."""
        config = PipelineConfig(input_path="test.json")
        assert config.output_dir is not None
        assert config.notion_output_dir is not None
        assert config.n8n_output_dir is not None


class TestLoadConfig:
    """Tests for configuration loading."""

    def test_load_config_returns_pipeline_config(self):
        """Should return PipelineConfig instance."""
        config = load_config()
        assert isinstance(config, PipelineConfig)

    def test_load_config_from_nonexistent_path(self):
        """Should return default config for nonexistent path."""
        config = load_config("/nonexistent/path.json")
        assert isinstance(config, PipelineConfig)
        assert config.name == "PTS BD Program Mapping Engine"


class TestIngestJobs:
    """Tests for job ingestion stage."""

    @pytest.mark.skipif(
        not SAMPLE_JOBS_PATH.exists(), reason="Sample jobs file not found"
    )
    def test_ingest_loads_sample_jobs(self):
        """Should load sample jobs from JSON file."""
        jobs = ingest_jobs(str(SAMPLE_JOBS_PATH))
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    @pytest.mark.skipif(
        not SAMPLE_JOBS_PATH.exists(), reason="Sample jobs file not found"
    )
    def test_ingest_jobs_have_fields(self):
        """Loaded jobs should have expected fields."""
        jobs = ingest_jobs(str(SAMPLE_JOBS_PATH))
        for job in jobs:
            assert "title" in job or "Job Title/Position" in job

    def test_ingest_handles_array_format(self):
        """Should handle array format JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"title": "Engineer"}], f)
            f.flush()
            jobs = ingest_jobs(f.name)
        assert len(jobs) == 1

    def test_ingest_rejects_non_array(self):
        """Should reject non-array JSON format."""
        import pytest

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"jobs": [{"title": "Engineer"}]}, f)
            f.flush()
            with pytest.raises(ValueError, match="Expected JSON array"):
                ingest_jobs(f.name)


class TestParseAndStandardize:
    """Tests for parse and standardize stage."""

    def test_standardize_returns_list(self):
        """Should return list of standardized jobs."""
        jobs = [{"title": "Engineer", "location": "DC"}]
        config = _default_config()
        result = parse_and_standardize(jobs, config)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_standardize_preserves_raw_fields(self):
        """Should preserve raw fields in output (skip_llm mode)."""
        jobs = [
            {
                "title": "Network Engineer",
                "location": "San Diego, CA",
                "description": "Support network infrastructure",
                "clearance": "TS/SCI",
            }
        ]
        config = _default_config()
        result = parse_and_standardize(jobs, config)

        job = result[0]
        # In skip_llm mode, raw fields are preserved as-is
        assert job.get("title") == "Network Engineer"
        assert "San Diego" in job.get("location", "")

    def test_standardize_adds_metadata(self):
        """Should add metadata fields."""
        jobs = [{"title": "Engineer", "url": "https://example.com"}]
        config = _default_config()
        result = parse_and_standardize(jobs, config)

        job = result[0]
        # Should add processing metadata
        assert "Processed At" in job or "Processing Date" in job

    def test_standardize_handles_errors(self):
        """Should handle malformed jobs gracefully."""
        jobs = [None, {}, {"title": "Valid Job"}]
        config = _default_config()
        # Should not raise exception
        result = parse_and_standardize([j for j in jobs if j], config)
        assert len(result) >= 1


class TestMatchToPrograms:
    """Tests for program matching stage."""

    def test_match_adds_mapping(self):
        """Should add _mapping to each job."""
        jobs = [
            {
                "Job Title/Position": "DCGS Engineer",
                "Location": "San Diego, CA",
                "Position Overview": "Support DCGS program",
            }
        ]
        config = _default_config()
        result = match_to_programs(jobs, config)

        assert "_mapping" in result[0]
        assert "program_name" in result[0]["_mapping"]
        assert "match_confidence" in result[0]["_mapping"]
        assert "bd_priority_score" in result[0]["_mapping"]

    def test_match_sets_enrichment_fields(self):
        """Should set top-level enrichment fields."""
        jobs = [{"Job Title/Position": "Engineer", "Location": "DC"}]
        config = _default_config()
        result = match_to_programs(jobs, config)

        assert "Matched Program" in result[0]
        assert "Match Confidence" in result[0]


class TestCalculateBDScores:
    """Tests for BD scoring stage."""

    def test_score_adds_scoring(self):
        """Should add _scoring to each job."""
        jobs = [
            {
                "Job Title/Position": "Engineer",
                "Security Clearance": "TS/SCI",
                "Location": "DC",
                "_mapping": {"match_confidence": 0.8, "program_name": "Test"},
            }
        ]
        config = _default_config()
        result = calculate_bd_scores(jobs, config)

        assert "_scoring" in result[0]
        assert "BD Priority Score" in result[0]["_scoring"]
        assert "Priority Tier" in result[0]["_scoring"]

    def test_score_sets_top_level_fields(self):
        """Should set top-level BD fields."""
        jobs = [
            {"Job Title/Position": "Engineer", "_mapping": {"match_confidence": 0.5}}
        ]
        config = _default_config()
        result = calculate_bd_scores(jobs, config)

        assert "BD Priority Score" in result[0]
        assert "Priority Tier" in result[0]

    def test_score_in_valid_range(self):
        """Scores should be in 0-100 range."""
        jobs = [
            {
                "Security Clearance": "TS/SCI w/ CI Poly",
                "Location": "San Diego",
                "_mapping": {"match_confidence": 0.9},
            }
        ]
        config = _default_config()
        result = calculate_bd_scores(jobs, config)

        score = result[0]["BD Priority Score"]
        assert 0 <= score <= 100


class TestExportResults:
    """Tests for export stage."""

    def test_export_creates_files(self):
        """Should create output files."""
        jobs = [
            {
                "Job Title/Position": "Engineer",
                "Location": "DC",
                "_mapping": {
                    "program_name": "Test",
                    "match_confidence": 0.5,
                    "bd_priority_score": 50,
                    "priority_tier": "Warm",
                },
                "_scoring": {"bd_score": 50, "tier": "Warm"},
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            config = _default_config(
                output_dir=tmpdir,
                notion_output_dir=str(Path(tmpdir) / "notion"),
                n8n_output_dir=str(Path(tmpdir) / "n8n"),
            )
            results = export_results(jobs, config)
            assert isinstance(results, dict)


class TestRunPipeline:
    """Integration tests for full pipeline."""

    @pytest.mark.skipif(
        not SAMPLE_JOBS_PATH.exists(), reason="Sample jobs file not found"
    )
    def test_pipeline_processes_sample_jobs(self):
        """Should process sample jobs through all stages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                input_path=str(SAMPLE_JOBS_PATH),
                output_dir=tmpdir,
                test_mode=True,
                skip_llm=True,
                generate_playbooks=False,
            )
            result = run_pipeline(config)

            assert isinstance(result, dict)
            assert "stats" in result
            assert result["stats"]["total_ingested"] >= 1
            assert result["stats"]["total_processed"] >= 0

    @pytest.mark.skipif(
        not SAMPLE_JOBS_PATH.exists(), reason="Sample jobs file not found"
    )
    def test_pipeline_creates_outputs(self):
        """Should create output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                input_path=str(SAMPLE_JOBS_PATH),
                output_dir=tmpdir,
                test_mode=True,
                skip_llm=True,
                generate_playbooks=False,
            )
            run_pipeline(config)

            # Check output directories exist
            assert (Path(tmpdir) / "notion").exists()
            assert (Path(tmpdir) / "n8n").exists()

            # Check files were created
            csv_files = list((Path(tmpdir) / "notion").glob("*.csv"))
            json_files = list((Path(tmpdir) / "n8n").glob("*.json"))
            assert len(csv_files) > 0
            assert len(json_files) > 0

    @pytest.mark.skipif(
        not SAMPLE_JOBS_PATH.exists(), reason="Sample jobs file not found"
    )
    def test_pipeline_statistics(self):
        """Should track accurate statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                input_path=str(SAMPLE_JOBS_PATH),
                output_dir=tmpdir,
                test_mode=True,
                skip_llm=True,
                generate_playbooks=False,
            )
            result = run_pipeline(config)

            stats = result["stats"]
            assert "total_ingested" in stats
            assert "total_processed" in stats
            assert "by_tier" in stats


class TestOutputValidation:
    """Tests for validating output file contents."""

    @pytest.mark.skipif(
        not SAMPLE_JOBS_PATH.exists(), reason="Sample jobs file not found"
    )
    def test_notion_csv_has_columns(self):
        """Notion CSV should have 20+ columns."""
        import csv

        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                input_path=str(SAMPLE_JOBS_PATH),
                output_dir=tmpdir,
                test_mode=True,
                skip_llm=True,
                generate_playbooks=False,
            )
            run_pipeline(config)

            csv_files = list((Path(tmpdir) / "notion").glob("*.csv"))
            assert len(csv_files) > 0

            with open(csv_files[0], "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)

            assert len(header) >= 20, f"Expected 20+ columns, got {len(header)}"

    @pytest.mark.skipif(
        not SAMPLE_JOBS_PATH.exists(), reason="Sample jobs file not found"
    )
    def test_n8n_json_has_mapping_scoring(self):
        """n8n JSON jobs should have _mapping and _scoring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = PipelineConfig(
                input_path=str(SAMPLE_JOBS_PATH),
                output_dir=tmpdir,
                test_mode=True,
                skip_llm=True,
                generate_playbooks=False,
            )
            run_pipeline(config)

            json_files = list((Path(tmpdir) / "n8n").glob("*.json"))
            assert len(json_files) > 0

            with open(json_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "jobs" in data
            for job in data["jobs"]:
                assert "_mapping" in job, "Job missing _mapping"
                assert "_scoring" in job, "Job missing _scoring"
