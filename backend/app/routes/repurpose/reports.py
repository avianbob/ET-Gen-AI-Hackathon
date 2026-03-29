"""
Reports API Routes - Manage archived reports (list, download, delete).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any

from app.services.repurpose.archive.report_archive_manager import ReportArchiveManager
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("api.reports")
router = APIRouter()

# Singleton archive manager
archive = ReportArchiveManager()


@router.get("/reports")
async def list_reports(limit: int = 50) -> Dict[str, Any]:
    """Get list of all archived reports (most recent first)."""
    try:
        reports = archive.get_all_reports(limit=limit)
        return {"total": len(reports), "reports": reports}
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/drug/{drug_name}")
async def list_reports_for_drug(drug_name: str) -> Dict[str, Any]:
    """Get all reports for a specific drug."""
    try:
        reports = archive.get_reports_for_drug(drug_name)
        return {"drug_name": drug_name, "total": len(reports), "reports": reports}
    except Exception as e:
        logger.error(f"Failed to list reports for {drug_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}")
async def get_report_metadata(report_id: str) -> Dict[str, Any]:
    """Get metadata for a specific report."""
    report = archive.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/reports/{report_id}/download")
def download_report(report_id: str) -> FileResponse:
    """Download an archived report file."""
    report = archive.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = archive.get_report_file_path(report_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    drug_name = report.get("drug_name", "report").replace(" ", "_")
    report_type = report.get("report_type", "full_report")

    if report_type == "excel_report":
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{drug_name}_report.xlsx"
    else:
        media_type = "application/pdf"
        indication = report.get("indication")
        if indication:
            safe_ind = indication.replace(" ", "_").replace("/", "_")[:40]
            filename = f"{drug_name}_{safe_ind}_report.pdf"
        else:
            filename = f"{drug_name}_report.pdf"

    return FileResponse(path=str(file_path), media_type=media_type, filename=filename)


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str) -> Dict[str, Any]:
    """Delete a report from the archive."""
    success = archive.delete_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found or deletion failed")
    return {"status": "success", "message": f"Report {report_id} deleted"}
