"""
HTML-to-PDF Generator using Playwright via Subprocess.

On Windows, Playwright requires running on the main thread for subprocess creation.
FastAPI's worker threads cannot satisfy this requirement. The solution is to spawn
a separate Python process that runs Playwright on its own main thread.

This module handles:
1. Data transformation (SearchResponse → template data)
2. HTML rendering (Jinja2 template)
3. PDF generation (via subprocess calling pdf_subprocess.py)
"""

import base64
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Union, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.paths import BACKEND_ROOT, TEMPLATES_PDF_DIR
from app.schemas.repurpose_api import SearchResponse
from .logger import get_logger
from .pdf_template_data import prepare_template_data, prepare_opportunity_template_data

logger = get_logger("pdf_generator")

TEMPLATE_DIR = TEMPLATES_PDF_DIR

# Path to the subprocess worker script
SUBPROCESS_SCRIPT = Path(__file__).parent / "pdf_subprocess.py"


def _create_jinja_env() -> Environment:
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(['html', 'xml'])
    )

    def truncate_filter(s: str, length: int = 30) -> str:
        """Truncate string with ellipsis."""
        if s is None:
            return ''
        s = str(s)
        return (s[:length - 3] + '...') if len(s) > length else s

    def round_filter(value, precision: int = 0):
        """Round a number to specified precision."""
        if value is None:
            return 0
        try:
            if precision == 0:
                return int(round(float(value)))
            return round(float(value), precision)
        except (ValueError, TypeError):
            return 0

    env.filters['truncate'] = truncate_filter
    env.filters['round'] = round_filter

    return env


def _generate_pdf_via_subprocess(html_content: str) -> bytes:
    """
    Generate PDF by spawning a subprocess.

    This bypasses the Windows limitation where asyncio.create_subprocess_exec()
    only works from the main thread. The subprocess has its own main thread.

    Args:
        html_content: Rendered HTML string

    Returns:
        PDF as bytes

    Raises:
        RuntimeError: If subprocess fails
    """
    thread_name = threading.current_thread().name
    logger.info(f"[{thread_name}] Spawning PDF subprocess...")

    # Encode HTML to base64 for safe transfer via stdin
    html_b64 = base64.b64encode(html_content.encode('utf-8')).decode('ascii')
    input_data = json.dumps({'html': html_b64})

    start_time = time.time()

    try:
        # Spawn subprocess to run Playwright
        # Using sys.executable ensures we use the same Python interpreter
        result = subprocess.run(
            [sys.executable, str(SUBPROCESS_SCRIPT)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=str(BACKEND_ROOT)
        )

        elapsed = time.time() - start_time
        logger.debug(f"[{thread_name}] Subprocess completed in {elapsed:.2f}s (exit code: {result.returncode})")

        if result.returncode != 0:
            logger.error(f"[{thread_name}] Subprocess stderr: {result.stderr}")
            # Try to parse error from stdout (our protocol sends JSON even on error)
            try:
                response = json.loads(result.stdout)
                error_msg = response.get('error', 'Unknown error')
                logger.error(f"[{thread_name}] Subprocess error: {error_msg}")
                if 'traceback' in response:
                    logger.error(f"[{thread_name}] Subprocess traceback:\n{response['traceback']}")
                raise RuntimeError(f"PDF subprocess failed: {error_msg}")
            except json.JSONDecodeError:
                raise RuntimeError(f"PDF subprocess failed with exit code {result.returncode}: {result.stderr}")

        # Parse response
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"[{thread_name}] Failed to parse subprocess output: {e}")
            logger.error(f"[{thread_name}] Stdout: {result.stdout[:500]}...")
            raise RuntimeError(f"Failed to parse PDF subprocess output: {e}")

        if not response.get('success'):
            error_msg = response.get('error', 'Unknown error')
            logger.error(f"[{thread_name}] Subprocess reported failure: {error_msg}")
            raise RuntimeError(f"PDF generation failed: {error_msg}")

        # Decode PDF from base64
        pdf_bytes = base64.b64decode(response['pdf'])
        pdf_size = response.get('size', len(pdf_bytes))

        logger.info(f"[{thread_name}] PDF subprocess successful: {pdf_size:,} bytes in {elapsed:.2f}s")
        return pdf_bytes

    except subprocess.TimeoutExpired:
        logger.error(f"[{thread_name}] PDF subprocess timed out after 120s")
        raise RuntimeError("PDF generation timed out")

    except FileNotFoundError as e:
        logger.error(f"[{thread_name}] Subprocess script not found: {SUBPROCESS_SCRIPT}")
        raise RuntimeError(f"PDF subprocess script not found: {e}")

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[{thread_name}] PDF subprocess failed after {elapsed:.2f}s: {type(e).__name__}: {e}")
        raise


def generate_pdf(
    result: Union[dict, SearchResponse],
    output_path: Optional[str] = None
) -> bytes:
    """
    Generate PDF report from search results.

    Args:
        result: SearchResponse dict or Pydantic model containing analysis results
        output_path: Optional path to save PDF file

    Returns:
        PDF as bytes
    """
    thread_name = threading.current_thread().name
    start_time = time.time()

    logger.info(f"[{thread_name}] Starting HTML-based PDF generation")
    logger.debug(f"[{thread_name}] Template directory: {TEMPLATE_DIR}")
    logger.debug(f"[{thread_name}] Subprocess script: {SUBPROCESS_SCRIPT}")

    # 1. Transform data for template
    logger.debug(f"[{thread_name}] Step 1: Transforming data...")
    template_data = prepare_template_data(result)
    drug_name = template_data.get('drug_name', 'Unknown')
    logger.debug(f"[{thread_name}] Template data prepared for drug: {drug_name}")
    logger.debug(f"[{thread_name}]   - Opportunities: {template_data.get('opportunity_count', 0)}")
    logger.debug(f"[{thread_name}]   - Evidence count: {template_data.get('evidence_count', 0)}")

    # 2. Load and render Jinja2 template
    logger.debug(f"[{thread_name}] Step 2: Rendering HTML template...")
    env = _create_jinja_env()

    try:
        template = env.get_template("report.html")
        logger.debug(f"[{thread_name}] Template loaded: report.html")
    except Exception as e:
        logger.error(f"[{thread_name}] Failed to load template: {e}")
        raise FileNotFoundError(
            f"PDF template not found at {TEMPLATE_DIR / 'report.html'}. "
            "Ensure the template file exists."
        )

    html_content = template.render(**template_data)
    logger.debug(f"[{thread_name}] HTML rendered: {len(html_content):,} characters")

    # 3. Convert to PDF via subprocess
    logger.debug(f"[{thread_name}] Step 3: Converting HTML to PDF via subprocess...")
    pdf_bytes = _generate_pdf_via_subprocess(html_content)

    elapsed = time.time() - start_time
    logger.info(f"[{thread_name}] PDF generated successfully: {len(pdf_bytes):,} bytes in {elapsed:.2f}s")

    # 4. Optionally save to file
    if output_path:
        Path(output_path).write_bytes(pdf_bytes)
        logger.info(f"[{thread_name}] PDF saved to: {output_path}")

    return pdf_bytes


def generate_opportunity_pdf(
    drug_name: str,
    opportunity: dict,
    evidence_items: list,
    enhanced_opportunity: dict = None,
) -> bytes:
    """
    Generate a mini PDF report for a single opportunity.

    Args:
        drug_name: Name of the drug
        opportunity: Single opportunity dict
        evidence_items: Evidence items for this indication
        enhanced_opportunity: Enhanced data (comparisons, market, science)

    Returns:
        PDF as bytes
    """
    thread_name = threading.current_thread().name
    start_time = time.time()

    logger.info(f"[{thread_name}] Starting opportunity PDF generation for: {drug_name}")

    # 1. Transform data for template
    template_data = prepare_opportunity_template_data(
        drug_name, opportunity, evidence_items, enhanced_opportunity
    )
    indication = template_data.get('indication', 'Unknown')
    logger.debug(f"[{thread_name}] Template data prepared for: {drug_name} - {indication}")

    # 2. Load and render Jinja2 template
    env = _create_jinja_env()

    try:
        template = env.get_template("opportunity_report.html")
    except Exception as e:
        logger.error(f"[{thread_name}] Failed to load opportunity template: {e}")
        raise FileNotFoundError(
            f"Opportunity report template not found at {TEMPLATE_DIR / 'opportunity_report.html'}."
        )

    html_content = template.render(**template_data)
    logger.debug(f"[{thread_name}] HTML rendered: {len(html_content):,} characters")

    # 3. Convert to PDF via subprocess
    pdf_bytes = _generate_pdf_via_subprocess(html_content)

    elapsed = time.time() - start_time
    logger.info(f"[{thread_name}] Opportunity PDF generated: {len(pdf_bytes):,} bytes in {elapsed:.2f}s")

    return pdf_bytes


def generate_patent_pdf(drug_name: str, patent_data: dict) -> bytes:
    """
    Generate a mini PDF extract of the patent landscape for a drug.

    Args:
        drug_name: Name of the drug
        patent_data: Patent landscape dict from PatentAgent.get_patent_landscape()

    Returns:
        PDF as bytes
    """
    thread_name = threading.current_thread().name
    start_time = time.time()

    logger.info(f"[{thread_name}] Starting patent PDF generation for: {drug_name}")

    template_data = {
        "drug_name": drug_name,
        "summary": patent_data.get("summary", ""),
        "patents": patent_data.get("tables", [{}])[0].get("rows", []) if patent_data.get("tables") else [],
        "fto_summary": patent_data.get("fto_summary", {}),
        "expiring_soon": patent_data.get("expiring_soon", []),
        "top_filers": patent_data.get("top_filers", {}),
        "total_patents": len(patent_data.get("evidence", [])),
        "generated_at": time.strftime("%Y-%m-%d %H:%M UTC"),
    }

    env = _create_jinja_env()

    try:
        template = env.get_template("patent_report.html")
    except Exception as e:
        logger.error(f"[{thread_name}] Failed to load patent template: {e}")
        raise FileNotFoundError(
            f"Patent report template not found at {TEMPLATE_DIR / 'patent_report.html'}."
        )

    html_content = template.render(**template_data)
    pdf_bytes = _generate_pdf_via_subprocess(html_content)

    elapsed = time.time() - start_time
    logger.info(f"[{thread_name}] Patent PDF generated: {len(pdf_bytes):,} bytes in {elapsed:.2f}s")

    return pdf_bytes


def generate_pdf_report(result: Union[dict, SearchResponse]) -> bytes:
    """
    Generate PDF report - main entry point for backward compatibility.

    Args:
        result: SearchResponse dict or Pydantic model containing analysis results

    Returns:
        PDF as bytes
    """
    return generate_pdf(result)


class PDFGenerator:
    """
    Class-based interface for PDF generation.

    Usage:
        generator = PDFGenerator()

        # Debug: render HTML without PDF conversion
        html = generator.render_html(search_response)

        # Generate PDF
        pdf_bytes = generator.generate(search_response)
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize PDF generator.

        Args:
            template_dir: Optional custom template directory
        """
        self.template_dir = template_dir or TEMPLATE_DIR
        self._env = None

    @property
    def env(self) -> Environment:
        """Get or create Jinja2 environment."""
        if self._env is None:
            self._env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(['html', 'xml'])
            )

            self._env.filters['truncate'] = lambda s, length=30: (
                (str(s)[:length - 3] + '...') if s and len(str(s)) > length else (s or '')
            )

            def safe_round(value, precision=0):
                if value is None:
                    return 0
                try:
                    if precision == 0:
                        return int(round(float(value)))
                    return round(float(value), precision)
                except (ValueError, TypeError):
                    return 0

            self._env.filters['round'] = safe_round

        return self._env

    def render_html(self, result: Union[dict, SearchResponse]) -> str:
        """
        Render HTML without converting to PDF.

        Useful for debugging template issues.

        Args:
            result: SearchResponse dict or Pydantic model

        Returns:
            Rendered HTML string
        """
        template_data = prepare_template_data(result)
        template = self.env.get_template("report.html")
        return template.render(**template_data)

    def generate(
        self,
        result: Union[dict, SearchResponse],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF from search results.

        Args:
            result: SearchResponse dict or Pydantic model
            output_path: Optional path to save PDF

        Returns:
            PDF as bytes
        """
        return generate_pdf(result, output_path)
