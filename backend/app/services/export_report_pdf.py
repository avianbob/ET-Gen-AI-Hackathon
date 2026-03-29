"""
Full report PDF export: same sequence as Dashboard UI, with all details
(including data not shown in the UI). Accepts the full analysis result payload.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from fpdf import FPDF


def _safe(s: Any, max_len: int = 2000) -> str:
    """Encode to ASCII-safe string for FPDF (latin-1 compatible)."""
    if s is None:
        return ""
    if isinstance(s, (int, float)):
        return str(s)
    if isinstance(s, bool):
        return "Yes" if s else "No"
    if isinstance(s, (list, dict)):
        return _safe(json.dumps(s, default=str)[:max_len])
    text = str(s).strip()
    # Replace chars that may cause FPDF encoding issues
    out = "".join(c if ord(c) < 256 else "?" for c in text)
    return out[:max_len] if len(out) > max_len else out


def _section_title(pdf: FPDF, title: str) -> None:
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, _safe(title), ln=1, fill=True)
    pdf.ln(2)


def _strip_markdown_bold(text: str) -> str:
    """Remove **bold** markdown from text."""
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", text).replace("**", "")


def _filter_recommendation_date(text: str) -> str:
    """Remove 'Recommendation date:' line/section from report text."""
    # Remove single line: "Recommendation date: February 11, 2026"
    text = re.sub(r"\n?\s*Recommendation\s+date\s*:\s*[^\n]+", "", text, flags=re.IGNORECASE)
    # Remove section starting with **Recommendation Date:**
    pattern = r"\n\s*(?:\*\*)?\s*Recommendation\s+Date\s*(?:\*\*)?\s*:?\s*[^\n]*(?:\n(?![*\d#\s]).[^\n]*)*"
    return re.sub(pattern, "", text, flags=re.IGNORECASE)


def _body(pdf: FPDF, text: str, indent: bool = False) -> None:
    pdf.set_font("Helvetica", "", 10)
    for line in text.split("\n"):
        line = _safe(_strip_markdown_bold(line.strip()))
        if not line:
            pdf.ln(3)
            continue
        if indent:
            pdf.cell(8)
        pdf.multi_cell(0, 6, line)
    pdf.ln(2)


def _key_value(pdf: FPDF, key: str, value: Any) -> None:
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(60, 6, _safe(key)[:55] + ":", ln=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 6, _safe(value, 500))
    pdf.ln(1)


def _dict_section(pdf: FPDF, data: Dict[str, Any], title: str, skip_keys: Optional[List[str]] = None) -> None:
    if not data or not isinstance(data, dict):
        return
    skip_keys = skip_keys or []
    _section_title(pdf, title)
    for k, v in data.items():
        if k in skip_keys or v is None:
            continue
        if isinstance(v, (dict, list)):
            _key_value(pdf, k, json.dumps(v, default=str, indent=2)[:800])
        else:
            _key_value(pdf, k, v)
    pdf.ln(3)


def build_full_report_pdf(result: Dict[str, Any], filename: str) -> str:
    """
    Build a PDF report in the same sequence as the Dashboard UI, including
    all details (even those not shown in the UI). Returns absolute path to the created file.
    """
    import os
    import tempfile
    from datetime import datetime

    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    drug = (result.get("query_context") or {}).get("drug") or result.get("agent_id") or "Report"
    drug_safe = _safe(drug, 80)

    # ----- 1. Cover / Title -----
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 14, "ET PharmAI - Full Analysis Report", ln=1, align="C")
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, drug_safe, ln=1, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", ln=1, align="C")
    pdf.ln(8)

    # ----- 2. Query context -----
    qc = result.get("query_context") or {}
    _section_title(pdf, "1. Query context")
    _key_value(pdf, "Drug / Molecule", qc.get("drug"))
    _key_value(pdf, "Disease / Indication", qc.get("disease"))
    _key_value(pdf, "Regions", ", ".join(qc.get("regions") or []) or "N/A")
    _key_value(pdf, "Phase", qc.get("phase"))
    _key_value(pdf, "Symptoms", ", ".join(qc.get("symptoms") or []) or "N/A")
    _key_value(pdf, "Side effects", ", ".join(qc.get("side_effects") or []) or "N/A")
    _key_value(pdf, "Diseases (list)", ", ".join(qc.get("diseases") or []) or "N/A")
    _key_value(pdf, "Raw query", qc.get("raw_query"))
    pdf.ln(3)

    # ----- 3. Feasibility / Grading -----
    grading = result.get("grading") or {}
    _section_title(pdf, "2. Feasibility score (grading)")
    for key in ("market_demand", "production_feasibility", "demographics", "patents_and_trials", "competition", "overall_score"):
        v = grading.get(key)
        if v is not None:
            label = key.replace("_", " ").title()
            pct = f"{float(v) * 100:.1f}%" if isinstance(v, (int, float)) else _safe(v)
            _key_value(pdf, label, pct)
    pdf.ln(3)

    # ----- 4. Molecular details (basic + Physicochemical & API properties) -----
    vd = result.get("visual_data") or {}
    mol = vd.get("molecular_details") or {}
    if mol:
        _section_title(pdf, "3. Molecular details")
        basic_keys = ("molecular_name", "molecular_family", "molecular_weight_g_per_mol", "molecular_weight_impact")
        for k in basic_keys:
            v = mol.get(k)
            if v is not None and v != "":
                _key_value(pdf, k.replace("_", " ").title(), v)
        pdf.ln(2)
        # Physicochemical & API properties (explicit section)
        phys_keys = [
            ("solubility", "Solubility"),
            ("lipophilicity_log_p", "Lipophilicity (Log P / Log D)"),
            ("pka", "pKa"),
            ("melting_point", "Melting point"),
            ("crystalline_nature", "Crystalline vs amorphous"),
            ("hygroscopicity", "Hygroscopicity"),
            ("chemical_stability", "Chemical stability"),
            ("particle_size_surface_area", "Particle size & surface area"),
            ("bcs_class", "Permeability (BCS)"),
            ("permeability_notes", "Permeability notes"),
            ("solid_state_properties", "Solid-state properties"),
            ("excipient_compatibility", "Compatibility with excipients"),
        ]
        phys_items = [(label, mol.get(k)) for k, label in phys_keys if mol.get(k) not in (None, "")]
        if phys_items:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Physicochemical & API properties:", ln=1)
            pdf.set_font("Helvetica", "", 9)
            for label, v in phys_items:
                _key_value(pdf, label, v)
            pdf.ln(2)
        # Any other molecular keys not yet covered
        for k, v in mol.items():
            if k in ("structure_image_url",) or k in [pk for pk, _ in phys_keys] or k in basic_keys or v is None or v == "":
                continue
            _key_value(pdf, k.replace("_", " ").title(), v)
        pdf.ln(3)

    # ----- 5. Brief details -----
    if mol.get("brief_details"):
        _section_title(pdf, "4. Brief details")
        _body(pdf, mol.get("brief_details", ""))
        pdf.ln(2)

    # ----- 6. Symptoms / Disease / Side effects (summary) -----
    _section_title(pdf, "5. Symptoms, disease & side effects summary")
    _key_value(pdf, "Disease", qc.get("disease"))
    _key_value(pdf, "Symptoms", ", ".join(qc.get("symptoms") or []) or "N/A")
    _key_value(pdf, "Side effects", ", ".join(qc.get("side_effects") or []) or "N/A")
    insights = (result.get("clinical_trials_data") or {}).get("extracted_insights") or {}
    if insights:
        _key_value(pdf, "Extracted symptoms (trials)", ", ".join(insights.get("symptoms") or []) or "N/A")
        _key_value(pdf, "Extracted diseases (trials)", ", ".join(insights.get("diseases") or []) or "N/A")
        _key_value(pdf, "Extracted side effects (trials)", ", ".join(insights.get("side_effects") or []) or "N/A")
    pdf.ln(3)

    # ----- 7. P&ID (full equipment, control loops, process conditions) -----
    pid = result.get("pid_data") or {}
    if pid:
        _section_title(pdf, "6. Process & instrumentation (P&ID) details")
        if pid.get("process_conditions"):
            _key_value(pdf, "Process conditions", json.dumps(pid["process_conditions"], indent=2))
        if pid.get("reactor"):
            _key_value(pdf, "Reactor", json.dumps(pid["reactor"], indent=2))
        equipment = pid.get("equipment") or []
        if equipment:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Equipment:", ln=1)
            pdf.set_font("Helvetica", "", 9)
            for eq in equipment:
                pdf.cell(10)
                pdf.multi_cell(0, 5, _safe(json.dumps(eq, default=str), 400))
            pdf.ln(2)
        control_loops = pid.get("control_loops") or []
        if control_loops:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Control loops:", ln=1)
            pdf.set_font("Helvetica", "", 9)
            for cl in control_loops:
                pdf.cell(10)
                pdf.multi_cell(0, 5, _safe(json.dumps(cl, default=str), 300))
            pdf.ln(2)
        # Full PID dump for anything not covered
        for key in ("material_handling", "stages", "unit_operations"):
            if key in pid and pid[key]:
                _key_value(pdf, f"P&ID: {key}", json.dumps(pid[key], default=str, indent=2)[:600])
        pdf.ln(3)

    # ----- 8. Market & EXIM (full data) -----
    market = vd.get("market_data") or {}
    exim = vd.get("exim_data") or {}
    if market or exim:
        _section_title(pdf, "7. Market (IQVIA) & EXIM data")
        if market:
            _dict_section(pdf, market, "Market data (IQVIA)", skip_keys=[])
            pdf.ln(1)
        if exim:
            _dict_section(pdf, exim, "EXIM trade data", skip_keys=[])
        pdf.ln(3)

    # ----- 9. Competitor / cost per kg -----
    tea = result.get("tea_data") or {}
    if tea.get("cost_per_kg_usd") is not None or tea.get("product_price_usd_per_kg") is not None:
        _section_title(pdf, "8. Cost & pricing (competitor context)")
        _key_value(pdf, "Cost per kg (USD)", tea.get("cost_per_kg_usd"))
        _key_value(pdf, "Product price USD per kg", tea.get("product_price_usd_per_kg"))
        pdf.ln(3)

    # ----- 10. TEA (full CAPEX/OPEX/financials) -----
    if tea:
        _section_title(pdf, "9. Techno-economic analysis (full breakdown)")
        capex_keys = [
            "equipment_capex_million_usd", "installation_capex_million_usd",
            "piping_instrumentation_capex_million_usd", "buildings_infrastructure_capex_million_usd",
            "engineering_design_capex_million_usd", "contingency_capex_million_usd", "total_capex_million_usd",
        ]
        opex_keys = [
            "raw_material_cost_million_usd_per_year", "utility_cost_million_usd_per_year",
            "labor_cost_million_usd_per_year", "maintenance_cost_million_usd_per_year",
            "insurance_overhead_cost_million_usd_per_year", "total_opex_million_usd_per_year",
        ]
        fin_keys = [
            "revenue_million_usd_per_year", "gross_profit_million_usd_per_year", "gross_margin_percent",
            "payback_period_years", "internal_rate_of_return", "net_present_value_million_usd",
            "production_capacity_kg_per_year", "production_feasibility_score", "pid_based",
        ]
        for k in capex_keys:
            if k in tea and tea[k] is not None:
                _key_value(pdf, k.replace("_", " ").title(), tea[k])
        pdf.ln(1)
        for k in opex_keys:
            if k in tea and tea[k] is not None:
                _key_value(pdf, k.replace("_", " ").title(), tea[k])
        pdf.ln(1)
        for k in fin_keys:
            if k in tea and tea[k] is not None:
                _key_value(pdf, k.replace("_", " ").title(), tea[k])
        if tea.get("equipment_costs"):
            _key_value(pdf, "Equipment costs (detail)", json.dumps(tea["equipment_costs"], default=str)[:600])
        pdf.ln(3)

    # ----- 11. Clinical trials (decision, analytics, full results) -----
    ctd = result.get("clinical_trials_data") or {}
    if ctd:
        _section_title(pdf, "10. Drug indications & clinical trials")
        if ctd.get("decision"):
            _key_value(pdf, "Search decision", json.dumps(ctd["decision"], indent=2))
        if ctd.get("analytics"):
            _key_value(pdf, "Analytics (phase/sponsor distribution, total)", json.dumps(ctd["analytics"], indent=2))
        _key_value(pdf, "Ongoing trials count", ctd.get("ongoing_trials_count"))
        results_list = ctd.get("results") or []
        if results_list:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Trial results (full detail, {len(results_list)} trials):", ln=1)
            pdf.set_font("Helvetica", "", 9)
            for i, t in enumerate(results_list[:30], 1):
                pdf.cell(5)
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 5, f"Trial {i}: {_safe(t.get('title') or t.get('id'), 120)}", ln=1)
                pdf.set_font("Helvetica", "", 9)
                for f in ("id", "status", "phases", "sponsor", "conditions", "brief_summary", "primary_outcome", "eligibility"):
                    val = t.get(f)
                    if val is not None and val != "":
                        if isinstance(val, list):
                            val = ", ".join(str(x) for x in val)
                        pdf.cell(10)
                        pdf.multi_cell(0, 5, f"  {f}: {_safe(str(val), 400)}")
                pdf.ln(2)
            if len(results_list) > 30:
                pdf.cell(5)
                pdf.cell(0, 5, f"... and {len(results_list) - 30} more trials.", ln=1)
        pdf.ln(3)

    # ----- 12. Plant site recommendations -----
    demo = vd.get("demographic_data") or {}
    sites = demo.get("plant_site_recommendations") or []
    if sites or demo:
        _section_title(pdf, "11. Demographic & plant site recommendations")
        if demo:
            _key_value(pdf, "Disease burden score", demo.get("disease_burden_score"))
            _key_value(pdf, "Demographic overall score", demo.get("demographic_overall_score"))
            _key_value(pdf, "Age distribution fit score", demo.get("age_distribution_fit_score"))
            _key_value(pdf, "Access affordability score", demo.get("access_affordability_score"))
        if sites:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Plant sites ({len(sites)}):", ln=1)
            pdf.set_font("Helvetica", "", 9)
            for s in sites:
                pdf.cell(5)
                pdf.multi_cell(0, 5, _safe(json.dumps(s, default=str), 350))
            pdf.ln(2)
        pdf.ln(3)

    # ----- 13. Investment memorandum (full report text) -----
    _section_title(pdf, "12. Final investment memorandum")
    report_text = result.get("analysis") or result.get("report_content") or ""
    if report_text:
        report_text = _filter_recommendation_date(_strip_markdown_bold(report_text))
        _body(pdf, report_text)
    pdf.ln(3)

    # ----- 14. LLM fallback notice -----
    fallback = result.get("llm_fallback_used") or []
    if fallback:
        _section_title(pdf, "13. Note (LLM fallback)")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 6, _safe("Groq was used as fallback for: " + ", ".join(fallback)))
    pdf.ln(2)

    # Footer on last page
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, "ET PharmAI - Full Report Export. Confidential.", align="C", ln=1)

    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    pdf.output(filepath)
    return filepath
