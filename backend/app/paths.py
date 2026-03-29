"""Repository root paths for repurposing services (templates, data/, cwd for subprocesses)."""

from pathlib import Path

# Agentichost-main/ (parent of app/)
BACKEND_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_PDF_DIR = BACKEND_ROOT / "templates" / "pdf"
