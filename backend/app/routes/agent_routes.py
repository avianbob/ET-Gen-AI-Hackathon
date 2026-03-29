from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from app.models.agent_model import AgentRequest, AgentResponse
from app.controllers.agent_controller import process_agent_task, gemini_service
from app.agents.report_generator import ReportGeneratorAgent
from app.services.gemini_service import GeminiService
from app.services.clinical_trials_tools import AgentDecision, SearchIntent, execute_clinical_search
from app.services.export_report_pdf import build_full_report_pdf
from pydantic import BaseModel
import asyncio

router = APIRouter()
report_gen = ReportGeneratorAgent()

class GeminiTestRequest(BaseModel):
    query: str


class ClinicalTrialsTestRequest(BaseModel):
    prompt: str

@router.post("/run-agent", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    try:
        return await asyncio.wait_for(
            process_agent_task(request),
            timeout=60   # ← critical fix
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent processing timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-pdf")
async def generate_pdf(data: dict):
    """
    Receives report text and returns a PDF file.
    """
    text = data.get("text", "")
    filename = "report.pdf"
    path = report_gen.create_pdf(filename, text)
    
    return FileResponse(path, media_type='application/pdf', filename=filename)


@router.post("/export-report")
async def export_report(data: dict):
    """
    Export full report as PDF: same sequence as Dashboard UI, with all details
    (including data not shown in the UI). Send the full analysis result as JSON body.
    """
    try:
        drug = (data.get("query_context") or {}).get("drug") or "report"
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in str(drug))[:50]
        filename = f"ET_PharmAI_Full_Report_{safe_name}.pdf"
        path = build_full_report_pdf(data, filename)
        return FileResponse(path, media_type="application/pdf", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/generate-pptx")
async def generate_pptx(data: dict):
    """
    Receives report text and optional title; returns a PowerPoint file.
    """
    text = data.get("text", "")
    title = data.get("title", "Investment Memorandum")
    filename = "investment_memo.pptx"
    try:
        path = report_gen.create_pptx(filename, text, title=title)
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=filename,
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail="PPTX generation requires python-pptx. Install with: pip install python-pptx")

@router.post("/clinical-trials-test")
async def clinical_trials_test(request: ClinicalTrialsTestRequest):
    """
    Test ClinicalTrials.gov API: classify intent via Gemini (same prompts as ClinicalTrails.gov)
    then run execute_clinical_search and return decision + search_results.
    """
    user_input = request.prompt or ""
    print(f"[API /clinical-trials-test] Received prompt: {user_input[:80]}...")
    try:
        gemini_service = None
        try:
            gemini_service = GeminiService()
        except Exception as e:
            print(f"[API /clinical-trials-test] Gemini init failed: {e}")
        if not gemini_service:
            print("[API /clinical-trials-test] Using fallback: BROAD search with prompt as query.")
            decision = AgentDecision(
                drug=user_input.strip() or None,
                disease=None,
                intent=SearchIntent.BROAD,
                reasoning="Gemini unavailable; using prompt as drug query.",
            )
        else:
            decision = gemini_service.get_clinical_trial_decision(user_input)
            if decision is None:
                decision = AgentDecision(
                    drug=user_input.strip() or None,
                    disease=None,
                    intent=SearchIntent.BROAD,
                    reasoning="Gemini returned no decision; fallback BROAD.",
                )
        print(f"[API /clinical-trials-test] Decision: intent={decision.intent}, drug={decision.drug}, disease={decision.disease}")
        search_results = execute_clinical_search(decision)
        print(f"[API /clinical-trials-test] Search results keys: {list(search_results.keys())}, total_found={search_results.get('analytics', {}).get('total_found', search_results.get('error', 'N/A'))}")
        return {"decision": decision.model_dump(mode="json"), "search_results": search_results}
    except Exception as e:
        print(f"[API /clinical-trials-test] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-gemini")
async def test_gemini(request: GeminiTestRequest):
    """Test Gemini API only (no Groq fallback). Response is from Gemini when configured."""
    if not gemini_service:
        raise HTTPException(
            status_code=503,
            detail="No LLM configured. Set GEMINI_API_KEY or GROQ_API_KEY in .env (use test-groq to test Groq).",
        )
    gemini_available = (
        getattr(gemini_service, "_client", None) is not None
        or getattr(gemini_service, "_model_legacy", None) is not None
    )
    if not gemini_available:
        raise HTTPException(
            status_code=503,
            detail="Gemini is not configured. Set GEMINI_API_KEY in .env. Use /test-groq to test Groq, or run analysis (Gemini with Groq fallback).",
        )
    try:
        text = gemini_service._generate_via_gemini_only(request.query)
        return {
            "success": True,
            "message": "Gemini API is working correctly!",
            "response": (text or "").strip(),
            "provider": "gemini",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")


class TestGroqRequest(BaseModel):
    prompt: str = "Say hello in one sentence."


@router.post("/test-groq")
async def test_groq(request: TestGroqRequest):
    """Test Groq API only (fails if Groq is not configured)."""
    if not gemini_service or not getattr(gemini_service, "_groq_client", None):
        raise HTTPException(
            status_code=503,
            detail="Groq is not configured. Set GROQ_API_KEY in .env (e.g. Agentichost-main/.env)",
        )
    try:
        text = gemini_service._generate_via_groq(request.prompt)
        return {"success": True, "response": (text or "").strip(), "error": None}
    except Exception as e:
        return {"success": False, "response": None, "error": str(e)}


@router.get("/test-llm")
async def test_llm_status():
    """Return status of Gemini and Groq (no keys sent)."""
    gemini_ok = False
    groq_ok = False
    if gemini_service:
        gemini_ok = (
            getattr(gemini_service, "_client", None) is not None
            or getattr(gemini_service, "_model_legacy", None) is not None
        )
        groq_ok = getattr(gemini_service, "_groq_client", None) is not None
    return {
        "gemini_configured": gemini_ok,
        "groq_configured": groq_ok,
        "message": "Set GEMINI_API_KEY and/or GROQ_API_KEY in .env if both are false.",
    }


@router.get("/test-llm-page", response_class=HTMLResponse)
async def test_llm_page():
    """HTML page to test both Gemini and Groq APIs from the browser."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PharmAI – Test Gemini & Groq API</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1.5rem; }
    h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
    .sub { color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }
    .status-box { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
    .status { padding: 0.6rem 1rem; border-radius: 8px; font-weight: 500; }
    .ok { background: #d4edda; color: #155724; }
    .warn { background: #fff3cd; color: #856404; }
    .err { background: #f8d7da; color: #721c24; }
    label { display: block; font-weight: 500; margin-bottom: 0.25rem; }
    textarea { width: 100%; min-height: 90px; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 6px; font-size: 0.95rem; }
    .buttons { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
    button { padding: 0.5rem 1rem; cursor: pointer; border-radius: 6px; border: 1px solid #0d6efd; background: #0d6efd; color: #fff; font-size: 0.9rem; }
    button:hover { background: #0b5ed7; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    button.secondary { background: #6c757d; border-color: #6c757d; }
    button.secondary:hover { background: #5c636a; }
    .result-box { margin-top: 1rem; }
    .result-box h3 { font-size: 0.95rem; margin-bottom: 0.25rem; }
    pre { background: #f5f5f5; padding: 1rem; border-radius: 6px; overflow: auto; font-size: 0.875rem; white-space: pre-wrap; word-break: break-word; min-height: 60px; }
    .loading { color: #666; }
  </style>
</head>
<body>
  <h1>PharmAI – LLM API Test</h1>
  <p class="sub">Test your Gemini and Groq API keys. Set GEMINI_API_KEY and/or GROQ_API_KEY in <code>.env</code>.</p>
  <div id="status" class="status-box"></div>
  <label for="prompt">Prompt (used for both Gemini and Groq):</label>
  <textarea id="prompt" placeholder="e.g. What is Paracetamol used for?">Say hello in one sentence.</textarea>
  <div class="buttons">
    <button type="button" id="btnStatus">Refresh status</button>
    <button type="button" id="btnGemini">Test Gemini</button>
    <button type="button" id="btnGroq">Test Groq</button>
  </div>
  <div class="result-box">
    <h3>Result</h3>
    <pre id="result">Click a button above to test.</pre>
  </div>
  <script>
    function apiBase() {
      return window.location.origin + '/api';
    }
    async function loadStatus() {
      var el = document.getElementById('status');
      el.innerHTML = '<span class="status loading">Loading…</span>';
      try {
        var r = await fetch(apiBase() + '/test-llm');
        var d = await r.json();
        el.innerHTML =
          '<span class="status ' + (d.gemini_configured ? 'ok' : 'warn') + '">Gemini: ' + (d.gemini_configured ? 'Configured' : 'Not configured') + '</span>' +
          '<span class="status ' + (d.groq_configured ? 'ok' : 'err') + '">Groq: ' + (d.groq_configured ? 'Configured' : 'Not configured') + '</span>';
      } catch (e) {
        el.innerHTML = '<span class="status err">Failed to load status: ' + e.message + '</span>';
      }
    }
    function setResult(text, isError) {
      var pre = document.getElementById('result');
      pre.textContent = text;
      pre.style.color = isError ? '#721c24' : '';
    }
    async function testGemini() {
      var prompt = document.getElementById('prompt').value || 'Hello';
      setResult('Calling Gemini…', false);
      try {
        var r = await fetch(apiBase() + '/test-gemini', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: prompt })
        });
        var d = await r.json();
        if (r.ok) {
          var resp = d.response || d.message || 'OK';
          setResult((d.provider === 'gemini' ? '[Gemini] ' : '') + resp, false);
        } else {
          setResult('Error: ' + (d.detail || d.message || r.status), true);
        }
      } catch (e) {
        setResult('Request failed: ' + e.message, true);
      }
    }
    async function testGroq() {
      var prompt = document.getElementById('prompt').value || 'Hello';
      setResult('Calling Groq…', false);
      try {
        var r = await fetch(apiBase() + '/test-groq', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: prompt })
        });
        var d = await r.json();
        if (r.ok && d.success) setResult('[Groq] ' + (d.response || 'OK'), false);
        else setResult('Error: ' + (d.error || d.detail || r.status), true);
      } catch (e) {
        setResult('Request failed: ' + e.message, true);
      }
    }
    document.getElementById('btnStatus').onclick = loadStatus;
    document.getElementById('btnGemini').onclick = testGemini;
    document.getElementById('btnGroq').onclick = testGroq;
    loadStatus();
  </script>
</body>
</html>"""