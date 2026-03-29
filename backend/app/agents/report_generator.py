import os
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from fpdf import FPDF
from ..schemas.analysis import AnalysisRequest, AgentResult, GradingBreakdown

if TYPE_CHECKING:
    from ..services.gemini_service import GeminiService


class ReportGeneratorAgent:
    """
    Synthesizes the final report using the shared LLM (Gemini with Groq fallback).
    Uses real API only; no dummy output.
    """

    def __init__(self, llm_service: Optional["GeminiService"] = None):
        self.llm_service = llm_service

    def generate_report(
        self,
        request: AnalysisRequest,
        grading: GradingBreakdown,
        results: List[AgentResult],
        fallback_used_list: Optional[List[str]] = None,
    ) -> str:
        molecule = (request.molecule_name or "").strip()
        indication = (getattr(request, "target_indication", None) or "N/A").strip()
        # Use molecule as asset name; if molecule looks like "treatment for X", use X as molecule for clarity
        if molecule.lower().startswith("treatment for "):
            display_molecule = molecule[14:].strip() or molecule
        else:
            display_molecule = molecule or "Pharmaceutical Asset"

        context = f"Molecule (asset name): {display_molecule}\n"
        context += f"Indication (therapeutic use): {indication}\n"
        context += f"Projected Feasibility Score: {grading.overall_score:.2f}/1.0\n\n"
        context += "--- RAW AGENT INTELLIGENCE ---\n"
        for r in results:
            context += f"[{r.agent_name.upper()}]: {r.summary}\n"

        key_regions = []
        if getattr(request, "parsed_intelligence", None) and isinstance(request.parsed_intelligence, dict):
            key_regions = request.parsed_intelligence.get("key_regions") or []
        if getattr(request, "regions", None) and request.regions:
            key_regions = list(dict.fromkeys(list(key_regions) + list(request.regions)))
        if key_regions:
            context += f"\nKey regions (use exactly these in the memo): {', '.join(key_regions)}\n"
        if getattr(request, "symptoms", None) and request.symptoms:
            context += f"Symptoms: {', '.join(request.symptoms)}\n"
        if getattr(request, "phase", None):
            context += f"Development phase: {request.phase}\n"

        report_date = datetime.now().strftime("%B %d, %Y")

        prompt = (
            f"Role: Managing Director of Pharmaceutical Investment Banking.\n"
            f"Task: Write a definitive Investment Committee Memorandum.\n\n"
            f"CRITICAL FORMATTING RULES:\n"
            f"- Use the Molecule as the asset name (e.g. '{display_molecule}'). Use the Indication only for therapeutic context (e.g. '{indication}'). Do NOT repeat the molecule name after the indication (wrong: 'Treatment for Paracetamol overdose, Paracetamol'; right: 'Paracetamol — Treatment for Paracetamol Overdose' or 'Subject: Paracetamol (Indication: Paracetamol Overdose)').\n"
            f"- Write all monetary and numeric values on a single line (e.g. '$0.3B', '3.0%', '5.0 bar'). Do NOT insert line breaks inside numbers or between $ and the amount.\n"
            f"- Use today's date for the recommendation date: {report_date}.\n"
            f"- Use section headers in the format: **SECTION NAME:** (e.g. **EXECUTIVE THESIS:**, **MARKET DEMAND:**).\n\n"
            f"INPUT DATA:\n{context}\n\n"
            f"MANDATORY SECTIONS (use **SECTION NAME:** format):\n"
            f"**SUBJECT:** One line: [Molecule] — [Brief indication].\n"
            f"**EXECUTIVE THESIS:** The 'Why Now' — synthesize market demand and strategic fit.\n"
            f"**MARKET DEMAND:** Estimated global market size (single line, e.g. $X.XB), CAGR, key regions from the data, target molecule, indication, projected feasibility score.\n"
            f"**TECHNICAL & OPERATIONAL RISKS:** Process complexity, scalability, operating conditions (temperature, pressure).\n"
            f"**FINANCIAL OUTLOOK:** CAPEX, annual OPEX, payback period, IRR. Keep numbers on one line each.\n"
            f"**STRATEGIC RECOMMENDATION:** Buy, Build, or Partner with one short paragraph.\n"
            f"**RECOMMENDATIONS:** Must be on its own line as a section header (same format as **SUBJECT:**). Then a numbered list (1. 2. 3.) on the following lines. End with: Recommendation date: {report_date}. Do not add any signing-off line or placeholder name.\n\n"
            f"Output only the memorandum text. No meta-commentary. No extra line breaks inside dollar or percentage values."
        )

        if self.llm_service:
            try:
                response = self.llm_service._generate_content_with_retry(
                    prompt,
                    operation_name="report_generation",
                    fallback_used_list=fallback_used_list,
                )
                return (response.text or "").strip() or context
            except Exception as e:
                return f"Report generation failed. Please consult raw agent logs. Error: {e}"
        return "LLM Service Unavailable for Report Generation."

    def create_pdf(self, filename: str, content: str) -> str:
        """
        Create a PDF file and return the absolute path.
        
        Args:
            filename: Name of the PDF file
            content: Text content to include in the PDF
            
        Returns:
            Absolute path to the created PDF file
        """
        # Create a temp directory if it doesn't exist, or use current directory
        import tempfile
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="PharmaAI Strategic Report", ln=1, align='C')
        pdf.ln(10)
        
        # Content
        pdf.set_font("Arial", size=11)
        # simplistic wrapping
        pdf.multi_cell(0, 10, content.encode('latin-1', 'replace').decode('latin-1'))
        
        # Save
        pdf.output(filepath)
        return filepath

    def create_pptx(self, filename: str, content: str, title: str = "Investment Memorandum") -> str:
        """
        Create a PowerPoint file from report content and return the absolute path.
        """
        import tempfile
        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt
            from pptx.dml.color import RgbColor
        except ImportError:
            raise ImportError("python-pptx is required. Install with: pip install python-pptx")

        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)

        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        # Title slide
        slide_layout = prs.slide_layouts[6]  # Blank
        slide = prs.slides.add_slide(slide_layout)
        left = Inches(0.5)
        top = Inches(2)
        width = Inches(9)
        height = Inches(1.2)
        tx = slide.shapes.add_textbox(left, top, width, height)
        tf = tx.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(32)
        p.font.bold = True
        p2 = tf.add_paragraph()
        import datetime
        p2.text = f"ET PharmAI • {datetime.datetime.now().strftime('%B %d, %Y')}"
        p2.font.size = Pt(14)
        p2.space_before = Pt(12)

        # Content slides: split by double newline or section headers
        chunks = []
        current = []
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                if current:
                    chunks.append("\n".join(current))
                    current = []
            elif stripped.startswith(("1.", "2.", "3.", "4.", "###", "SECTION:")):
                if current:
                    chunks.append("\n".join(current))
                current = [stripped]
            else:
                current.append(line)
        if current:
            chunks.append("\n".join(current))

        for chunk in chunks[:12]:  # Limit slides
            slide = prs.slides.add_slide(slide_layout)
            left, top, width, height = Inches(0.5), Inches(0.5), Inches(9), Inches(6.5)
            tx = slide.shapes.add_textbox(left, top, width, height)
            tf = tx.text_frame
            tf.word_wrap = True
            for i, line in enumerate(chunk.split("\n")):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.text = line[:200] + ("..." if len(line) > 200 else "")
                p.font.size = Pt(14)
                p.space_after = Pt(6)

        prs.save(filepath)
        return filepath