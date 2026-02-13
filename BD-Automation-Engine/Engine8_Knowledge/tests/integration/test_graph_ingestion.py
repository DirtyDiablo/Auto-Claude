"""
Phase 21A — Graph Ingestion Engine Tests

Tests bulk data loading from CSV/API into Neo4j graph nodes and relationships.
Uses mocking — does not require running Neo4j or data files.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Engine8_Knowledge.graph.ingestion import (
    GraphIngestionEngine, LOCATION_COORDS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_mgr():
    mgr = MagicMock()
    mgr.run_batch.return_value = {
        "batches": 1,
        "total_records": 5,
        "nodes_created": 5,
        "properties_set": 25,
        "relationships_created": 3,
    }
    mgr.write_query.return_value = {
        "nodes_created": 1,
        "nodes_deleted": 0,
        "relationships_created": 1,
        "relationships_deleted": 0,
        "properties_set": 5,
    }
    return mgr


@pytest.fixture
def engine(mock_mgr):
    return GraphIngestionEngine(mock_mgr)


# ---------------------------------------------------------------------------
# TestIngestionEngine — init and stats
# ---------------------------------------------------------------------------

class TestIngestionEngineInit:
    """Test engine initialization."""

    def test_engine_creates_with_manager(self, mock_mgr):
        engine = GraphIngestionEngine(mock_mgr)
        assert engine._mgr is mock_mgr

    def test_reset_stats_zeroes_all(self, engine):
        engine._reset_stats()
        assert engine._stats["persons"] == 0
        assert engine._stats["companies"] == 0
        assert engine._stats["programs"] == 0
        assert engine._stats["jobs"] == 0
        assert engine._stats["locations"] == 0
        assert engine._stats["interactions"] == 0
        assert engine._stats["relationships"] == 0
        assert engine._stats["errors"] == 0
        assert engine._stats["skipped"] == 0


# ---------------------------------------------------------------------------
# TestContactIngestion
# ---------------------------------------------------------------------------

class TestContactIngestion:
    """Test contact CSV loading and ingestion."""

    def test_ingest_contacts_no_file(self, engine):
        with patch.object(Path, "exists", return_value=False):
            result = engine.ingest_contacts()
        assert result["status"] == "no_data"

    def test_ingest_contacts_with_data(self, engine, mock_mgr):
        csv_data = "name,title,email,phone,company,linkedin,program,tier,bd_priority,source_db,location\nAlice,Eng,alice@test.com,,Lockheed,,DCGS,1,High,csv,Herndon\nBob,PM,bob@test.com,,GDIT,,JSTARS,2,Medium,csv,McLean\n"
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            result = engine.ingest_contacts()
        assert result["status"] == "completed"
        assert result["ingested"] == 2
        mock_mgr.run_batch.assert_called_once()

    def test_ingest_contacts_with_limit(self, engine, mock_mgr):
        csv_data = "name,title,email\nAlice,Eng,alice@test.com\nBob,PM,bob@test.com\nCarol,Mgr,carol@test.com\n"
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            result = engine.ingest_contacts(limit=2)
        assert result["ingested"] == 2

    def test_load_contacts_csv_parses_fields(self, engine):
        csv_data = "name,title,email,phone,company,linkedin,program,tier,bd_priority,source_db,location\nJane Doe,Director,jane@doe.com,555-1234,Raytheon,linkedin.com/jane,DCGS,1,Critical,bullhorn,Fort Meade\n"
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            contacts = engine._load_contacts_csv()
        assert len(contacts) == 1
        assert contacts[0]["name"] == "Jane Doe"
        assert contacts[0]["company"] == "Raytheon"
        assert contacts[0]["tier"] == "1"

    def test_load_contacts_csv_handles_missing_file(self, engine):
        with patch.object(Path, "exists", return_value=False):
            contacts = engine._load_contacts_csv()
        assert contacts == []

    def test_load_contacts_csv_handles_read_error(self, engine):
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", side_effect=Exception("permission denied")):
            contacts = engine._load_contacts_csv()
        assert contacts == []


# ---------------------------------------------------------------------------
# TestProgramIngestion
# ---------------------------------------------------------------------------

class TestProgramIngestion:
    """Test federal program CSV loading and ingestion."""

    def test_ingest_programs_no_file(self, engine):
        with patch.object(Path, "exists", return_value=False):
            result = engine.ingest_programs()
        assert result["status"] == "no_data"

    def test_ingest_programs_with_data(self, engine, mock_mgr):
        csv_data = 'Program Name,Acronym,Contract Value,Agency Owner,Prime Contractor,Clearance Requirements,Program Type,Contract Vehicle,Hiring Velocity,Recompete Date,Confidence Level,Known Subcontractors\nDistributed Common Ground System,DCGS,$950M,Army,Northrop Grumman,TS/SCI,C5ISR,IDIQ,High,2027,High,"Leidos, Raytheon"\n'
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            result = engine.ingest_programs()
        assert result["status"] == "completed"
        assert result["ingested"] == 1
        # Should call run_batch for programs + write_query for each sub
        mock_mgr.run_batch.assert_called_once()
        # Two subcontractors: Leidos and Raytheon
        assert mock_mgr.write_query.call_count == 2

    def test_ingest_programs_no_subs(self, engine, mock_mgr):
        csv_data = 'Program Name,Acronym,Contract Value,Agency Owner,Prime Contractor,Clearance Requirements,Program Type,Contract Vehicle,Hiring Velocity,Recompete Date,Confidence Level,Known Subcontractors\nJSTARS,JSTARS,$2B,Air Force,GDIT,Secret,C5ISR,FFP,Medium,2028,Medium,\n'
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            result = engine.ingest_programs()
        assert result["status"] == "completed"
        # No subs = no write_query calls for subs
        mock_mgr.write_query.assert_not_called()

    def test_load_programs_csv_field_mapping(self, engine):
        csv_data = 'Program Name,Acronym,Contract Value,Agency Owner,Prime Contractor\nDCGS,DCGS,$950M,Army,Northrop Grumman\n'
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            progs = engine._load_programs_csv()
        assert len(progs) == 1
        assert progs[0]["acronym"] == "DCGS"
        assert progs[0]["agency_owner"] == "Army"
        assert progs[0]["prime_contractor"] == "Northrop Grumman"

    def test_ingest_programs_sub_error_increments_errors(self, engine, mock_mgr):
        csv_data = 'Program Name,Acronym,Contract Value,Agency Owner,Prime Contractor,Clearance Requirements,Program Type,Contract Vehicle,Hiring Velocity,Recompete Date,Confidence Level,Known Subcontractors\nDCGS,DCGS,$950M,Army,NG,TS/SCI,C5ISR,IDIQ,High,2027,High,"BadSub"\n'
        mock_mgr.write_query.side_effect = Exception("cypher error")
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            engine.ingest_programs()
        assert engine._stats["errors"] >= 1


# ---------------------------------------------------------------------------
# TestJobIngestion
# ---------------------------------------------------------------------------

class TestJobIngestion:
    """Test job ingestion from API."""

    def test_ingest_jobs_no_api(self, engine):
        with patch.object(engine, "_load_jobs_from_api", return_value=[]):
            result = engine.ingest_jobs()
        assert result["status"] == "no_data"

    def test_ingest_jobs_with_api_data(self, engine, mock_mgr):
        mock_jobs = [
            {"title": "SW Eng", "status": "Open", "clearance": "TS", "location": "McLean",
             "company": "Booz Allen", "program": "DCGS", "source_url": "", "bd_priority": "High",
             "functional_area": "Engineering", "date_added": "2026-01-01"},
        ]
        with patch.object(engine, "_load_jobs_from_api", return_value=mock_jobs):
            result = engine.ingest_jobs()
        assert result["status"] == "completed"
        assert result["ingested"] == 1
        mock_mgr.run_batch.assert_called_once()

    def test_load_jobs_from_api_success(self, engine):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jobs": [
                {"title": "Analyst", "clearance": "Secret", "company": "SAIC"},
            ]
        }
        with patch("Engine8_Knowledge.graph.ingestion.httpx") as mock_httpx:
            mock_httpx.get.return_value = mock_response
            jobs = engine._load_jobs_from_api(limit=10)
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Analyst"

    def test_load_jobs_from_api_failure(self, engine):
        with patch("Engine8_Knowledge.graph.ingestion.httpx") as mock_httpx:
            mock_httpx.get.side_effect = Exception("connection refused")
            jobs = engine._load_jobs_from_api()
        assert jobs == []


# ---------------------------------------------------------------------------
# TestInteractionIngestion
# ---------------------------------------------------------------------------

class TestInteractionIngestion:
    """Test interaction/notes ingestion."""

    def test_ingest_interactions_no_file(self, engine):
        with patch.object(Path, "exists", return_value=False):
            result = engine.ingest_interactions()
        assert result["status"] == "no_data"

    def test_ingest_interactions_with_data(self, engine, mock_mgr):
        csv_data = "date_added,type,action,status,note_body_clean,about,note_author\n2026-01-15,call,Follow-up,done,Discussed DCGS timeline,Jane Doe,John Smith\n"
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            result = engine.ingest_interactions()
        assert result["status"] == "completed"
        assert result["ingested"] == 1

    def test_load_interactions_csv_fields(self, engine):
        csv_data = "date_added,type,action,status,note_body_clean,about,note_author\n2026-01-15,call,Follow-up,done,Discussed timeline,Jane Doe,John Smith\n"
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=csv_data)):
            interactions = engine._load_interactions_csv()
        assert len(interactions) == 1
        assert interactions[0]["date"] == "2026-01-15"
        assert interactions[0]["type"] == "call"
        assert interactions[0]["about"] == "Jane Doe"
        assert interactions[0]["author"] == "John Smith"


# ---------------------------------------------------------------------------
# TestLocationIngestion
# ---------------------------------------------------------------------------

class TestLocationIngestion:
    """Test location node creation."""

    def test_ingest_locations_creates_all(self, engine, mock_mgr):
        result = engine.ingest_locations()
        assert result["status"] == "completed"
        assert result["ingested"] == len(LOCATION_COORDS)
        mock_mgr.run_batch.assert_called_once()

    def test_location_coords_not_empty(self):
        assert len(LOCATION_COORDS) >= 25

    def test_location_coords_are_valid(self):
        for name, (lat, lon) in LOCATION_COORDS.items():
            assert isinstance(lat, float), f"{name} lat not float"
            assert isinstance(lon, float), f"{name} lon not float"
            assert -90 <= lat <= 90, f"{name} lat out of range"
            assert -180 <= lon <= 180, f"{name} lon out of range"

    def test_location_batch_includes_military_flag(self, engine, mock_mgr):
        engine.ingest_locations()
        call_args = mock_mgr.run_batch.call_args
        batch = call_args[0][1]  # second positional arg
        fort_meade = next((l for l in batch if l["hub_name"] == "Fort Meade"), None)
        assert fort_meade is not None
        assert fort_meade["military"] is True
        herndon = next((l for l in batch if l["hub_name"] == "Herndon"), None)
        assert herndon is not None
        assert herndon["military"] is False


# ---------------------------------------------------------------------------
# TestIngestAll
# ---------------------------------------------------------------------------

class TestIngestAll:
    """Test full graph rebuild."""

    def test_ingest_all_calls_all_sources(self, engine):
        with patch.object(engine, "ingest_locations", return_value={"status": "completed"}) as m_loc, \
             patch.object(engine, "ingest_contacts", return_value={"status": "completed"}) as m_con, \
             patch.object(engine, "ingest_programs", return_value={"status": "completed"}) as m_prg, \
             patch.object(engine, "ingest_jobs", return_value={"status": "completed"}) as m_job, \
             patch.object(engine, "ingest_interactions", return_value={"status": "completed"}) as m_int:
            engine.ingest_all()
        m_loc.assert_called_once()
        m_con.assert_called_once()
        m_prg.assert_called_once()
        m_job.assert_called_once()
        m_int.assert_called_once()

    def test_ingest_all_includes_elapsed(self, engine):
        with patch.object(engine, "ingest_locations", return_value={"status": "completed"}), \
             patch.object(engine, "ingest_contacts", return_value={"status": "completed"}), \
             patch.object(engine, "ingest_programs", return_value={"status": "completed"}), \
             patch.object(engine, "ingest_jobs", return_value={"status": "completed"}), \
             patch.object(engine, "ingest_interactions", return_value={"status": "completed"}):
            result = engine.ingest_all()
        assert "elapsed_sec" in result
        assert "timestamp" in result

    def test_ingest_all_with_limit(self, engine):
        with patch.object(engine, "ingest_locations", return_value={"status": "completed"}), \
             patch.object(engine, "ingest_contacts", return_value={"status": "completed"}) as m_con, \
             patch.object(engine, "ingest_programs", return_value={"status": "completed"}) as m_prg, \
             patch.object(engine, "ingest_jobs", return_value={"status": "completed"}) as m_job, \
             patch.object(engine, "ingest_interactions", return_value={"status": "completed"}) as m_int:
            engine.ingest_all(limit=50)
        m_con.assert_called_once_with(50)
        m_prg.assert_called_once_with(50)
        m_job.assert_called_once_with(50)
        m_int.assert_called_once_with(50)
