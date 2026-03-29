"""
Report Archive Manager - Manages report archival using JSON metadata + filesystem storage.
Pattern: Similar to CacheManager for consistency with USE_MONGODB=false default.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from app.services.repurpose.utils.logger import get_logger

logger = get_logger("archive")


class ReportArchiveManager:
    """Manages archival of PDF/Excel reports using filesystem storage."""

    def __init__(self, archive_dir: Optional[str] = None):
        self.archive_dir = Path(archive_dir or "data/reports")
        self.metadata_file = self.archive_dir / "reports_metadata.json"

        self.archive_dir.mkdir(parents=True, exist_ok=True)

        if not self.metadata_file.exists():
            self._save_metadata([])

        logger.info(f"Report archive initialized: {self.archive_dir}")

    def _load_metadata(self) -> List[Dict[str, Any]]:
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return []

    def _save_metadata(self, metadata: List[Dict[str, Any]]):
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def archive_report(
        self,
        pdf_bytes: bytes,
        drug_name: str,
        report_type: str = "full_report",
        indication: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save a report to archive.

        Returns:
            Report metadata dict with report_id, file_path, etc.
        """
        report_id = str(uuid.uuid4())

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_drug = drug_name.replace(" ", "_").replace("/", "_")[:50]
        if report_type == "opportunity_report" and indication:
            safe_ind = indication.replace(" ", "_").replace("/", "_")[:40]
            filename = f"{report_id}_{safe_drug}_{safe_ind}_{timestamp}.pdf"
        elif report_type == "excel_report":
            filename = f"{report_id}_{safe_drug}_{timestamp}.xlsx"
        else:
            filename = f"{report_id}_{safe_drug}_{timestamp}.pdf"

        file_path = self.archive_dir / filename

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        logger.info(f"Archived report: {filename} ({len(pdf_bytes):,} bytes)")

        report_metadata = {
            "report_id": report_id,
            "drug_name": drug_name,
            "report_type": report_type,
            "indication": indication,
            "file_path": filename,
            "file_size": len(pdf_bytes),
            "created_at": datetime.now().isoformat(),
            "session_id": session_id,
        }

        all_metadata = self._load_metadata()
        all_metadata.insert(0, report_metadata)
        self._save_metadata(all_metadata)

        return report_metadata

    def get_all_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        metadata = self._load_metadata()
        return metadata[:limit]

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        for report in self._load_metadata():
            if report.get("report_id") == report_id:
                return report
        return None

    def get_report_file_path(self, report_id: str) -> Optional[Path]:
        report = self.get_report_by_id(report_id)
        if report:
            return self.archive_dir / report["file_path"]
        return None

    def delete_report(self, report_id: str) -> bool:
        report = self.get_report_by_id(report_id)
        if not report:
            return False

        file_path = self.archive_dir / report["file_path"]
        try:
            if file_path.exists():
                file_path.unlink()

            all_metadata = self._load_metadata()
            all_metadata = [r for r in all_metadata if r.get("report_id") != report_id]
            self._save_metadata(all_metadata)

            logger.info(f"Deleted report: {report_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {e}")
            return False

    def get_reports_for_drug(self, drug_name: str) -> List[Dict[str, Any]]:
        return [
            r
            for r in self._load_metadata()
            if r.get("drug_name", "").lower() == drug_name.lower()
        ]
