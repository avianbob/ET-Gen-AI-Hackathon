# backend/app/agents/demographics/demographic.py
import hashlib
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest

if TYPE_CHECKING:
    from ...services.gemini_service import GeminiService

# Himachal Pradesh (Baddi) – leading pharma manufacturing hub; always included in recommendations
HIMACHAL_SITE: Dict[str, Any] = {
    "name": "Baddi Pharma Hub (Himachal Pradesh)",
    "city": "Baddi",
    "country": "India",
    "region_code": "India",
    "lat": 30.9463,
    "lng": 76.7794,
}

# Fallback: Indian pharma hubs when LLM is unavailable
PLANT_SITE_CANDIDATES: List[Dict[str, Any]] = [
    {"name": "Hyderabad Pharma City", "city": "Hyderabad", "country": "India", "region_code": "India", "lat": 17.3850, "lng": 78.4867},
    {"name": "Gujarat API Hub (Ahmedabad)", "city": "Ahmedabad", "country": "India", "region_code": "India", "lat": 23.0225, "lng": 72.5714},
    {"name": "Visakhapatnam Pharma Park", "city": "Visakhapatnam", "country": "India", "region_code": "India", "lat": 17.7392, "lng": 83.2247},
    {"name": "Chennai Pharma Cluster", "city": "Chennai", "country": "India", "region_code": "India", "lat": 13.0827, "lng": 80.2707},
    {"name": "Mumbai API & Formulation Hub", "city": "Mumbai", "country": "India", "region_code": "India", "lat": 19.0760, "lng": 72.8777},
    {"name": "Pune Pharma SEZ", "city": "Pune", "country": "India", "region_code": "India", "lat": 18.5204, "lng": 73.8567},
    {"name": "Vadodara Bulk Drug Zone", "city": "Vadodara", "country": "India", "region_code": "India", "lat": 22.3072, "lng": 73.1812},
    {"name": "Dahej Industrial Cluster", "city": "Dahej", "country": "India", "region_code": "India", "lat": 21.7041, "lng": 72.5714},
    {"name": "Baddi Pharma Hub (Himachal Pradesh)", "city": "Baddi", "country": "India", "region_code": "India", "lat": 30.9463, "lng": 76.7794},
]


class DemographicAgent(BaseAgent):
    """
    Estimates disease burden and access fit in key markets.
    Recommends plant site locations (India only) via Gemini/Groq when available;
    fallback to deterministic India list otherwise.
    """

    def __init__(self, name: str | None = None, gemini_service: Optional["GeminiService"] = None) -> None:
        super().__init__(name=name)
        self.gemini_service = gemini_service

    def _score_site(
        self,
        site: Dict[str, Any],
        request: AnalysisRequest,
        seed: int,
        index: int,
        regions_override: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compute energy, land, market proximity, and export/supply scores for a site."""
        is_complex = request.complexity == "high"
        regions = regions_override if regions_override is not None else (request.regions or [])
        region_codes = [r.upper() if isinstance(r, str) else str(r) for r in regions]

        # Energy ease: India/Singapore often have incentives; US/EU reliable grid
        energy_base = {"India": 0.82, "USA": 0.88, "Ireland": 0.90, "Germany": 0.92, "Singapore": 0.95, "China": 0.78}
        energy_ease = energy_base.get(site["country"], 0.80) + (seed % 5) / 100
        energy_ease = self._clamp_score(energy_ease)

        # Land availability: India, China, Ireland typically higher
        land_base = {"India": 0.88, "China": 0.85, "Ireland": 0.82, "USA": 0.70, "Singapore": 0.65, "Germany": 0.68}
        land_availability = land_base.get(site["country"], 0.75) + ((seed + index) % 6) / 100
        land_availability = self._clamp_score(land_availability)

        # Market proximity: near US/EU5/India/China = great for supply and export
        market_base = {"USA": 0.95, "Germany": 0.92, "Ireland": 0.90, "India": 0.85, "China": 0.88, "Singapore": 0.87}
        market_proximity = market_base.get(site["country"], 0.80) + ((seed + index * 2) % 5) / 100
        market_proximity = self._clamp_score(market_proximity)

        # Export & supply ease: logistics, regulatory, ports
        export_base = {"Singapore": 0.95, "Ireland": 0.92, "USA": 0.88, "India": 0.85, "China": 0.82, "Germany": 0.90}
        export_supply = export_base.get(site["country"], 0.80) + ((seed + index * 3) % 4) / 100
        export_supply = self._clamp_score(export_supply)

        # Bonus if site region matches request regions
        if region_codes and site.get("region_code", "").upper() in [r.upper() for r in region_codes]:
            energy_ease = min(1.0, energy_ease + 0.03)
            market_proximity = min(1.0, market_proximity + 0.05)

        overall_site = (
            energy_ease * 0.25
            + land_availability * 0.25
            + market_proximity * 0.30
            + export_supply * 0.20
        )
        overall_site = self._clamp_score(overall_site)

        return {
            "name": site["name"],
            "city": site.get("city", site["name"]),
            "country": site["country"],
            "lat": site["lat"],
            "lng": site["lng"],
            "region_code": site.get("region_code", ""),
            "energy_ease_score": energy_ease,
            "land_availability_score": land_availability,
            "market_proximity_score": market_proximity,
            "export_supply_score": export_supply,
            "overall_site_score": overall_site,
            "rationale": {
                "energy": "Reliable power and pharma-grade utilities; incentives available." if energy_ease > 0.8 else "Adequate energy; consider backup and green options.",
                "land": "Good availability of developable land and industrial zones." if land_availability > 0.75 else "Moderate land availability; early engagement with authorities recommended.",
                "market": "Close to major drug markets for quick supply and export." if market_proximity > 0.85 else "Reasonable access to key markets; logistics to be optimized.",
                "export_supply": "Strong logistics and regulatory pathway for export and supply." if export_supply > 0.85 else "Viable export/supply chain; partner with local distributors.",
            },
        }

    async def run(self, request: AnalysisRequest):
        molecule = request.molecule_name or "Unknown"
        indication = request.target_indication
        complexity = request.complexity
        parsed = getattr(request, "parsed_intelligence", None) or {}
        # Prefer key_regions from IQVIA (parsed) when available for consistency across agents
        regions = parsed.get("key_regions") or request.regions or []
        symptoms = request.symptoms or []

        seed = int(hashlib.sha256(molecule.encode("utf-8")).hexdigest(), 16) % 100
        is_complex = complexity == "high"

        # --- Existing demographic scores (disease burden, age, affordability) ---
        base_disease_burden = 0.80 if is_complex else 0.85
        disease_burden = base_disease_burden + ((seed % 15) / 100)
        disease_burden = self._clamp_score(disease_burden)

        base_age_fit = 0.75 if is_complex else 0.82
        age_fit = base_age_fit + ((seed % 20) / 100)
        age_fit = self._clamp_score(age_fit)

        base_affordability = 0.70 if is_complex else 0.78
        affordability = base_affordability + ((seed % 18) / 100)
        affordability = self._clamp_score(affordability)

        overall = (
            disease_burden * 0.4 + age_fit * 0.3 + affordability * 0.3
        )
        overall = self._clamp_score(self._apply_complexity(overall, complexity))

        # --- Plant site recommendations: use Gemini/Groq (India only); fallback to deterministic list ---
        plant_site_recommendations: List[Dict[str, Any]] = []
        if self.gemini_service:
            fallback_list = getattr(request, "llm_fallback_used", None)
            llm_sites = self.gemini_service.get_plant_site_recommendations(
                molecule_name=molecule,
                indication=indication,
                fallback_used_list=fallback_list,
            )
            if llm_sites:
                plant_site_recommendations = llm_sites
        if not plant_site_recommendations:
            ordered = list(PLANT_SITE_CANDIDATES)
            for i in range(len(ordered) - 1):
                j = (seed + i * 7) % len(ordered)
                ordered[i], ordered[j] = ordered[j], ordered[i]
            ordered = ordered[:5]
            for i, site in enumerate(ordered):
                scored = self._score_site(site, request, seed, i, regions_override=regions)
                plant_site_recommendations.append(scored)

        # Ensure at least one Himachal Pradesh (Baddi) location – leading pharma hub
        has_himachal = any(
            "baddi" in (s.get("city") or "").lower() or "himachal" in (s.get("name") or "").lower()
            for s in plant_site_recommendations
        )
        if not has_himachal:
            himachal_scored = self._score_site(
                HIMACHAL_SITE, request, seed, len(plant_site_recommendations), regions_override=regions
            )
            plant_site_recommendations.append(himachal_scored)
        plant_site_recommendations.sort(key=lambda x: x["overall_site_score"], reverse=True)

        data: Dict[str, Any] = {
            "disease_burden_score": disease_burden,
            "age_distribution_fit_score": age_fit,
            "access_affordability_score": affordability,
            "demographic_overall_score": overall,
            "plant_site_recommendations": plant_site_recommendations,
            "technical_details": {
                "methodology": "Plant sites ranked by energy ease, land availability, market proximity, and export/supply logistics. Coordinates are representative of pharma hubs.",
                "criteria": "Energy ease = utilities & incentives; Land = availability; Market proximity = access to major drug markets; Export/supply = logistics and regulatory ease.",
            },
        }

        burden_desc = "very high" if disease_burden > 0.9 else "high" if disease_burden > 0.85 else "moderate"
        age_desc = "excellent" if age_fit > 0.85 else "good" if age_fit > 0.75 else "moderate"
        affordability_desc = "strong" if affordability > 0.8 else "moderate" if affordability > 0.7 else "limited"
        region_str = ", ".join(regions) if regions else "emerging and developed markets"
        indication_str = f" for {indication}" if indication else ""
        symptoms_str = f" (symptoms: {', '.join(symptoms)})" if symptoms else ""
        top_site = plant_site_recommendations[0] if plant_site_recommendations else {}
        top_name = top_site.get("name", "N/A")

        summary = (
            f"Demographic analysis for {molecule}{indication_str}{symptoms_str} indicates a {burden_desc} disease burden "
            f"with {age_desc} alignment to target age groups and {affordability_desc} affordability potential "
            f"in {region_str}. Recommended plant location: **{top_name}** (energy, land, and market proximity considered) "
            f"for ease of export and supply to key markets. See map for full site rankings."
        )

        return self._result(summary=summary, raw_data=data)
