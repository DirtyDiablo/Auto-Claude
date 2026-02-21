"""Data ingestion router — single and batch record ingest to vector store."""

import json
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Request

from Engine8_Knowledge.models import (
    DocumentInput,
    ProgramInput,
    CompanyInput,
    ContactInput,
    JobInput,
)
from Engine8_Knowledge.deps import get_store, get_memory

logger = logging.getLogger("BDKnowledgeAPI")

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])


def _require_store():
    store = get_store()
    if not store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    return store


@router.post("/document")
def ingest_document(data: DocumentInput):
    """Ingest document to Qdrant documents collection via OpenAI embeddings."""
    store = _require_store()
    try:
        doc = {
            "content": data.text,
            "indexed_at": datetime.now().isoformat(),
            "_source": "api_ingest",
        }
        if data.metadata:
            doc.update(data.metadata)
        indexed, errors = store.index_documents([doc])
        return {"success": True, "indexed": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/program")
def ingest_program(data: ProgramInput):
    """Ingest program to Qdrant programs collection via OpenAI embeddings."""
    store = _require_store()
    try:
        program_dict = {
            "Program Name": data.name,
            "description": data.description,
            "Agency": data.agency,
            "Prime Contractor": ", ".join(data.primes) if data.primes else "",
            "Contract Value": data.value,
            "clearance": data.clearance,
            "technologies": ", ".join(data.technologies) if data.technologies else "",
            "indexed_at": datetime.now().isoformat(),
            "_source": "api_ingest",
        }
        indexed, errors = store.index_programs([program_dict])
        return {"success": True, "program": data.name, "indexed": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest program error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/programs/batch")
def ingest_programs_batch(programs: List[ProgramInput]):
    """Batch ingest programs to Qdrant programs collection."""
    store = _require_store()
    try:
        program_dicts = []
        for p in programs:
            program_dicts.append({
                "Program Name": p.name,
                "description": p.description,
                "Agency": p.agency,
                "Prime Contractor": ", ".join(p.primes) if p.primes else "",
                "Contract Value": p.value,
                "clearance": p.clearance,
                "technologies": ", ".join(p.technologies) if p.technologies else "",
                "indexed_at": datetime.now().isoformat(),
                "_source": "api_ingest_batch",
            })
        indexed, errors = store.index_programs(program_dicts)
        return {
            "success": True,
            "inserted": indexed,
            "updated": 0,
            "errors": errors,
            "total_submitted": len(programs),
        }
    except Exception as e:
        logger.error(f"Batch ingest programs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/company")
def ingest_company(data: CompanyInput):
    """Ingest company to Qdrant documents collection via OpenAI embeddings."""
    store = _require_store()
    try:
        doc = {
            "content": f"COMPANY: {data.name} | Type: {data.type} | Capabilities: {', '.join(data.capabilities)} | Programs: {', '.join(data.programs)}",
            "name": data.name,
            "type": data.type,
            "capabilities": ", ".join(data.capabilities),
            "programs": ", ".join(data.programs),
            "partners": ", ".join(data.partners),
            "locations": ", ".join(data.locations),
            "indexed_at": datetime.now().isoformat(),
            "_source": "api_ingest",
        }
        indexed, errors = store.index_documents([doc])
        return {"success": True, "company": data.name, "indexed": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest company error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contact")
def ingest_contact(data: ContactInput):
    """Ingest contact to Qdrant contacts collection via OpenAI embeddings."""
    store = _require_store()
    try:
        contact_dict = {
            "name": data.name,
            "company": data.company,
            "title": data.title,
            "programs": ", ".join(data.programs) if data.programs else "",
            "clearance": data.clearance,
            "indexed_at": datetime.now().isoformat(),
            "_source": "api_ingest",
        }
        indexed, errors = store.index_contacts([contact_dict])
        return {"success": True, "contact": data.name, "indexed": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest contact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contacts/batch")
def ingest_contacts_batch(contacts: List[ContactInput]):
    """Batch ingest contacts to Qdrant contacts collection."""
    store = _require_store()
    try:
        contact_dicts = []
        for c in contacts:
            contact_dicts.append({
                "name": c.name,
                "company": c.company,
                "title": c.title,
                "programs": ", ".join(c.programs) if c.programs else "",
                "clearance": c.clearance,
                "indexed_at": datetime.now().isoformat(),
                "_source": "api_ingest_batch",
            })
        indexed, errors = store.index_contacts(contact_dicts)
        return {
            "success": True,
            "inserted": indexed,
            "updated": 0,
            "errors": errors,
            "total_submitted": len(contacts),
        }
    except Exception as e:
        logger.error(f"Batch ingest contacts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs")
def ingest_jobs(jobs: List[JobInput]):
    """Ingest multiple jobs (for Data-Scraper)."""
    store = _require_store()
    try:
        job_dicts = []
        for job in jobs:
            job_dicts.append({
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "clearance": job.clearance,
                "description": job.description[:2000] if job.description else "",
                "indexed_at": datetime.now().isoformat(),
                "_source": "api_ingest",
            })
        indexed, errors = store.index_jobs(job_dicts)
        return {"success": True, "count": indexed, "errors": errors}
    except Exception as e:
        logger.error(f"Ingest jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scraper-batch")
async def ingest_scraper_batch(
    jobs_json: UploadFile = File(None, description="standardized_jobs JSON file"),
    intel_report: UploadFile = File(None, description="BD Intelligence Report .md file"),
    excel_file: UploadFile = File(None, description="BD Job Openings .xlsx file"),
):
    """Batch ingest from Data-Scraper — JSON jobs, intel reports, Excel workbooks."""
    store = _require_store()
    memory = get_memory()
    results = {"success": True, "ingested": {}}

    if jobs_json:
        try:
            content = await jobs_json.read()
            jobs = json.loads(content.decode("utf-8"))
            job_dicts = []
            for job in jobs:
                job_dicts.append({
                    "job_id": job.get("job_id", ""),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "location_normalized": job.get("location_normalized", ""),
                    "clearance": job.get("clearance_required", ""),
                    "clearance_level": job.get("clearance_level", ""),
                    "bd_priority_score": job.get("bd_priority_score", 0),
                    "bd_priority_tier": job.get("bd_priority_tier", ""),
                    "mapped_program": job.get("mapped_program", ""),
                    "program_confidence": job.get("program_confidence", 0),
                    "likely_prime": job.get("likely_prime", ""),
                    "likely_agency": job.get("likely_agency", ""),
                    "source_url": job.get("source_url", ""),
                    "date_posted": job.get("date_posted", ""),
                    "date_scraped": job.get("date_scraped", ""),
                    "description": job.get("description", "")[:2000],
                    "indexed_at": datetime.now().isoformat(),
                })
            indexed, errors = store.index_jobs(job_dicts)
            results["ingested"]["jobs"] = indexed
            if errors:
                results["ingested"]["job_errors"] = errors
            logger.info(f"Ingested {indexed} jobs from JSON")
            try:
                if memory:
                    memory.add_scrape_result("jobs", f"Batch ingested {indexed} jobs", indexed)
            except Exception as me:
                logger.warning(f"Memory logging failed: {me}")
        except Exception as e:
            results["ingested"]["jobs_error"] = str(e)
            logger.error(f"Jobs JSON error: {e}")

    if intel_report:
        try:
            content = await intel_report.read()
            report_text = content.decode("utf-8")
            indexed, errors = store.index_documents([{
                "title": intel_report.filename,
                "type": "intel_report",
                "content": report_text[:10000],
                "indexed_at": datetime.now().isoformat(),
            }])
            results["ingested"]["intel_report"] = intel_report.filename
            logger.info(f"Ingested intel report: {intel_report.filename}")
        except Exception as e:
            results["ingested"]["intel_report_error"] = str(e)
            logger.error(f"Intel report error: {e}")

    if excel_file:
        try:
            import pandas as pd
            import io

            content = await excel_file.read()
            df = pd.read_excel(io.BytesIO(content))
            summary = f"Excel workbook: {excel_file.filename}\n"
            summary += f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
            summary += f"Columns: {', '.join(df.columns.tolist())}\n"
            indexed, errors = store.index_documents([{
                "title": excel_file.filename,
                "type": "excel_workbook",
                "content": summary,
                "row_count": len(df),
                "column_count": len(df.columns),
                "indexed_at": datetime.now().isoformat(),
            }])
            results["ingested"]["excel"] = {"filename": excel_file.filename, "rows": len(df)}
            logger.info(f"Ingested Excel: {excel_file.filename} ({len(df)} rows)")
        except Exception as e:
            results["ingested"]["excel_error"] = str(e)
            logger.error(f"Excel error: {e}")

    return results


@router.post("/scraper-bulk")
async def ingest_scraper_bulk(request: Request):
    """Bulk ingest records from data-scraper via JSON body."""
    store = _require_store()
    try:
        body = await request.json()
        collection = body.get("collection")
        records = body.get("records", [])

        if not collection:
            raise HTTPException(status_code=400, detail="collection is required")
        if not records:
            raise HTTPException(status_code=400, detail="records list is empty")

        indexed, errors = store.bulk_upsert_from_scraper(
            collection=collection,
            records=records,
            source_tag=body.get("source", "data_scraper"),
        )

        return {
            "success": True,
            "collection": collection,
            "indexed": indexed,
            "errors": errors,
            "total_submitted": len(records),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scraper bulk ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
