"""
Unified LLM service: Google Gemini (google.genai SDK) with Groq fallback.
Supports Groq as fallback when Gemini fails (429, network, etc.).
"""
import json
import os
import re
import time
from typing import Optional, Dict, Any, List
from urllib.parse import quote

from dotenv import load_dotenv

# Load .env before reading any env vars (use project root if possible)
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(_env_path)
load_dotenv()

from ..schemas.analysis import PharmaQueryContext

# Prefer new google.genai SDK; only load deprecated google.generativeai if new is unavailable.
_google_genai_new = None
_google_genai_legacy = None
try:
    from google import genai as _google_genai_new
except ImportError:
    pass
if _google_genai_new is None:
    try:
        import warnings
        with warnings.catch_warnings(action="ignore", category=FutureWarning):
            import google.generativeai as _google_genai_legacy
    except ImportError:
        pass

try:
    from groq import Groq
except ImportError:
    Groq = None

# Max wait (seconds) when API says "retry in Xs" (used only if Groq unavailable)
GEMINI_RETRY_DELAY_CAP = 60
# No Gemini retries on 429: fall back to Groq after first 429
GEMINI_RETRY_ATTEMPTS = 0


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in str(exc) or "quota" in msg or "exceeded" in msg or "rate" in msg


def _parse_retry_delay_seconds(exc: Exception) -> float:
    """Parse 'Please retry in 27.065182495s' from error message. Return capped delay in seconds."""
    msg = str(exc)
    match = re.search(r"retry in ([\d.]+)\s*s", msg, re.IGNORECASE)
    if match:
        try:
            delay = float(match.group(1))
            return min(max(delay, 1), GEMINI_RETRY_DELAY_CAP)
        except (ValueError, TypeError):
            pass
    return min(30, GEMINI_RETRY_DELAY_CAP)


def _extract_first_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract the first complete JSON object from LLM output. Handles markdown, extra text,
    and 'Extra data' errors when the model returns explanation + JSON or multiple objects.
    """
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    # Strip markdown code block
    if "```" in text:
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```.*$", "", text, flags=re.DOTALL)
    text = text.strip()
    # Find first { and then matching } by brace count
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    try:
        return json.loads(text[start:])
    except json.JSONDecodeError:
        return None


class GeminiService:
    """
    Unified LLM service: Google Gemini with Groq fallback.
    - Prefer Gemini when GEMINI_API_KEY is set and init succeeds; on API errors (429, network, etc.)
      fall back to Groq when GROQ_API_KEY is set.
    - When Gemini is not available (no key or init failed), use Groq only if GROQ_API_KEY is set.
    - At least one of GEMINI_API_KEY or GROQ_API_KEY must be set; otherwise raises ValueError.
    - Use _generate_via_gemini_only() for tests that must hit Gemini (no Groq fallback).
    """

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.api_key = (api_key.strip() if isinstance(api_key, str) else None) or None
        groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
        self._groq_client = None
        if Groq and groq_key:
            try:
                self._groq_client = Groq(api_key=groq_key)
                print("Groq client initialized.")
            except Exception as e:
                print(f"Groq client not initialized: {e}")

        self._client = None  # new SDK: google.genai Client
        self._model_legacy = None  # legacy: google.generativeai GenerativeModel
        self.current_model_name = None
        self.available_models = []

        if not self.api_key and not self._groq_client:
            raise ValueError(
                "No LLM API key found. Set GEMINI_API_KEY and/or GROQ_API_KEY in .env (at least one required). "
                "Example: GROQ_API_KEY=gsk_... in Agentichost-main/.env"
            )

        def _is_404(exc: Exception) -> bool:
            msg = str(exc).lower()
            return "404" in msg or "not found" in msg

        if self.api_key and (_google_genai_new is not None or _google_genai_legacy is not None):
            use_legacy_first = os.getenv("GEMINI_USE_LEGACY", "").strip().lower() in ("1", "true", "yes")
            new_sdk_404 = False  # set if new SDK fails all models with 404 (then we try legacy)

            if _google_genai_new is not None and not use_legacy_first:
                print("Initializing Gemini (google.genai)...")
                # Prefer models that work with Gemini API (ai.google.dev); 2.0-flash can 404 on some endpoints
                preferred_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
                try:
                    self._client = _google_genai_new.Client(api_key=self.api_key)
                    self.available_models = preferred_models
                    for model_name in preferred_models:
                        try:
                            r = self._client.models.generate_content(model=model_name, contents="Hi")
                            if getattr(r, "text", None) or (hasattr(r, "candidates") and r.candidates):
                                self.current_model_name = model_name
                                print(f"[Gemini] Initialized successfully: {model_name}")
                                break
                        except Exception as e:
                            if _is_404(e):
                                new_sdk_404 = True
                            print(f"[Gemini] Model {model_name} failed: {type(e).__name__}: {e}")
                            continue
                    if self.current_model_name is None and new_sdk_404:
                        print("[Gemini] New SDK returned 404 for all models (common with AI Studio keys). Trying legacy SDK...")
                        self._client = None  # clear so legacy can be tried below
                    elif self.current_model_name is None:
                        print("[Gemini] All models failed during init; Gemini will not be used (Groq fallback only). Check GEMINI_API_KEY at https://aistudio.google.com/apikey and that your key has access to Gemini models.")
                except Exception as e:
                    print(f"Warning: Gemini client init failed: {e}")
            else:
                # Legacy google.generativeai (e.g. when google-genai pip install timed out)
                print("Initializing Gemini (google.generativeai legacy)...")
                preferred_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
                try:
                    _google_genai_legacy.configure(api_key=self.api_key)
                    for model_name in preferred_models:
                        try:
                            self._model_legacy = _google_genai_legacy.GenerativeModel(model_name)
                            self._model_legacy.generate_content("Hi")
                            self.current_model_name = model_name
                            self.available_models = preferred_models
                            print(f"[Gemini] Initialized (legacy): {model_name}")
                            break
                        except Exception as e:
                            print(f"[Gemini] Legacy model {model_name} failed: {type(e).__name__}: {e}")
                            continue
                    if self.current_model_name is None:
                        print("[Gemini] All legacy models failed; Gemini will not be used (Groq fallback only).")
                except Exception as e:
                    print(f"[Gemini] Legacy client init failed: {type(e).__name__}: {e}")

        if self._client is None and self._model_legacy is None and self._groq_client:
            print("Using Groq only (no Gemini). Set GEMINI_API_KEY for Gemini primary.")
        elif self._client is None and self._model_legacy is None:
            raise ValueError(
                "Gemini could not be initialized and Groq is not configured. "
                "Set GEMINI_API_KEY and/or GROQ_API_KEY in .env (e.g. in Agentichost-main/.env)."
            )

    def _generate_via_groq(self, prompt: str) -> str:
        """Call Groq chat completions; return response text. Raises on error."""
        if not self._groq_client:
            raise RuntimeError("Groq client not available")
        response = self._groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content if response.choices else None
        if content is None:
            raise ValueError("Groq returned empty content")
        return content

    def _generate_via_gemini_only(self, prompt: str) -> str:
        """
        Call Gemini only (no Groq fallback). Use for tests or when response must be from Gemini.
        Raises if Gemini is not configured or if the API call fails.
        """
        if self._client is None and self._model_legacy is None:
            raise RuntimeError(
                "Gemini is not configured. Set GEMINI_API_KEY in .env. Use the main pipeline for Groq fallback."
            )
        if self._client is not None:
            response = self._client.models.generate_content(
                model=self.current_model_name,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if text is None and getattr(response, "candidates", None) and response.candidates:
                c = response.candidates[0]
                if getattr(c, "content", None) and getattr(c.content, "parts", None) and c.content.parts:
                    text = getattr(c.content.parts[0], "text", None)
            return text or ""
        if self._model_legacy is not None:
            response = self._model_legacy.generate_content(prompt)
            return getattr(response, "text", None) or ""
        raise RuntimeError("Gemini client not available")

    def _generate_content_with_retry(
        self,
        prompt: str,
        max_retries: int = GEMINI_RETRY_ATTEMPTS,
        operation_name: Optional[str] = None,
        fallback_used_list: Optional[List[str]] = None,
    ):
        """
        Generate text: prefer Gemini; fall back to Groq only when Gemini is unavailable or fails.
        - Gemini not configured (no client): use Groq if available.
        - Gemini configured: try Gemini first; on error (429, network, etc.) try Groq if available.
        Returns an object with .text. When Groq is used, appends operation_name to fallback_used_list.
        """
        def _make_text_response(text: str):
            class _TextResponse:
                pass
            r = _TextResponse()
            r.text = text
            return r

        # No Gemini: use Groq only
        if self._client is None and self._model_legacy is None and self._groq_client:
            try:
                text = self._generate_via_groq(prompt)
                if fallback_used_list is not None and operation_name:
                    fallback_used_list.append(operation_name)
                return _make_text_response(text)
            except Exception as e:
                print(f"[LLM] Groq failed ({operation_name or 'unknown'}): {e}")
                raise

        # Try Gemini (new SDK or legacy)
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                if self._client is not None:
                    response = self._client.models.generate_content(
                        model=self.current_model_name,
                        contents=prompt,
                    )
                    text = getattr(response, "text", None)
                    if text is None and getattr(response, "candidates", None):
                        c = response.candidates[0]
                        if getattr(c, "content", None) and getattr(c.content, "parts", None) and c.content.parts:
                            text = getattr(c.content.parts[0], "text", None)
                else:
                    response = self._model_legacy.generate_content(prompt)
                    text = getattr(response, "text", None)
                return _make_text_response(text or "")
            except Exception as e:
                last_exc = e
                if _is_quota_error(e):
                    break
                if attempt < max_retries:
                    delay = _parse_retry_delay_seconds(e)
                    time.sleep(min(delay, 5))
                else:
                    break

        # Gemini failed (any error): try Groq if available
        if last_exc and self._groq_client:
            try:
                text = self._generate_via_groq(prompt)
                err_msg = str(last_exc).strip()[:200]
                print(f"[LLM] Using Groq for: {operation_name or 'unknown'} (Gemini failed: {type(last_exc).__name__}: {err_msg})")
                if fallback_used_list is not None and operation_name:
                    fallback_used_list.append(operation_name)
                return _make_text_response(text)
            except Exception as groq_e:
                print(f"[LLM] Groq fallback failed: {groq_e}")
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Unexpected state in _generate_content_with_retry")

    def generate_query(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate an enhanced/optimized query from user input.
        
        Args:
            user_input: The original user query/input
            context: Optional context dictionary for query enhancement
            
        Returns:
            Enhanced query string
        """
        context_str = ""
        if context:
            context_str = f"\nContext: {context}"
        
        prompt = f"""You are a pharmaceutical research assistant. 
Given the user's input, generate an optimized and comprehensive query for pharmaceutical analysis.

User Input: {user_input}
{context_str}

Generate a well-structured query that:
1. Clarifies the molecule/drug name
2. Identifies key analysis dimensions needed
3. Includes relevant pharmaceutical terminology
4. Is suitable for pharmaceutical market research

Return only the optimized query, nothing else:"""

        try:
            response = self._generate_content_with_retry(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating query with Gemini (model: {getattr(self, 'current_model_name', 'unknown')}): {e}")
            if self.available_models and (self._client or self._model_legacy):
                for fallback_model_name in self.available_models:
                    if fallback_model_name != getattr(self, "current_model_name", ""):
                        try:
                            print(f"Trying fallback model: {fallback_model_name}")
                            if self._client:
                                r = self._client.models.generate_content(model=fallback_model_name, contents=prompt)
                                text = getattr(r, "text", None) or ""
                            else:
                                m = _google_genai_legacy.GenerativeModel(fallback_model_name)
                                r = m.generate_content(prompt)
                                text = getattr(r, "text", None) or ""
                            self.current_model_name = fallback_model_name
                            if self._model_legacy is not None:
                                self._model_legacy = _google_genai_legacy.GenerativeModel(fallback_model_name)
                            print(f"Successfully switched to model: {fallback_model_name}")
                            return text.strip()
                        except Exception:
                            continue
            print("All Gemini models failed, using original query")
            return user_input

    def extract_structured_context(
        self,
        user_input: str,
        complexity_hint: str = "normal",
        fallback_used_list: Optional[List[str]] = None,
    ) -> Optional[PharmaQueryContext]:
        """
        Extract structured pharmaceutical context (drug, disease, symptoms, regions, phase)
        from free-text query using Gemini. Returns None on failure so caller can use fallback.
        """
        prompt = f"""You are a pharmaceutical research assistant. Extract structured parameters from the user query. Output ONLY one valid JSON object, no other text, no markdown, no explanation.

User query: {user_input}
Complexity: {complexity_hint}

Rules:
- "query_type": "analysis" or "alternatives" (use "alternatives" only if user asks for alternatives to a specific drug).
- "reference_drug": only when query_type is "alternatives", else null.
- "drug": the main drug/molecule name. If user asks about "X medicine" or "medicine for X" (e.g. "asthma medicine"), set drug to null and put the condition in "disease" (e.g. disease="Asthma").
- "disease": primary indication/condition. Fix common typos. When the user mentions a drug (e.g. "Metformin", "metamorphin") but no condition, set disease to that drug's main approved indication (e.g. "Type 2 Diabetes" for Metformin).
- "diseases", "symptoms", "side_effects": arrays. When a drug is given, infer its known indications in "diseases" and common symptoms it treats or side effects (e.g. for Metformin: diseases=["Type 2 Diabetes"], symptoms=["hyperglycemia", "insulin resistance"], side_effects=["GI upset", "lactic acidosis risk"]). Use [] only if truly unknown.
- "regions", "phase": arrays/string as before; use [] or null if none.

Output this exact structure, one line only:
{{"query_type":"analysis","reference_drug":null,"drug":null,"disease":"...","diseases":[],"symptoms":[],"side_effects":[],"regions":[],"phase":null}}"""

        try:
            response = self._generate_content_with_retry(
                prompt,
                operation_name="query_understanding",
                fallback_used_list=fallback_used_list,
            )
            text = (response.text or "").strip()
            print(f"[Gemini] query_understanding raw response (first 300 chars): {repr(text[:300])}")
            data = _extract_first_json(text)
            if not data:
                print(f"[Gemini] query_understanding: no valid JSON in response; cannot extract context.")
                return None
            def _str_or_none(v):
                if v is None:
                    return None
                if isinstance(v, str):
                    return v.strip() or None
                if isinstance(v, dict):
                    return None  # LLM sometimes returns object e.g. {step_1, step_2}; do not pass to frontend
                return str(v).strip() or None

            def _str_list(v):
                if not isinstance(v, list):
                    return []
                return [x for x in v if isinstance(x, str) and x.strip()]

            drug = _str_or_none(data.get("drug"))
            disease = _str_or_none(data.get("disease"))
            diseases = _str_list(data.get("diseases"))
            symptoms = _str_list(data.get("symptoms"))
            side_effects = _str_list(data.get("side_effects"))
            regions = _str_list(data.get("regions"))
            phase = _str_or_none(data.get("phase"))
            query_type = (data.get("query_type") or "analysis").strip().lower()
            if query_type not in ("analysis", "alternatives"):
                query_type = "analysis"
            reference_drug = _str_or_none(data.get("reference_drug"))
            ctx = PharmaQueryContext(
                drug=drug,
                disease=disease,
                diseases=diseases or None,
                symptoms=symptoms or None,
                side_effects=side_effects or None,
                regions=regions or None,
                phase=phase if phase else None,
                raw_query=user_input or "",
                complexity=complexity_hint or "normal",
                query_type=query_type,
                reference_drug=reference_drug if reference_drug else None,
            )
            print(f"[Gemini] query_understanding extracted: drug={ctx.drug}, disease={ctx.disease}, symptoms={len(ctx.symptoms or [])}, diseases={len(ctx.diseases or [])}, side_effects={len(ctx.side_effects or [])}")
            return ctx
        except Exception as e:
            print(f"[Gemini] Error extracting structured context: {type(e).__name__}: {e}")
            return None

    def generate_pid_design(
        self,
        drug_name: str,
        target_volume_kg_per_year: Optional[float] = None,
        fallback_used_list: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Ask Gemini to design a conceptual P&ID for manufacturing the drug.
        Returns a dict matching the frontend PIDData schema (equipment, control_loops, reactor,
        process_conditions, material_handling) or None on failure.
        """
        vol_str = (
            f"{target_volume_kg_per_year:,.0f} kg/year"
            if target_volume_kg_per_year and target_volume_kg_per_year > 0
            else "Commercial Scale"
        )
        prompt = f"""Role: Senior Principal Process Engineer.
Task: Design a conceptual Process & Instrumentation Diagram (P&ID) for {drug_name} API manufacturing.
Scale: {vol_str}. Match equipment sizes and flow rates to this production scale so that capacity (kg API/year) is plausible (e.g. for thousands of tons/year use larger reactors and higher flow rates; for hundreds of tons use smaller vessels).

Requirements:
1. Define the REAL chemical synthesis route (e.g. key reactants, solvents) for {drug_name}.
2. Select appropriate reactor types (CSTR, PFR, GLR) and materials (SS316L, Hastelloy, Glass-Lined).
3. Include critical downstream unit operations: ONE separator, ONE crystallizer, ONE filter, ONE dryer (no duplicates).
4. Specify realistic operating conditions (Temp, Pressure) for each unit.
5. Keep the equipment list CONCISE: 2-4 feed tanks (one per reactant/catalyst), 1-2 reactors, exactly one separator (S-201), one crystallizer (C-301), one filter, one dryer. Use unique ids: FEED-001, FEED-002, R-101, R-102, S-201, C-301, etc. Do NOT add multiple separators or crystallizers or overlapping units. Reactor volume and feed rates must be consistent with the stated scale (e.g. Commercial Scale or N kg/year).

Output STRICTLY JSON (no markdown). Use this structure:

{{
  "equipment": [
    {{ "id": "FEED-001", "type": "Feed Tank", "name": "Reactant A Feed", "temperature": 25, "pressure": 1.0, "specs": {{ "volume": "2000L", "material": "SS316" }} }},
    {{ "id": "FEED-002", "type": "Feed Tank", "name": "Reactant B Feed", "temperature": 25, "pressure": 1.0, "specs": {{ "volume": "2000L" }} }},
    {{ "id": "R-101", "type": "CSTR Reactor", "name": "Main Reactor", "temperature": 120, "pressure": 4.5, "specs": {{ "volume": "6000L", "material": "Glass-Lined Steel" }} }},
    {{ "id": "S-201", "type": "Separator", "name": "Separator", "temperature": 80, "pressure": 3.0, "specs": {{ "type": "Decanter" }} }},
    {{ "id": "C-301", "type": "Crystallizer", "name": "Crystallizer", "temperature": 20, "pressure": 2.0, "specs": {{ "type": "Cooling" }} }},
    {{ "id": "F-401", "type": "Filter", "name": "Filter", "temperature": 25, "pressure": 1.0, "specs": {{}} }},
    {{ "id": "D-501", "type": "Dryer", "name": "Dryer", "temperature": 60, "pressure": 1.0, "specs": {{}} }}
  ],
  "control_loops": [
    {{ "tag": "TIC-101", "description": "Reactor Temp", "setpoint": 120, "range": [0, 200], "unit": "°C" }},
    {{ "tag": "PIC-101", "description": "Reactor Pressure", "setpoint": 4.5, "range": [0, 10], "unit": "bar" }},
    {{ "tag": "LIC-201", "description": "Separator Level", "setpoint": 50, "range": [0, 100], "unit": "%" }}
  ],
  "reactor": {{ "temperature": 120, "pressure": 4.5, "volume": 6000 }},
  "process_conditions": {{
    "operating_temperature_range": "25-140°C",
    "operating_pressure_range": "Vacuum-5 bar",
    "number_of_reactors": 1,
    "reactor_types": ["CSTR"],
    "number_of_steps": 1
  }},
  "material_handling": {{
    "target_molecule": "{drug_name}",
    "reactants": ["Specific reactant 1 for this API", "Specific reactant 2"],
    "catalysts": ["Catalyst if needed"],
    "intermediates": [],
    "products": ["Crystalline {drug_name}"],
    "recycle_streams": [],
    "synthesis_route": "Brief description for {drug_name}"
  }}
}}

Use realistic chemistry for {drug_name}. Return ONLY the JSON object; no duplicate equipment (one separator, one crystallizer, one filter, one dryer)."""

        try:
            response = self._generate_content_with_retry(
                prompt,
                operation_name="pid_design",
                fallback_used_list=fallback_used_list,
            )
            text = (response.text or "").strip()
            data = _extract_first_json(text)
            if not data:
                print("Gemini P&ID Error: No valid JSON in response (extract failed).")
                return None
            # Normalize to schema expected by frontend and TechnoEconomicAgent
            equipment = data.get("equipment") or []
            if not isinstance(equipment, list):
                equipment = []
            control_loops = data.get("control_loops") or []
            if not isinstance(control_loops, list):
                control_loops = []
            reactor = data.get("reactor") or {}
            if not isinstance(reactor, dict):
                reactor = {}
            reactor.setdefault("temperature", 80)
            reactor.setdefault("pressure", 5)
            reactor.setdefault("volume", 5000)
            process_conditions = data.get("process_conditions") or {}
            if not isinstance(process_conditions, dict):
                process_conditions = {}
            process_conditions.setdefault("number_of_reactors", 1)
            process_conditions.setdefault("reactor_types", ["CSTR"])
            process_conditions.setdefault("number_of_steps", 1)
            material_handling = data.get("material_handling") or {}
            if not isinstance(material_handling, dict):
                material_handling = {}
            material_handling["target_molecule"] = drug_name
            if "reactants" not in material_handling or not material_handling["reactants"]:
                material_handling["reactants"] = ["Precursor", "Solvent"]
            if "catalysts" not in material_handling or not material_handling["catalysts"]:
                material_handling["catalysts"] = []
            return {
                "equipment": equipment,
                "control_loops": control_loops,
                "reactor": reactor,
                "process_conditions": process_conditions,
                "material_handling": material_handling,
            }
        except Exception as e:
            print(f"Gemini P&ID Error: {e}")
            print(f"Error generating P&ID design with Gemini: {e}")
            return None

    # Same system prompt as ClinicalTrails.gov main.py for intent-based clinical search
    _CLINICAL_TRIAL_SYSTEM_PROMPT = """You are an expert Pharmaceutical Research Agent.

RULES:
1. DISCOVERY (Repurposing): User asks "What else can [Drug] do?" or "repurposing ideas". Put drug's main indication in disease to exclude it.
2. VALIDATION: User asks if a SPECIFIC drug works for a SPECIFIC disease (e.g. "Does Metformin help PCOS?").
3. REVERSE_DISCOVERY: User has a condition/disease and wants treatments or medicines for it (e.g. "asthma medicine", "medicine for asthma", "diabetes drugs"). Set disease=condition (fix typos: Asthama->Asthma), drug=null, intent=REVERSE_DISCOVERY.
4. BROAD: User gives only a specific drug name (e.g. "Paracetamol", "Ibuprofen").
Important: "X medicine" or "medicine for X" = REVERSE_DISCOVERY with disease=X, drug=null. Do not treat "X medicine" as a drug name."""

    def get_clinical_trial_decision(
        self,
        user_prompt: str,
        fallback_used_list: Optional[List[str]] = None,
    ):
        """
        Classify user prompt into AgentDecision (drug, disease, intent, reasoning).
        Returns AgentDecision or None on failure.
        """
        from .clinical_trials_tools import AgentDecision, SearchIntent
        prompt = f"""{self._CLINICAL_TRIAL_SYSTEM_PROMPT}

Output ONLY one JSON object with keys: "drug", "disease", "intent" (DISCOVERY|VALIDATION|BROAD|REVERSE_DISCOVERY), "reasoning". No other text.

User input: {user_prompt}"""

        try:
            print(f"[ClinicalTrials] Gemini classifying prompt: {user_prompt[:80]}...")
            response = self._generate_content_with_retry(
                prompt,
                operation_name="clinical_trial_decision",
                fallback_used_list=fallback_used_list,
            )
            text = (response.text or "").strip()
            data = _extract_first_json(text)
            if not data:
                return None
            intent_str = (data.get("intent") or "BROAD").upper()
            if intent_str not in ("DISCOVERY", "VALIDATION", "BROAD", "REVERSE_DISCOVERY"):
                intent_str = "BROAD"
            decision = AgentDecision(
                drug=data.get("drug"),
                disease=data.get("disease"),
                intent=SearchIntent(intent_str),
                reasoning=data.get("reasoning", ""),
            )
            print(f"[ClinicalTrials] Gemini decision: intent={decision.intent}, drug={decision.drug}, disease={decision.disease}")
            return decision
        except Exception as e:
            print(f"[ClinicalTrials] Gemini decision error: {e}")
            return None

    def extract_clinical_trials_insights(
        self,
        results: List[Dict[str, Any]],
        drug_name: Optional[str] = None,
        max_trials_to_use: int = 20,
        fallback_used_list: Optional[List[str]] = None,
    ) -> Dict[str, List[str]]:
        """
        Process clinical trials API response with Gemini to extract structured insights:
        - symptoms: symptoms/outcomes the drug can help with (from conditions, outcomes, descriptions)
        - diseases: diseases/conditions the drug is studied for
        - side_effects: reported or potential side effects (from descriptions, outcomes, eligibility)

        Returns {"symptoms": [], "diseases": [], "side_effects": []}. Uses a condensed
        summary of trial data to stay within token limits.
        """
        if not results:
            return {"symptoms": [], "diseases": [], "side_effects": []}

        # Build condensed input: title, conditions, brief_summary (truncated), primary_outcome per trial
        lines: List[str] = []
        for i, r in enumerate(results[:max_trials_to_use]):
            title = (r.get("title") or "Unknown")[:120]
            conditions = r.get("conditions") or []
            cond_str = ", ".join(conditions[:5]) if conditions else "—"
            summary = (r.get("brief_summary") or "")[:400]
            outcome = (r.get("primary_outcome") or "")[:200]
            eligibility = (r.get("eligibility") or "")[:300]
            lines.append(
                f"Trial {i+1}: {title}\n"
                f"  Conditions: {cond_str}\n"
                f"  Summary: {summary}\n"
                f"  Primary outcome: {outcome}\n"
                f"  Eligibility (excerpt): {eligibility}"
            )

        trials_text = "\n\n".join(lines)
        drug_hint = f" (drug/molecule: {drug_name})" if drug_name else ""

        prompt = f"""You are a pharmaceutical research expert. Below is condensed data from ClinicalTrials.gov studies{drug_hint}.

Extract and return exactly three lists. Be concise; deduplicate and use clear medical terms.

TRIAL DATA:
{trials_text}

Return a single JSON object with exactly these keys (arrays of strings only; use empty array if none found):
- "symptoms": symptoms or patient outcomes this drug/treatment is intended to help with (e.g. pain, fever, inflammation, HbA1c reduction).
- "diseases": diseases, disorders, or conditions this drug is studied for (deduplicate; use standard medical names).
- "side_effects": reported or potential adverse effects, safety concerns, or contraindications mentioned in summaries/eligibility/outcomes.

Rules: Return only the JSON object. No markdown, no explanation. Use short phrases. Maximum ~15 items per list. Deduplicate."""

        try:
            response = self._generate_content_with_retry(
                prompt,
                operation_name="clinical_trials_insights",
                fallback_used_list=fallback_used_list,
            )
            text = (response.text or "").strip()
            data = _extract_first_json(text)
            if not data:
                return {"symptoms": [], "diseases": [], "side_effects": []}
            symptoms = data.get("symptoms")
            diseases = data.get("diseases")
            side_effects = data.get("side_effects")
            if not isinstance(symptoms, list):
                symptoms = []
            if not isinstance(diseases, list):
                diseases = []
            if not isinstance(side_effects, list):
                side_effects = []
            return {
                "symptoms": [str(s).strip() for s in symptoms if s],
                "diseases": [str(d).strip() for d in diseases if d],
                "side_effects": [str(s).strip() for s in side_effects if s],
            }
        except Exception as e:
            print(f"Error extracting clinical trials insights with Gemini: {e}")
            return {"symptoms": [], "diseases": [], "side_effects": []}

    def get_indication_for_drug(
        self,
        drug_name: str,
        fallback_used_list: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Return the primary therapeutic indication(s) for a drug (e.g. Paracetamol -> Pain, Fever).
        Used for alternatives flow: find other drugs for the same indication.
        """
        prompt = f"""You are a pharmaceutical expert. What is the primary therapeutic indication or condition that the drug "{drug_name}" is used to treat? Reply with one short phrase only (e.g. "Pain, Fever" or "Type 2 Diabetes"), no explanation."""
        try:
            response = self._generate_content_with_retry(
                prompt,
                operation_name="get_indication",
                fallback_used_list=fallback_used_list,
            )
            text = (response.text or "").strip()
            return text if text else None
        except Exception as e:
            print(f"Error getting indication for {drug_name}: {e}")
            return None

    def get_molecular_details(
        self,
        molecule_name: str,
        fallback_used_list: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Use Gemini/Groq to get molecular name, family, weight, brief details, and physicochemical/
        API properties. Also adds structure_image_url (PubChem PNG) for the molecule.
        """
        if not (molecule_name or "").strip():
            return None
        prompt = f"""You are a pharmaceutical chemistry and API characterization expert. For the drug/molecule "{molecule_name.strip()}", provide the following as a single JSON object. Use concise strings; for "why_it_matters" fields use one short sentence. If a value is unknown, use null or omit.

Required base fields:
- molecular_name: standard IUPAC or common name (string)
- molecular_family: chemical class/family, e.g. NSAID, small molecule (string)
- molecular_weight_g_per_mol: approximate MW in g/mol (number only)
- brief_details: 2-4 sentences on structure, key functional groups, therapeutic relevance (string)

Physicochemical / API properties (provide when known; otherwise null or brief "unknown" where appropriate):
1. molecular_weight_impact: how MW impacts permeability, dissolution, dose size (string, optional)
2. solubility: e.g. "Poorly soluble in water; soluble in methanol, ethanol" (string)
3. solubility_why_it_matters: oral bioavailability, formulation implications (string, optional)
4. lipophilicity_log_p: e.g. "Log P ≈ 1.8–2.0" or "Log D 7.4 = ..." (string)
5. lipophilicity_why_it_matters: membrane permeability, solubility vs absorption (string, optional)
6. pka: e.g. "Weakly ionizable, largely neutral at physiological pH" (string)
7. pka_why_it_matters: dissolution across GI pH, formulation pH (string, optional)
8. melting_point: e.g. "~150–155 °C" (string)
9. melting_point_why_it_matters: thermal stability, process selection (string, optional)
10. crystalline_nature: e.g. "Crystalline; polymorphism possible" (string)
11. crystalline_why_it_matters: solubility, stability, polymorph control (string, optional)
12. hygroscopicity: e.g. "Low to moderate moisture sensitivity" (string)
13. hygroscopicity_why_it_matters: packaging, excipient compatibility, shelf-life (string, optional)
14. chemical_stability: e.g. "Stable under normal conditions; sensitive to oxidation/hydrolysis" (string)
15. chemical_stability_why_it_matters: storage, antioxidants/excipients (string, optional)
16. particle_size_surface_area: e.g. "Micronized API often preferred" (string)
17. particle_size_why_it_matters: dissolution rate, content uniformity (string, optional)
18. bcs_class: e.g. "BCS Class II" (string)
19. permeability_notes: e.g. "High permeability, low solubility" (string, optional)
20. permeability_why_it_matters: rate-limiting step, solubility vs permeability focus (string, optional)
21. solid_state_properties: e.g. "Polymorphism, crystal habit, flowability" (string)
22. solid_state_why_it_matters: compression, blend uniformity, scale-up (string, optional)
23. excipient_compatibility: e.g. "Must be tested with fillers, binders, lubricants" (string)
24. excipient_why_it_matters: prevent degradation, consistent drug release (string, optional)

Return ONLY a single JSON object with the above keys. Use null for unknown optional fields. No other text."""

        try:
            response = self._generate_content_with_retry(
                prompt,
                operation_name="molecular_details",
                fallback_used_list=fallback_used_list,
            )
            text = (response.text or "").strip()
            data = _extract_first_json(text)
            if not data:
                return None
            name = (data.get("molecular_name") or molecule_name or "").strip()
            family = (data.get("molecular_family") or "").strip() or "N/A"
            try:
                weight = float(data.get("molecular_weight_g_per_mol") or 0)
            except (TypeError, ValueError):
                weight = 0
            details = (data.get("brief_details") or "").strip() or "No brief details available."
            safe_name = quote((name or molecule_name or "").strip())
            structure_image_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{safe_name}/PNG?image_size=400x400"

            out: Dict[str, Any] = {
                "molecular_name": name or molecule_name,
                "molecular_family": family,
                "molecular_weight_g_per_mol": weight,
                "brief_details": details,
                "structure_image_url": structure_image_url,
            }
            optional_keys = [
                "molecular_weight_impact", "solubility", "solubility_why_it_matters",
                "lipophilicity_log_p", "lipophilicity_why_it_matters", "pka", "pka_why_it_matters",
                "melting_point", "melting_point_why_it_matters", "crystalline_nature", "crystalline_why_it_matters",
                "hygroscopicity", "hygroscopicity_why_it_matters", "chemical_stability", "chemical_stability_why_it_matters",
                "particle_size_surface_area", "particle_size_why_it_matters", "bcs_class",
                "permeability_notes", "permeability_why_it_matters", "solid_state_properties", "solid_state_why_it_matters",
                "excipient_compatibility", "excipient_why_it_matters",
            ]
            for key in optional_keys:
                val = data.get(key)
                if val is not None and (isinstance(val, str) and val.strip() or not isinstance(val, str)):
                    out[key] = val.strip() if isinstance(val, str) else val
            return out
        except Exception as e:
            print(f"Error getting molecular details: {e}")
            return None

    def customize_response(
        self,
        raw_report: str,
        query: str,
        customization_instructions: Optional[str] = None
    ) -> str:
        """
        Customize and enhance the generated report using Gemini.
        
        Args:
            raw_report: The raw report content to customize
            query: Original query for context
            customization_instructions: Optional specific customization instructions
            
        Returns:
            Customized report string
        """
        instructions = customization_instructions or (
            "Enhance this pharmaceutical analysis report to be more professional, "
            "insightful, and actionable. Maintain all factual data but improve "
            "readability, add strategic insights, and ensure executive-level clarity."
        )
        
        prompt = f"""You are a pharmaceutical business analyst expert. 
Customize and enhance the following analysis report based on the original query.

Original Query: {query}

Customization Instructions: {instructions}

Raw Report:
{raw_report}

Please provide a customized, professional, and enhanced version of this report that:
1. Maintains all factual accuracy
2. Improves clarity and readability
3. Adds strategic insights and recommendations
4. Uses professional pharmaceutical industry terminology
5. Is suitable for executive presentation

Return the complete customized report:"""

        try:
            response = self._generate_content_with_retry(prompt, operation_name="customize_report")
            return (response.text or "").strip()
        except Exception as e:
            print(f"Error customizing response with Gemini: {e}")
            return raw_report

    def generate_insights(
        self,
        agent_results: list,
        query: str
    ) -> str:
        """
        Generate additional insights from agent results using Gemini.
        
        Args:
            agent_results: List of agent result summaries
            query: Original query for context
            
        Returns:
            Generated insights string
        """
        results_summary = "\n".join([
            f"- {result.agent_name}: {result.summary}"
            for result in agent_results
        ])
        
        prompt = f"""You are a Senior Pharmaceutical Strategic Consultant.
Analyze the following data for the molecule "{query}".

ACTION: Generate a strategic assessment.
DATA:
{results_summary}

OUTPUT FORMAT (Markdown):
### 🟢 Strategic Advantages
* [Insight 1]
* [Insight 2]

### 🔴 Critical Risks
* [Risk 1]
* [Risk 2]

### 💡 Executive Recommendation
[One clear, actionable sentence: Go, No-Go, or pivot?]

STRICT RULE: Do not use fluff words. Be direct and numerical where possible."""

        try:
            response = self._generate_content_with_retry(prompt, operation_name="generate_insights")
            return (response.text or "").strip()
        except Exception as e:
            print(f"Error generating insights with Gemini: {e}")
            return "Additional insights could not be generated at this time."

    # Indian city coordinates for plant site mapping (LLM returns city names)
    _INDIAN_CITY_COORDS: Dict[str, tuple] = {
        "hyderabad": (17.3850, 78.4867),
        "ahmedabad": (23.0225, 72.5714),
        "visakhapatnam": (17.7392, 83.2247),
        "vishakhapatnam": (17.7392, 83.2247),
        "chennai": (13.0827, 80.2707),
        "mumbai": (19.0760, 72.8777),
        "pune": (18.5204, 73.8567),
        "vadodara": (22.3072, 73.1812),
        "dahej": (21.7041, 72.5714),
        "bangalore": (12.9716, 77.5946),
        "bengaluru": (12.9716, 77.5946),
        "delhi": (28.7041, 77.1025),
        "gurgaon": (28.4595, 77.0266),
        "gurugram": (28.4595, 77.0266),
        "vizag": (17.7392, 83.2247),
        "baddi": (30.9463, 76.7794),
        "solan": (30.9045, 77.0962),
    }

    def get_plant_site_recommendations(
        self,
        molecule_name: str,
        indication: Optional[str] = None,
        fallback_used_list: Optional[List[str]] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Use Gemini/Groq to recommend pharma plant locations in India only.
        Returns list of dicts with name, city, country, lat, lng, scores (0-1), rationale.
        """
        ind_hint = f" for indication {indication}" if indication else ""
        prompt = f"""You are a pharmaceutical manufacturing and site-selection expert. Recommend exactly 5 plant locations in INDIA ONLY for manufacturing the drug/molecule: {molecule_name}{ind_hint}.

For each location provide: name (short site name), city (Indian city name only), energy_ease_score (0-1), land_availability_score (0-1), market_proximity_score (0-1), export_supply_score (0-1), and rationale (object with keys "energy", "land", "market", "export_supply" – each a short sentence).

Return ONLY a single JSON object with one key "sites" containing an array of exactly 5 objects. No other text.
Example format:
{{"sites": [
  {{"name": "Hyderabad Pharma City", "city": "Hyderabad", "energy_ease_score": 0.85, "land_availability_score": 0.88, "market_proximity_score": 0.82, "export_supply_score": 0.85, "rationale": {{"energy": "...", "land": "...", "market": "...", "export_supply": "..."}}}},
  ...4 more
]}}

Use only real Indian pharma hubs (e.g. Hyderabad, Ahmedabad, Visakhapatnam, Chennai, Mumbai, Pune, Vadodara, Dahej, Baddi in Himachal Pradesh). Include at least one location in Himachal Pradesh (Baddi/Solan) as it is a leading pharmaceutical manufacturing hub. Return only the JSON object."""

        try:
            response = self._generate_content_with_retry(
                prompt,
                operation_name="plant_site_recommendations",
                fallback_used_list=fallback_used_list,
            )
            text = (response.text or "").strip()
            data = _extract_first_json(text)
            if not data or "sites" not in data:
                return None
            raw_sites = data.get("sites")
            if not isinstance(raw_sites, list) or len(raw_sites) == 0:
                return None
            out: List[Dict[str, Any]] = []
            for i, s in enumerate(raw_sites[:5]):
                if not isinstance(s, dict):
                    continue
                city = (s.get("city") or "").strip() or "Hyderabad"
                city_lower = city.lower()
                lat, lng = self._INDIAN_CITY_COORDS.get(city_lower, (17.3850, 78.4867))
                energy = self._clamp_score_01(float(s.get("energy_ease_score", 0.8)))
                land = self._clamp_score_01(float(s.get("land_availability_score", 0.8)))
                market = self._clamp_score_01(float(s.get("market_proximity_score", 0.8)))
                export_s = self._clamp_score_01(float(s.get("export_supply_score", 0.8)))
                overall = (energy * 0.25 + land * 0.25 + market * 0.30 + export_s * 0.20)
                rationale = s.get("rationale") if isinstance(s.get("rationale"), dict) else {}
                out.append({
                    "name": (s.get("name") or city).strip() or f"Site {i+1}",
                    "city": city,
                    "country": "India",
                    "lat": lat,
                    "lng": lng,
                    "region_code": "India",
                    "energy_ease_score": energy,
                    "land_availability_score": land,
                    "market_proximity_score": market,
                    "export_supply_score": export_s,
                    "overall_site_score": min(1.0, max(0.0, overall)),
                    "rationale": {
                        k: str(v).strip() for k, v in (rationale or {}).items()
                        if k in ("energy", "land", "market", "export_supply") and v
                    },
                })
            return out if out else None
        except Exception as e:
            print(f"Error getting plant site recommendations: {e}")
            return None

    @staticmethod
    def _clamp_score_01(x: float) -> float:
        try:
            return min(1.0, max(0.0, float(x)))
        except (TypeError, ValueError):
            return 0.8

