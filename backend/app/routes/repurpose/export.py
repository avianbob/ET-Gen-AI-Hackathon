"""
Export API Routes - Export search results to PDF.

NOTE: The export_pdf endpoint is SYNCHRONOUS (not async) because:
1. Playwright's sync API cannot run inside an asyncio event loop
2. FastAPI automatically runs sync endpoints in a thread pool
3. The thread pool workers don't have an event loop, so Playwright works
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import io
import threading
import time

from app.schemas.repurpose_api import SearchResponse
from app.services.repurpose.utils.logger import get_logger
from app.services.repurpose.archive.report_archive_manager import ReportArchiveManager


class OpportunityExportRequest(BaseModel):
    """Request model for single-opportunity PDF export."""
    drug_name: str = Field(..., description="Name of the drug")
    opportunity: Dict[str, Any] = Field(..., description="Opportunity data")
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence items for this indication")
    enhanced_opportunity: Optional[Dict[str, Any]] = Field(None, description="Enhanced data (comparisons, market, science)")

logger = get_logger("api.export")
router = APIRouter()

# Singleton archive manager
archive = ReportArchiveManager()


@router.post("/export/pdf")
def export_pdf(result: SearchResponse) -> StreamingResponse:
    """
    Export search results to a formatted PDF report.

    NOTE: This is a SYNC endpoint (not async) to allow Playwright sync API
    to work. FastAPI runs this in a thread pool automatically.

    Args:
        result: Search result to export

    Returns:
        StreamingResponse with PDF file

    Raises:
        HTTPException: On PDF generation errors
    """
    start_time = time.time()
    thread_name = threading.current_thread().name

    logger.info(f"[{thread_name}] PDF export requested for: {result.drug_name}")
    logger.debug(f"[{thread_name}] Running in thread pool (no asyncio event loop)")

    try:
        # Import HTML-based PDF generator (Playwright sync API)
        logger.debug(f"[{thread_name}] Importing PDF generator...")
        from app.services.repurpose.utils.html_pdf_generator import generate_pdf_report

        # Generate PDF
        logger.info(f"[{thread_name}] Starting PDF generation...")
        pdf_buffer = generate_pdf_report(result)

        # Archive the report
        try:
            archive.archive_report(
                pdf_bytes=pdf_buffer,
                drug_name=result.drug_name,
                report_type="full_report",
                session_id=getattr(result, "session_id", None),
            )
        except Exception as archive_err:
            logger.warning(f"[{thread_name}] Failed to archive report (non-blocking): {archive_err}")

        # Create filename
        filename = f"{result.drug_name.replace(' ', '_')}_repurposing_report.pdf"

        elapsed = time.time() - start_time
        logger.info(f"[{thread_name}] PDF generated successfully: {filename} ({len(pdf_buffer):,} bytes) in {elapsed:.2f}s")

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ImportError as e:
        logger.error(f"[{thread_name}] PDF generator not available: {e}")
        raise HTTPException(
            status_code=501,
            detail="PDF export not available. Install dependencies: pip install playwright jinja2 && playwright install chromium"
        )

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[{thread_name}] PDF export failed after {elapsed:.2f}s: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")


@router.post("/export/opportunity-pdf")
def export_opportunity_pdf(request: OpportunityExportRequest) -> StreamingResponse:
    """
    Export a single opportunity to a focused mini PDF report.

    NOTE: This is a SYNC endpoint (not async) to allow Playwright sync API
    to work. FastAPI runs this in a thread pool automatically.
    """
    start_time = time.time()
    thread_name = threading.current_thread().name

    logger.info(f"[{thread_name}] Opportunity PDF export requested for: {request.drug_name}")

    try:
        from app.services.repurpose.utils.html_pdf_generator import generate_opportunity_pdf

        logger.info(f"[{thread_name}] Starting opportunity PDF generation...")
        pdf_buffer = generate_opportunity_pdf(
            request.drug_name,
            request.opportunity,
            request.evidence_items,
            request.enhanced_opportunity,
        )

        # Archive the report
        indication = request.opportunity.get('indication', 'opportunity')
        try:
            archive.archive_report(
                pdf_bytes=pdf_buffer,
                drug_name=request.drug_name,
                report_type="opportunity_report",
                indication=indication,
            )
        except Exception as archive_err:
            logger.warning(f"[{thread_name}] Failed to archive opportunity report (non-blocking): {archive_err}")

        safe_indication = indication.replace(' ', '_').replace('/', '_')[:40]
        filename = f"{request.drug_name.replace(' ', '_')}_{safe_indication}_report.pdf"

        elapsed = time.time() - start_time
        logger.info(f"[{thread_name}] Opportunity PDF generated: {filename} ({len(pdf_buffer):,} bytes) in {elapsed:.2f}s")

        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ImportError as e:
        logger.error(f"[{thread_name}] PDF generator not available: {e}")
        raise HTTPException(
            status_code=501,
            detail="PDF export not available. Install dependencies: pip install playwright jinja2 && playwright install chromium"
        )

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[{thread_name}] Opportunity PDF export failed after {elapsed:.2f}s: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Opportunity PDF export failed: {str(e)}")


class PatentExportRequest(BaseModel):
    """Request model for patent landscape PDF export."""
    drug_name: str = Field(..., description="Name of the drug")
    patent_data: Dict[str, Any] = Field(..., description="Patent landscape data from PatentAgent")


@router.post("/export/patent-pdf")
def export_patent_pdf(request: PatentExportRequest) -> StreamingResponse:
    """
    Export patent landscape to a focused mini PDF extract.

    NOTE: This is a SYNC endpoint (not async) to allow Playwright sync API to work.
    """
    start_time = time.time()
    thread_name = threading.current_thread().name

    logger.info(f"[{thread_name}] Patent PDF export requested for: {request.drug_name}")

    try:
        from app.services.repurpose.utils.html_pdf_generator import generate_patent_pdf

        pdf_buffer = generate_patent_pdf(request.drug_name, request.patent_data)

        # Archive the report
        try:
            archive.archive_report(
                pdf_bytes=pdf_buffer,
                drug_name=request.drug_name,
                report_type="patent_report",
            )
        except Exception as archive_err:
            logger.warning(f"[{thread_name}] Failed to archive patent report (non-blocking): {archive_err}")

        filename = f"{request.drug_name.replace(' ', '_')}_patent_landscape.pdf"

        elapsed = time.time() - start_time
        logger.info(f"[{thread_name}] Patent PDF generated: {filename} ({len(pdf_buffer):,} bytes) in {elapsed:.2f}s")

        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ImportError as e:
        logger.error(f"[{thread_name}] PDF generator not available: {e}")
        raise HTTPException(
            status_code=501,
            detail="PDF export not available. Install dependencies: pip install playwright jinja2 && playwright install chromium"
        )

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[{thread_name}] Patent PDF export failed after {elapsed:.2f}s: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Patent PDF export failed: {str(e)}")


@router.post("/export/excel")
def export_excel(result: SearchResponse) -> StreamingResponse:
    """
    Export search results to Excel format with multiple sheets.

    NOTE: This is a SYNC endpoint (like PDF export).
    """
    start_time = time.time()
    thread_name = threading.current_thread().name

    logger.info(f"[{thread_name}] Excel export requested for: {result.drug_name}")

    try:
        from app.services.repurpose.utils.excel_generator import generate_excel_report

        logger.info(f"[{thread_name}] Starting Excel generation...")
        excel_buffer = generate_excel_report(result)

        # Archive the report
        try:
            archive.archive_report(
                pdf_bytes=excel_buffer,
                drug_name=result.drug_name,
                report_type="excel_report",
                session_id=getattr(result, "session_id", None),
            )
        except Exception as archive_err:
            logger.warning(f"[{thread_name}] Failed to archive Excel report (non-blocking): {archive_err}")

        filename = f"{result.drug_name.replace(' ', '_')}_repurposing_report.xlsx"

        elapsed = time.time() - start_time
        logger.info(f"[{thread_name}] Excel generated: {filename} ({len(excel_buffer):,} bytes) in {elapsed:.2f}s")

        return StreamingResponse(
            io.BytesIO(excel_buffer),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ImportError as e:
        logger.error(f"[{thread_name}] Excel generator not available: {e}")
        raise HTTPException(
            status_code=501,
            detail="Excel export not available. Install dependency: pip install openpyxl"
        )

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[{thread_name}] Excel export failed after {elapsed:.2f}s: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")


@router.post("/export/json")
async def export_json(result: SearchResponse) -> Dict[str, Any]:
    """
    Export search results as JSON (for downloading).

    Args:
        result: Search result to export

    Returns:
        Dictionary with download information
    """
    try:
        logger.info(f"JSON export requested for: {result.drug_name}")

        # Convert to dict and return
        result_dict = result.model_dump()

        return {
            "status": "success",
            "filename": f"{result.drug_name.replace(' ', '_')}_repurposing_report.json",
            "data": result_dict
        }

    except Exception as e:
        logger.error(f"JSON export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
