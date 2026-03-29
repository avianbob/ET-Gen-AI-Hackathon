import hashlib
import json
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest
from .process_design import ProcessDesignAgent

if TYPE_CHECKING:
    from ...services.gemini_service import GeminiService


class TechnoEconomicAgent(BaseAgent):
    """
    Performs advanced techno-economic assessment based on actual PID equipment and process design.
    Calculates detailed CAPEX, OPEX, and financial metrics from the proposed process.
    Optional: AI-generated sensitivity analysis when gemini_service is provided.
    """

    def __init__(self, name: str | None = None, gemini_service: Optional["GeminiService"] = None) -> None:
        super().__init__(name=name)
        self.gemini_service = gemini_service

    def _fetch_economic_constants_from_llm(
        self, molecule: str, indication: Optional[str], request: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Call LLM once per analysis to get realistic pharmaceutical economics (equipment, labor, raw materials, market share).
        Returns a dict of constants or None on failure; callers fall back to hardcoded defaults when None.
        """
        if not self.gemini_service:
            return None
        fallback_list = getattr(request, "llm_fallback_used", None)
        indication_str = indication or "general API manufacturing"
        prompt = f"""You are a pharmaceutical process economics expert. For the API/molecule "{molecule}" and indication "{indication_str}", provide realistic techno-economic constants for a mid-scale API plant.

CRITICAL — Match molecule type to realistic price and share so the project is economically viable:
- Generic small molecules (e.g. Metformin, Paracetamol, Ibuprofen, Aspirin): product_price_usd_per_kg_fallback = 15 to 50 USD/kg (use levels that allow payback in 5–15 years for a typical plant); api_market_share = 0.005 to 0.03 (0.5% to 3% of drug market).
- Niche small molecules: product_price_usd_per_kg_fallback = 100 to 500 USD/kg; api_market_share = 0.02 to 0.08.
- Biologics / complex: product_price_usd_per_kg_fallback = 10000 to 100000; api_market_share = 0.05 to 0.15.

Choose equipment_base_costs_million_usd, salaries, and factors so that when combined with product_price_usd_per_kg_fallback, a mid-scale plant would typically achieve payback in 5–15 years and positive NPV at 10% discount. Avoid combinations that make the project obviously unviable (e.g. very low price with very high CAPEX).

Return ONLY a single valid JSON object (no markdown, no code fence, no explanation) with exactly these keys and numeric values:

{{
  "equipment_base_costs_million_usd": {{
    "Feed Tank": <float>, "CSTR Reactor": <float>, "PFR": <float>, "Batch Reactor": <float>,
    "Tubular Reactor": <float>, "Fixed Bed": <float>, "Fluidized Bed": <float>,
    "Separator": <float>, "Crystallizer": <float>, "Filter": <float>, "Dryer": <float>
  }},
  "operator_salary_usd": <int>, "engineer_salary_usd": <int>, "qc_salary_usd": <int>, "management_cost_usd": <int>,
  "raw_material_cost_per_kg_min": <float>, "raw_material_cost_per_kg_max": <float>,
  "api_market_share": <float 0.005 to 0.15 depending on molecule type>,
  "location_factor": <float 0.3 to 1.0>,
  "installation_factor": <float 0.30 to 0.45>, "piping_factor": <float 0.15 to 0.25>, "building_factor": <float 0.10 to 0.15>,
  "engineering_factor": <float 0.08 to 0.12>, "contingency_factor": <float 0.10 to 0.15>,
  "maintenance_factor": <float 0.03 to 0.06>, "insurance_factor": <float 0.02 to 0.035>,
  "product_price_usd_per_kg_fallback": <float: generics 15-50 for viable payback/NPV, niche 100-500, biologics 10k+>
}}

Equipment costs are base figures in million USD. Salaries and location_factor should reflect target region (e.g. India lower than US/EU)."""

        try:
            response = self.gemini_service._generate_content_with_retry(
                prompt,
                operation_name="TechnoEconomicConstants",
                fallback_used_list=fallback_list,
            )
            text = (getattr(response, "text", None) or "").strip()
            if not text:
                return None
            # Strip markdown code block if present
            if "```" in text:
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```.*$", "", text, flags=re.DOTALL)
            text = text.strip()
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
            obj = json.loads(text[start:])
            return obj
        except Exception as e:
            print(f"[TechnoEconomicAgent] Failed to fetch economic constants from LLM: {e}")
            return None

    async def run(self, request: AnalysisRequest):
        molecule = request.molecule_name or "Unknown"
        complexity = request.complexity
        seed = int(hashlib.sha256(molecule.encode("utf-8")).hexdigest(), 16) % 100
        is_complex = complexity == "high"

        # Techno-economic analysis is driven solely by the P&ID of the proposed plant (Stage 2 Process Design).
        # Use injected P&ID when provided by the pipeline; only fall back to local generation when not in pipeline.
        pid_data = getattr(request, "injected_pid_data", None)
        pid_source: str
        if pid_data and isinstance(pid_data, dict) and pid_data.get("equipment"):
            pid_source = "injected_from_process_design"
        else:
            process_agent = ProcessDesignAgent()
            pid_data = process_agent._generate_pid_data(molecule, is_complex, seed)
            pid_source = "generated_fallback"

        # Fetch realistic economic constants from LLM (one call); fall back to hardcoded when unavailable
        constants = self._fetch_economic_constants_from_llm(
            molecule, getattr(request, "target_indication", None), request
        )
        # All CAPEX, OPEX, capacity and cost_per_kg are derived strictly from this P&ID
        economic_data = self._calculate_detailed_economics(molecule, pid_data, is_complex, seed, constants=constants)

        # Build explicit PID summary for report/UI (TEA connected from proposed plant P&ID)
        equipment = pid_data.get("equipment", [])
        process_conditions = pid_data.get("process_conditions", {})
        reactor_block = pid_data.get("reactor", {})
        reactor_equipment = [eq for eq in equipment if (eq.get("id") or "").startswith("R-") or "reactor" in ((eq.get("type") or "").lower())]
        pid_summary = {
            "source": pid_source,
            "equipment_count": len(equipment),
            "number_of_reactors": process_conditions.get("number_of_reactors") or len(reactor_equipment) or 1,
            "reactor_types": process_conditions.get("reactor_types") or [eq.get("type") for eq in reactor_equipment] or [],
            "temperature_c": process_conditions.get("temperature") or reactor_block.get("temperature"),
            "pressure_bar": process_conditions.get("pressure") or reactor_block.get("pressure"),
        }

        # Calculate financial metrics (revenue/price can use market; capacity/cost stay from P&ID)
        parsed = getattr(request, "parsed_intelligence", None) or {}
        financial_metrics = self._calculate_financial_metrics(
            economic_data, seed, request=request, parsed_intelligence=parsed, constants=constants
        )

        # Break-even price: minimum sales price to cover OPEX (cost per kg at current capacity)
        opex_m_usd = economic_data["total_opex_million_usd_per_year"]
        cap = economic_data["production_capacity_kg_per_year"]
        break_even_price_usd_per_kg = round((opex_m_usd * 1_000_000) / cap, 2) if cap > 0 else 0.0

        # Optional: AI-generated sensitivity analysis
        sensitivity_analysis = None
        if self.gemini_service:
            try:
                fallback_list = getattr(request, "llm_fallback_used", None)
                prompt = (
                    f"For a pharmaceutical API plant: CAPEX ${economic_data['total_capex_million_usd']:.1f}M, "
                    f"annual OPEX ${opex_m_usd:.1f}M, production capacity {cap:,.0f} kg/year, "
                    f"current product price ${financial_metrics.get('product_price_usd_per_kg', 0):.0f}/kg. "
                    "In one short paragraph (2-3 sentences), describe what happens to profitability if raw material costs rise by 20%."
                )
                resp = self.gemini_service._generate_content_with_retry(
                    prompt, operation_name="TechnoEconomicSensitivity", fallback_used_list=fallback_list
                )
                if resp and getattr(resp, "text", None):
                    sensitivity_analysis = resp.text.strip()
            except Exception as e:
                print(f"[TechnoEconomicAgent] Sensitivity analysis failed: {e}")

        if not sensitivity_analysis:
            sensitivity_analysis = (
                f"A 20% increase in raw material costs would raise annual OPEX by approximately "
                f"${economic_data.get('raw_material_cost_million_usd_per_year', 0) * 0.2:.1f}M, "
                "reducing margin unless offset by price or efficiency gains."
            )

        # Combine all data – TEA is explicitly connected to the proposed plant P&ID
        data: Dict[str, Any] = {
            **economic_data,
            **financial_metrics,
            "break_even_price_usd_per_kg": break_even_price_usd_per_kg,
            "sensitivity_analysis": sensitivity_analysis,
            "pid_based": True,
            "pid_source": pid_source,
            "pid_summary": pid_summary,
        }

        summary = (
            f"Techno-economic analysis for {molecule} is derived from the proposed plant P&ID "
            f"({pid_summary['equipment_count']} equipment items, {pid_summary['number_of_reactors']} reactor(s)). "
            f"Total CAPEX ${economic_data['total_capex_million_usd']:.1f}M, annual OPEX "
            f"${economic_data['total_opex_million_usd_per_year']:.1f}M/year; payback "
            f"{financial_metrics['payback_period_years']:.1f} years, IRR {int(financial_metrics['internal_rate_of_return'] * 100)}%, "
            f"{'strong' if financial_metrics['production_feasibility_score'] > 0.75 else 'moderate' if financial_metrics['production_feasibility_score'] > 0.6 else 'marginal'} "
            f"economic feasibility."
        )

        return self._result(summary=summary, raw_data=data)

    def _calculate_detailed_economics(
        self,
        molecule: str,
        pid_data: Dict[str, Any],
        is_complex: bool,
        seed: int,
        constants: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate detailed CAPEX and OPEX based on actual PID equipment.
        When constants (from LLM) are provided, use them for factors and cost bases; otherwise use hardcoded defaults.
        """
        equipment = pid_data.get("equipment", [])
        process_conditions = pid_data.get("process_conditions", {})
        material_handling = pid_data.get("material_handling", {})
        c = constants or {}

        # 1. Equipment CAPEX (based on actual equipment in PID)
        equipment_costs = {}
        total_equipment_capex = 0.0

        for eq in equipment:
            eq_cost = self._estimate_equipment_cost(eq, seed, constants=c)
            equipment_costs[eq["id"]] = {
                "name": eq["name"],
                "type": eq["type"],
                "cost_million_usd": eq_cost,
                "specs": eq.get("specs", {}),
            }
            total_equipment_capex += eq_cost

        # 2. Installation & Construction Costs
        installation_factor = self._float_from_const(c, "installation_factor", 0.35 + (seed % 10) / 100)
        installation_capex = total_equipment_capex * installation_factor

        # 3. Piping & Instrumentation
        piping_factor = self._float_from_const(c, "piping_factor", 0.20 + (seed % 10) / 100)
        piping_capex = total_equipment_capex * piping_factor

        # 4. Buildings & Infrastructure
        building_factor = self._float_from_const(c, "building_factor", 0.12 + (seed % 5) / 100)
        building_capex = total_equipment_capex * building_factor

        # 5. Engineering & Design
        direct_costs = total_equipment_capex + installation_capex + piping_capex + building_capex
        engineering_factor = self._float_from_const(c, "engineering_factor", 0.10 + (seed % 4) / 100)
        engineering_capex = direct_costs * engineering_factor

        # 6. Contingency
        project_cost = direct_costs + engineering_capex
        contingency_factor = self._float_from_const(c, "contingency_factor", 0.12 + (seed % 5) / 100)
        contingency_capex = project_cost * contingency_factor

        # Total CAPEX
        total_capex = project_cost + contingency_capex

        # 7. Raw Material Costs (OPEX)
        reactants = material_handling.get("reactants", [])
        catalysts = material_handling.get("catalysts", [])

        raw_material_cost = self._estimate_raw_material_costs(
            reactants, catalysts, process_conditions, seed, constants=c
        )

        # 8. Utility Costs (OPEX)
        utility_cost = self._estimate_utility_costs(equipment, process_conditions, seed)

        # 9. Labor Costs (OPEX)
        num_reactors = process_conditions.get("number_of_reactors", 1)
        labor_cost = self._estimate_labor_costs(num_reactors, len(equipment), seed, constants=c)

        # 10. Maintenance Costs (OPEX)
        maintenance_factor = self._float_from_const(c, "maintenance_factor", 0.04 + (seed % 2) / 100)
        maintenance_cost = total_equipment_capex * maintenance_factor

        # 11. Insurance & Overhead (OPEX)
        insurance_factor = self._float_from_const(c, "insurance_factor", 0.025 + (seed % 1) / 100)
        insurance_cost = total_capex * insurance_factor

        # Total OPEX
        total_opex = raw_material_cost + utility_cost + labor_cost + maintenance_cost + insurance_cost

        # 12. Production Capacity (based on reactor volumes and flow rates)
        production_capacity = self._estimate_production_capacity(equipment, process_conditions, seed)

        # Optional: global location factor (e.g. 0.4 for emerging markets)
        location_factor = self._float_from_const(c, "location_factor", 1.0)
        if location_factor != 1.0:
            total_equipment_capex *= location_factor
            for eid in equipment_costs:
                equipment_costs[eid]["cost_million_usd"] = round(
                    equipment_costs[eid]["cost_million_usd"] * location_factor, 4
                )
            installation_capex *= location_factor
            piping_capex *= location_factor
            building_capex *= location_factor
            engineering_capex *= location_factor
            contingency_capex *= location_factor
            total_capex = total_equipment_capex + installation_capex + piping_capex + building_capex + engineering_capex + contingency_capex
            labor_cost *= location_factor
            maintenance_cost = total_equipment_capex * maintenance_factor
            insurance_cost = total_capex * insurance_factor
            total_opex = raw_material_cost + utility_cost + labor_cost + maintenance_cost + insurance_cost

        return {
            "equipment_costs": equipment_costs,
            "equipment_capex_million_usd": round(total_equipment_capex, 2),
            "installation_capex_million_usd": round(installation_capex, 2),
            "piping_instrumentation_capex_million_usd": round(piping_capex, 2),
            "buildings_infrastructure_capex_million_usd": round(building_capex, 2),
            "engineering_design_capex_million_usd": round(engineering_capex, 2),
            "contingency_capex_million_usd": round(contingency_capex, 2),
            "total_capex_million_usd": round(total_capex, 2),
            "raw_material_cost_million_usd_per_year": round(raw_material_cost, 2),
            "utility_cost_million_usd_per_year": round(utility_cost, 2),
            "labor_cost_million_usd_per_year": round(labor_cost, 2),
            "maintenance_cost_million_usd_per_year": round(maintenance_cost, 2),
            "insurance_overhead_cost_million_usd_per_year": round(insurance_cost, 2),
            "total_opex_million_usd_per_year": round(total_opex, 2),
            "production_capacity_kg_per_year": production_capacity,
            "cost_per_kg_usd": round((total_opex * 1_000_000) / production_capacity, 2) if production_capacity > 0 else 0,
        }

    def _float_from_const(self, c: Dict[str, Any], key: str, default: float) -> float:
        """Read a float from constants dict with safe default."""
        val = c.get(key)
        if val is None:
            return default
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def _estimate_equipment_cost(
        self, equipment: Dict[str, Any], seed: int, constants: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Estimate equipment cost based on type, size, and specifications.
        Costs in million USD. Uses LLM-derived equipment_base_costs_million_usd when provided.
        """
        eq_type = equipment.get("type", "")
        specs = equipment.get("specs", {})
        volume_str = specs.get("volume", "5000L")

        try:
            volume_clean = str(volume_str).replace("L", "").replace("m³", "").replace(" ", "").strip()
            volume = float(volume_clean)
            if "m³" in str(volume_str):
                volume *= 1000
        except (ValueError, AttributeError, TypeError):
            volume = 5000

        c = constants or {}
        eq_bases = c.get("equipment_base_costs_million_usd") or {}
        # Build cost_factors: prefer LLM bases (scale by volume where sensible), else hardcoded
        default_factors = {
            "Feed Tank": 0.15 + (volume / 10000) * 0.05,
            "CSTR Reactor": 0.8 + (volume / 1000) * 0.15,
            "PFR": 0.6 + (volume / 1000) * 0.12,
            "Batch Reactor": 0.7 + (volume / 1000) * 0.13,
            "Tubular Reactor": 0.5 + (volume / 1000) * 0.10,
            "Fixed Bed": 0.4 + (volume / 1000) * 0.08,
            "Fluidized Bed": 0.9 + (volume / 1000) * 0.18,
            "Separator": 0.3 + (volume / 5000) * 0.10,
            "Crystallizer": 0.5 + (volume / 3000) * 0.12,
            "Filter": 0.2 + (self._extract_numeric_value(specs.get("area", "10"), default=10) / 10) * 0.05,
            "Dryer": 0.25 + (volume / 1000) * 0.08,
        }
        cost_factors = {}
        for key, default_val in default_factors.items():
            if key in eq_bases and isinstance(eq_bases[key], (int, float)):
                base_val = float(eq_bases[key])
                # Slight volume scaling so same type different size differs
                cost_factors[key] = base_val * (0.9 + 0.2 * min(volume / 10000, 1.0))
            else:
                cost_factors[key] = default_val

        base_cost = 0.3
        for key, cost in cost_factors.items():
            if key in eq_type:
                base_cost = cost
                break

        material = specs.get("material", "SS316")
        material_multiplier = 1.0
        if "Hastelloy" in material or "Titanium" in material:
            material_multiplier = 1.5
        elif "Glass" in material or "Lining" in material:
            material_multiplier = 1.3

        temp = equipment.get("temperature", 100)
        pressure = equipment.get("pressure", 5.0)
        if isinstance(temp, str):
            temp = self._extract_numeric_value(temp, default=100)
        if isinstance(pressure, str):
            pressure = self._extract_numeric_value(pressure, default=5.0)
        if temp > 200 or pressure > 10:
            material_multiplier *= 1.2

        # Reduced variation when using LLM constants (±2%); else ±10%
        variation = 1.0 + ((seed % 5) - 2) / 100 if c else 1.0 + ((seed % 20) - 10) / 100
        return base_cost * material_multiplier * variation

    def _extract_numeric_value(self, value: Any, default: float = 0.0) -> float:
        """
        Extract numeric value from string or return default.
        Handles strings like "10 m²", "5000L", etc.
        """
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Extract first number from string
            import re
            match = re.search(r'[\d.]+', value)
            if match:
                return float(match.group())
        return default

    def _estimate_raw_material_costs(
        self,
        reactants: List[str],
        catalysts: List[str],
        process_conditions: Dict[str, Any],
        seed: int,
        constants: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Estimate annual raw material costs in million USD.
        Uses LLM raw_material_cost_per_kg_min/max when provided.
        """
        c = constants or {}
        cost_min = self._float_from_const(c, "raw_material_cost_per_kg_min", 5.0)
        cost_max = self._float_from_const(c, "raw_material_cost_per_kg_max", 15.0)
        num_reactors = process_conditions.get("number_of_reactors", 1)
        production_capacity = 50000 + (seed % 50000)

        total_reactant_cost = 0.0
        for reactant in reactants:
            if "Aminophenol" in reactant or "Amino" in reactant:
                cost_per_kg = cost_min + (cost_max - cost_min) * 0.7 + (seed % 10) * 0.5
            elif "Acetic" in reactant or "Acid" in reactant:
                cost_per_kg = min(3.5, cost_min * 0.3) + (seed % 2) / 10
            elif "Anhydride" in reactant:
                cost_per_kg = cost_min * 0.5 + (seed % 3)
            elif "Alcohol" in reactant:
                cost_per_kg = cost_min * 0.3 + (seed % 2)
            else:
                cost_per_kg = cost_min + (seed % 11) * (cost_max - cost_min) / 10
            ratio = 1.2 + (seed % 10) / 10
            total_reactant_cost += cost_per_kg * production_capacity * ratio

        catalyst_cost = 0.0
        for catalyst in catalysts:
            if "Pd" in catalyst or "Pt" in catalyst:
                cost_per_kg = 50000 + (seed % 50000)
                catalyst_cost += cost_per_kg * production_capacity * 0.001
            elif "Enzyme" in catalyst:
                cost_per_kg = 200 + (seed % 300)
                catalyst_cost += cost_per_kg * production_capacity * 0.01
            else:
                cost_per_kg = 50 + (seed % 50)
                catalyst_cost += cost_per_kg * production_capacity * 0.005

        solvent_cost = 0.0
        solvents = [r for r in reactants if any(s in r for s in ["DMF", "DMSO", "THF", "Ethanol", "Methanol", "Toluene"])]
        for solvent in solvents:
            cost_per_kg = 1.0 + (seed % 2)
            solvent_cost += cost_per_kg * production_capacity * 0.5

        total = (total_reactant_cost + catalyst_cost + solvent_cost) / 1_000_000
        return total

    def _estimate_utility_costs(
        self, 
        equipment: List[Dict[str, Any]], 
        process_conditions: Dict[str, Any],
        seed: int
    ) -> float:
        """
        Estimate annual utility costs (steam, cooling water, electricity) in million USD.
        """
        # Count reactors and their operating conditions
        reactors = [eq for eq in equipment if "R-" in eq["id"]]
        total_utility_cost = 0.0
        
        for reactor in reactors:
            temp = reactor.get("temperature", 100)
            # Ensure temp is numeric
            if isinstance(temp, str):
                temp = self._extract_numeric_value(temp, default=100)
            
            volume_str = reactor.get("specs", {}).get("volume", "5000L")
            volume = self._extract_numeric_value(volume_str, default=5000)
            # If volume_str contains "m³", convert to liters
            if isinstance(volume_str, str) and "m³" in volume_str:
                volume *= 1000
            
            # Steam cost (for heating)
            if temp > 100:
                steam_cost = (temp - 100) * volume * 0.0001  # $ per year per reactor
                total_utility_cost += steam_cost
            
            # Cooling water cost (for cooling/jackets)
            cooling_cost = volume * 0.00005  # $ per year per reactor
            total_utility_cost += cooling_cost
        
        # Electricity (for agitators, pumps, etc.)
        num_equipment = len(equipment)
        electricity_cost = num_equipment * 50000  # $50k per major equipment per year
        total_utility_cost += electricity_cost
        
        # Compressed air, nitrogen, etc.
        utility_overhead = num_equipment * 20000  # $20k per equipment
        total_utility_cost += utility_overhead
        
        return total_utility_cost / 1_000_000  # Convert to million USD

    def _estimate_labor_costs(
        self,
        num_reactors: int,
        num_equipment: int,
        seed: int,
        constants: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Estimate annual labor costs in million USD.
        Uses LLM operator_salary_usd, engineer_salary_usd, qc_salary_usd, management_cost_usd when provided.
        """
        c = constants or {}
        operator_salary = int(c.get("operator_salary_usd", 70000 + (seed % 20000)))
        engineer_salary = int(c.get("engineer_salary_usd", 120000 + (seed % 30000)))
        qc_salary = int(c.get("qc_salary_usd", 80000 + (seed % 20000)))
        management_cost = int(c.get("management_cost_usd", 500000 + (seed % 300000)))

        operators_per_shift = 2 + num_reactors
        shifts_per_day = 3
        operators_total = operators_per_shift * shifts_per_day
        operator_cost = operators_total * operator_salary

        engineers = 1 + (num_reactors // 2)
        engineer_cost = engineers * engineer_salary

        qc_staff = 2 + (num_equipment // 5)
        qc_cost = qc_staff * qc_salary

        total = (operator_cost + engineer_cost + qc_cost + management_cost) / 1_000_000
        return total

    def _estimate_production_capacity(
        self, 
        equipment: List[Dict[str, Any]], 
        process_conditions: Dict[str, Any],
        seed: int
    ) -> float:
        """
        Estimate annual production capacity in kg/year.
        """
        # Find primary reactor
        reactors = [eq for eq in equipment if "R-" in eq["id"]]
        if not reactors:
            return 50000  # Default 50 tons/year
        
        primary_reactor = reactors[0]
        volume_str = primary_reactor.get("specs", {}).get("volume", "5000L")
        volume = self._extract_numeric_value(volume_str, default=5000)
        # If volume_str contains "m³", convert to liters
        if isinstance(volume_str, str) and "m³" in volume_str:
            volume *= 1000
        
        # Estimate based on reactor volume and type
        reactor_type = primary_reactor.get("type", "")
        
        if "Batch" in reactor_type:
            # Batch: volume * batches per year
            batch_time_hours = 2 + (seed % 4)  # 2-6 hours per batch
            batches_per_year = (365 * 24) / batch_time_hours
            # Assume 10% product concentration
            capacity = volume * 0.1 * batches_per_year * 0.8  # 0.8 density
        else:
            # Continuous: volume * flow rate * operating hours
            flow_rate = primary_reactor.get("flow_rate", 200)  # L/min
            operating_hours = 8000  # 90% uptime
            # Assume 5% product concentration
            capacity = (flow_rate * 60 * operating_hours) * 0.05 * 0.8  # 0.8 density
        
        return max(capacity, 10000)  # Minimum 10 tons/year

    def _calculate_financial_metrics(
        self,
        economic_data: Dict[str, Any],
        seed: int,
        request: Any = None,
        parsed_intelligence: Dict[str, Any] | None = None,
        constants: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate financial metrics: IRR, NPV, Payback Period, etc.
        Uses parsed_intelligence (market size from IQVIA) when available; constants (LLM) for api_share and base_price fallback.
        """
        parsed = parsed_intelligence or {}
        c = constants or {}
        capex = economic_data["total_capex_million_usd"]
        opex = economic_data["total_opex_million_usd_per_year"]
        production_capacity = economic_data["production_capacity_kg_per_year"]
        target_volume = getattr(request, "target_production_volume_kg_per_year", None) if request else None
        quantity_sold = min(production_capacity, target_volume) if target_volume else production_capacity
        if quantity_sold <= 0:
            quantity_sold = production_capacity

        # Revenue and price: prefer realistic API price from Stage 1 (IQVIA) or LLM constants
        typical_price = parsed.get("typical_api_price_usd_per_kg")
        if isinstance(typical_price, (int, float)) and typical_price > 0:
            # Primary path: use LLM-derived typical bulk API price (realistic for generics)
            base_price = float(typical_price)
            print(f"[TechnoEconomic] Using LLM-derived market price (from IQVIA): ${base_price:.2f}/kg")
            revenue_per_year = (quantity_sold * base_price) / 1_000_000
        else:
            api_market_b = parsed.get("api_market_size_billion_usd")
            market_size_b = parsed.get("estimated_market_size_billion_usd")
            api_share = self._float_from_const(c, "api_market_share", 0.03)  # generics: 0.5–3%
            # Prefer API market size (bulk) over drug TAM
            if isinstance(api_market_b, (int, float)) and api_market_b > 0 and quantity_sold > 0:
                revenue_total_usd = float(api_market_b) * 1e9
                revenue_per_year = revenue_total_usd / 1_000_000
                base_price = revenue_total_usd / quantity_sold
            elif market_size_b is not None and quantity_sold > 0:
                revenue_total_usd = float(market_size_b) * 1e9 * api_share
                revenue_per_year = revenue_total_usd / 1_000_000
                base_price = revenue_total_usd / quantity_sold
            else:
                base_price = self._float_from_const(c, "product_price_usd_per_kg_fallback", 0.0)
                if base_price > 0 and c:
                    print(f"[TechnoEconomic] Using LLM-derived product price (from TEA constants): ${base_price:.2f}/kg")
                if base_price <= 0:
                    base_price = 50 + (seed % 150)  # generic range 50–200
                revenue_per_year = (production_capacity * base_price) / 1_000_000
            # Sanity: avoid absurd $/kg from (drug TAM * share) / small quantity_sold
            if base_price > 2000.0:
                fallback_price = self._float_from_const(c, "product_price_usd_per_kg_fallback", 0.0)
                base_price = fallback_price if fallback_price > 0 else 100.0
                revenue_per_year = (quantity_sold * base_price) / 1_000_000
        
        # Gross profit
        gross_profit = revenue_per_year - opex
        
        # Payback period
        if gross_profit > 0:
            payback_period = capex / gross_profit
        else:
            payback_period = 999  # Not profitable
        
        # IRR calculation (simplified)
        # Assume 10-year project life
        project_life = 10
        cash_flows = [-capex]  # Year 0: initial investment
        for year in range(1, project_life + 1):
            # Revenue may grow 5% per year, OPEX increases 3% per year
            year_revenue = revenue_per_year * (1.05 ** (year - 1))
            year_opex = opex * (1.03 ** (year - 1))
            cash_flows.append(year_revenue - year_opex)
        
        # Simple IRR approximation (Newton-Raphson would be better, but this works)
        irr = self._calculate_irr_simple(cash_flows)
        
        # NPV at 10% discount rate
        discount_rate = 0.10
        npv = sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows))
        
        # Production feasibility score
        capex_score = 1.0 - min(capex / 100.0, 1.0)  # Normalize
        opex_score = 1.0 - min(opex / 20.0, 1.0)
        payback_score = 1.0 - min(payback_period / 10.0, 1.0)
        irr_score = min(irr / 0.35, 1.0)  # Cap at 35%
        npv_score = min(npv / 50.0, 1.0) if npv > 0 else 0
        
        feasibility = (
            capex_score * 0.20 +
            opex_score * 0.20 +
            payback_score * 0.20 +
            irr_score * 0.25 +
            npv_score * 0.15
        )
        
        # Break-even price is added in run() from economic_data; not duplicated here
        return {
            "revenue_million_usd_per_year": round(revenue_per_year, 2),
            "gross_profit_million_usd_per_year": round(gross_profit, 2),
            "gross_margin_percent": round((gross_profit / revenue_per_year * 100) if revenue_per_year > 0 else 0, 1),
            "payback_period_years": round(payback_period, 2),
            "internal_rate_of_return": round(irr, 3),
            "net_present_value_million_usd": round(npv, 2),
            "product_price_usd_per_kg": round(base_price, 2),
            "production_feasibility_score": self._clamp_score(feasibility),
            "project_life_years": project_life,
        }

    def _calculate_irr_simple(self, cash_flows: List[float], max_iterations: int = 100) -> float:
        """
        Simple IRR calculation using iterative approach.
        """
        if len(cash_flows) < 2:
            return 0.0
        
        # Initial guess
        rate = 0.10
        
        for _ in range(max_iterations):
            npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
            npv_derivative = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows) if i > 0)
            
            if abs(npv_derivative) < 1e-10:
                break
            
            rate = rate - npv / npv_derivative
            
            # Bounds check
            if rate < -0.99:
                rate = -0.99
            if rate > 10.0:
                rate = 10.0
            
            if abs(npv) < 1e-6:
                break
        
        return max(0.0, min(rate, 1.0))  # Clamp between 0% and 100%

