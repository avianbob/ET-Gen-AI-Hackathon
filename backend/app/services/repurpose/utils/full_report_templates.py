"""
Template text for unified report sections (process / TEA / demographics).
Used by LangGraph and to backfill cached search results that predate the extension node.
"""

from __future__ import annotations

from typing import Any, Dict, List


def template_full_report_extensions(drug_name: str, top_indications: str = "") -> Dict[str, str]:
    drug = (drug_name or "Unknown").strip() or "Unknown"
    tops = (top_indications or "").strip() or "general repurposing hypotheses"
    return {
        "process_design": (
            f"**{drug} — process design (summary)**\n\n"
            "High-level oral solid or sterile routing depends on API physicochemistry and the target dosage form from labeling and evidence. "
            "Apply QbD to tie critical process parameters to dissolution, purity, and stability; align scale-up with GMP expectations for repurposing "
            "programs (e.g. 505(b)(2) style filings where applicable)."
        ),
        "techno_economic": (
            f"**{drug} — techno-economics (indicative)**\n\n"
            "Order-of-magnitude COGS is driven by batch scale, yield, solvent recovery, and packaging choices. "
            "Full business cases should layer in clinical stage, pricing, and share assumptions using the market and competition signals from this search—not investment advice."
        ),
        "demographics_sites": (
            f"**{drug} — demographics & manufacturing footprint**\n\n"
            f"Opportunity themes from this run: **{tops}**. For India-scale supply, clusters such as Hyderabad, Ahmedabad, or Vizag often balance API synergy, talent, and export logistics—"
            "subject to state incentives, environmental compliance, and target market geography."
        ),
    }


def _indication_line(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("indication") or "").strip()
    ind = getattr(item, "indication", None)
    return str(ind or "").strip()


def top_indications_csv_from_payload(cached: Dict[str, Any], limit: int = 8) -> str:
    """Best-effort top indications string from enhanced or ranked lists."""
    enhanced = cached.get("enhanced_indications") or []
    ranked = cached.get("ranked_indications") or []
    seq: List[Any] = list(enhanced) if enhanced else list(ranked)
    names: List[str] = []
    for item in seq[:limit]:
        n = _indication_line(item)
        if n and n.lower() != "unknown indication":
            names.append(n)
    return ", ".join(names) if names else ""


def ensure_full_report_extensions_on_cache(cached: Dict[str, Any]) -> None:
    """
    Mutate cached_result in place: if full_report_extensions missing or empty, attach templates.
    Does not replace non-empty LLM-generated sections.
    """
    ext = cached.get("full_report_extensions")
    if isinstance(ext, dict) and ext.get("process_design") and ext.get("techno_economic") and ext.get("demographics_sites"):
        return
    drug = str(cached.get("drug_name") or "Unknown").strip()
    tops = top_indications_csv_from_payload(cached)
    cached["full_report_extensions"] = template_full_report_extensions(drug, tops)
