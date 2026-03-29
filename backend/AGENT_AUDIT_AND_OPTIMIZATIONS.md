`# Agent audit: 404 fix, hardcoded/random outputs, and optimizations

## 1. Why the 404 error happens (and what was changed)

**Cause:** The app prefers the **new** Google GenAI SDK (`google.genai` from `pip install google-genai`) when it’s installed. That SDK can call an endpoint that returns **404 Not Found** for some models when using **Google AI Studio** API keys (e.g. `AIza...`). So every Gemini call fails with 404 and the log shows fallback to Groq for each operation.

**Changes made:**

- **Model order:** Default model list now tries **gemini-1.5-flash** and **gemini-1.5-pro** first (more widely available), then 2.0/2.5.
- **404 → legacy SDK:** If the new SDK returns 404 for every model, the code automatically tries the **legacy** SDK (`google.generativeai`), which works with AI Studio keys.
- **Env option:** You can force the legacy SDK by setting in `.env`:
  ```bash
  GEMINI_USE_LEGACY=1
  ```
  Then restart the backend; Gemini should stop 404’ing and Groq fallback won’t be used for every call.

**Quick fix:** Add `GEMINI_USE_LEGACY=1` to `Agentichost-main/.env` and restart the server.

---

## 2. Agents: real vs hardcoded / deterministic / fallback

| Agent | Real data / LLM | Hardcoded / random / fallback | UI impact |
|-------|------------------|-------------------------------|-----------|
| **Query understanding** | LLM (Gemini/Groq) | None | Correct drug/disease when Gemini works; when Gemini 404’s, Groq is used. |
| **IQVIA Insights** | LLM only | On LLM failure: **empty** structure (zeros, "N/A", empty lists) — no fake numbers | UI shows "Data unavailable" / zeros if LLM fails. |
| **EXIM Trends** | LLM only | On LLM failure: **empty** structure (0.0 scores, "Data unavailable") | Same as above. |
| **Clinical Trials** | Real API (clinicaltrials.gov) + LLM for intent/drug | None for trials; intent uses LLM (Groq if Gemini 404’s) | Real trials; intent can be wrong if LLM is weak. |
| **Process Design (PID)** | Gemini/Groq for PID when available | **Fallback:** rule-based `_generate_pid_data` (molecule + seed) — deterministic, not random | UI shows either LLM-generated or rule-based PID; rule-based is plausible but not from real data. |
| **Techno-Economic** | LLM for economic constants when available | **Fallback:** **hardcoded** factors and seed-based variation (installation_factor, piping_factor, equipment costs, etc.) | CAPEX/OPEX/IRR can look “random” when LLM fails because of seed-based variation. |
| **Demographics** | LLM for plant site recommendations (India) when available | **Scores:** seed-based formulas (disease_burden, age_fit, affordability). **Sites:** fallback = **fixed list** `PLANT_SITE_CANDIDATES` (e.g. Hyderabad, Ahmedabad, Baddi) shuffled by seed; Baddi forced in | Map and scores are deterministic per run; not real demographic data. |
| **Report generation** | LLM (Gemini/Groq) | None | Report reflects whatever the pipeline returned; no dummy text. |

**Summary:**

- **Fully LLM/API (no hardcoded numbers):** Query understanding, IQVIA, EXIM, Report. On LLM failure they either fail or return **empty/minimal** structures (no fake trends).
- **Hybrid (LLM + fallback):** Process Design (PID), Techno-Economic (constants), Demographics (plant sites). Fallbacks are **deterministic** (seed + rules) or **fixed lists**, not random number generators, but they are not real data.
- **Real external API:** Clinical Trials only (clinicaltrials.gov).

---

## 3. Cross-check with UI

- **Dashboard / report:** Market size, EXIM, trials, PID, CAPEX/OPEX, plant map come from the pipeline above. If you see “Data unavailable” or zeros in market/EXIM, the LLM (or its fallback) failed or returned empty. If you see consistent numbers and sites every run for the same query, that’s the deterministic/seed-based fallback.
- **“Groq was used as fallback”** in the report or logs means Gemini failed (e.g. 404); Groq was used for that step. Fixing 404 (e.g. `GEMINI_USE_LEGACY=1`) will reduce Groq fallback and make Gemini-driven outputs (query understanding, IQVIA, EXIM, PID, constants, plant sites, report) consistent with what the UI expects.

---

## 4. Suggested optimizations (Agentic host)

1. **Eliminate 404 in production:** Set `GEMINI_USE_LEGACY=1` when using AI Studio keys, or rely on the new auto-fallback to legacy when 404 is detected (already implemented).
2. **Techno-Economic:** When LLM constants are unavailable, consider a **fixed** set of conservative defaults (e.g. one “generic small molecule” profile) instead of seed-based variation, so reports don’t look randomly different across runs.
3. **Demographics:** Optionally label in the API/UI when plant sites are “LLM-recommended” vs “default India list” so the user knows the source.
4. **Process Design:** Same idea: expose in the API/UI whether PID came from “LLM” or “rule-based fallback” (e.g. `pid_data.source` or similar already exists; ensure the UI shows it).
5. **IQVIA/EXIM:** Keep current behavior (empty structure on failure); consider a one-line user-facing message like “Market/EXIM data could not be loaded (LLM unavailable).” in the UI when the payload is empty.
6. **Logging:** Reduce log noise by logging “Using Groq for: &lt;op&gt;” once per run (or per op) instead of every call, or only when `fallback_used_list` is updated.

---

## 5. Files touched for 404 fix

- `app/services/gemini_service.py`: model order, 404 detection, auto legacy fallback, `GEMINI_USE_LEGACY` support.
- `.env.example`: comment for `GEMINI_USE_LEGACY=1`.
