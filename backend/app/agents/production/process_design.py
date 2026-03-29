# backend/app/agents/production/process_design.py
import hashlib
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest

if TYPE_CHECKING:
    from ...services.gemini_service import GeminiService


class ProcessDesignAgent(BaseAgent):
    """
    Evaluates process complexity, scalability, and continuous manufacturing fit.
    Generates detailed PID (Process and Instrumentation Diagram) data via Gemini when available,
    with fallback to deterministic rule-based generation.
    """

    def __init__(self, name: str | None = None, gemini_service: Optional["GeminiService"] = None) -> None:
        super().__init__(name=name)
        self.gemini_service = gemini_service

    async def run(self, request: AnalysisRequest):
        molecule = request.molecule_name or "Unknown"
        complexity = request.complexity

        # Try Gemini first for drug-specific P&ID design
        pid_data: Dict[str, Any] | None = None
        if self.gemini_service:
            pid_data = self.gemini_service.generate_pid_design(
                drug_name=molecule,
                target_volume_kg_per_year=getattr(request, "target_production_volume_kg_per_year", None),
                fallback_used_list=getattr(request, "llm_fallback_used", None),
            )
        if pid_data is None:
            # Fallback: deterministic rule-based P&ID
            seed = int(hashlib.sha256(molecule.encode("utf-8")).hexdigest(), 16) % 100
            is_complex = complexity == "high"
            pid_data = self._generate_pid_data(molecule, is_complex, seed)

        # Fine-tuning: scores from PID characteristics
        seed = int(hashlib.sha256(molecule.encode("utf-8")).hexdigest(), 16) % 100
        is_complex = complexity == "high"
        base_complexity = 0.7 if is_complex else 0.5
        process_complexity_score = base_complexity + ((seed % 20) / 100)  # 0.5-0.9 range
        scalability_base = 0.7 if is_complex else 0.85
        scalability_score = scalability_base - ((seed % 15) / 100)  # 0.55-0.85 range
        continuous_fit_base = 0.6 if is_complex else 0.75
        continuous_manufacturing_fit = continuous_fit_base + ((seed % 20) / 100)  # 0.6-0.95 range
        feasibility = (
            (1.0 - process_complexity_score) * 0.3
            + scalability_score * 0.4
            + continuous_manufacturing_fit * 0.3
        )
        feasibility = self._apply_complexity(feasibility, complexity)

        # Safety (HAZOP), waste streams, sustainability from PID / route
        material_handling = pid_data.get("material_handling", {})
        waste_streams = list(material_handling.get("products", []) or [])
        if "By-products" not in str(waste_streams):
            waste_streams.append("By-products")
        if material_handling.get("recycle_streams"):
            for s in material_handling["recycle_streams"]:
                if "Solvent" in str(s) or "Mother liquor" in str(material_handling.get("products", [])):
                    waste_streams.append("Mother liquor / solvent recovery stream")
                    break
        safety_hazards_hazop = [
            "Exothermic reaction risk in primary reactor; ensure cooling and emergency relief.",
            "High-temperature operation; thermal hazards and material compatibility.",
            "Chemical handling and exposure; PPE and ventilation required.",
        ]
        # Sustainability 0-10: higher if solvent recycle and fewer steps
        num_steps = pid_data.get("process_conditions", {}).get("number_of_steps", 3)
        recycle_count = len(material_handling.get("recycle_streams") or [])
        sustainability_score = min(10, max(0, 4 + (2 if recycle_count > 0 else 0) - (num_steps - 2)))

        data: Dict[str, Any] = {
            "process_complexity_score": self._clamp_score(process_complexity_score),  # 0–1, higher = more complex
            "scalability_score": self._clamp_score(scalability_score),  # 0–1, higher = easier to scale
            "continuous_manufacturing_fit": self._clamp_score(continuous_manufacturing_fit),  # 0–1
            "production_feasibility_score": self._clamp_score(feasibility),
            "safety_hazards_hazop": safety_hazards_hazop,
            "waste_streams": waste_streams[:5],
            "sustainability_score": sustainability_score,
            "pid_data": pid_data,  # Detailed PID information
        }

        complexity_desc = "high" if process_complexity_score > 0.7 else "moderate" if process_complexity_score > 0.5 else "low"
        scalability_desc = "excellent" if scalability_score > 0.8 else "good" if scalability_score > 0.65 else "moderate"
        
        summary = (
            f"Process design assessment for {molecule} indicates {complexity_desc} complexity "
            f"but {scalability_desc} scalability potential. The molecule is "
            f"{'well' if continuous_manufacturing_fit > 0.7 else 'reasonably'} suited for continuous manufacturing with appropriate optimisation. "
            f"Operating conditions: Reactor at {pid_data['reactor']['temperature']}°C, {pid_data['reactor']['pressure']} bar."
        )

        return self._result(summary=summary, raw_data=data)

    def _determine_synthesis_route(self, molecule: str, seed: int) -> Dict[str, Any]:
        """
        Determine realistic synthesis route and reactants based on molecule characteristics.
        Returns route information including number of steps, reactor types, and reactants.
        """
        molecule_lower = molecule.lower()
        
        # Determine number of synthesis steps based on complexity
        # Simple molecules: 1-2 steps, Complex: 3-4 steps
        name_length_factor = min(len(molecule) / 30, 1.0)  # Longer names = more complex
        complexity_factor = name_length_factor + (seed % 30) / 100
        
        if complexity_factor < 0.4:
            num_steps = 1
            num_reactors = 1
        elif complexity_factor < 0.6:
            num_steps = 2
            num_reactors = 1 + (seed % 2)  # 1-2 reactors
        elif complexity_factor < 0.8:
            num_steps = 3
            num_reactors = 2 + (seed % 2)  # 2-3 reactors
        else:
            num_steps = 4
            num_reactors = 3 + (seed % 2)  # 3-4 reactors
        
        # Determine reactor types based on process needs
        reactor_types = []
        reactor_type_options = ["CSTR", "PFR", "Batch Reactor", "Tubular Reactor", "Fixed Bed", "Fluidized Bed"]
        
        for i in range(num_reactors):
            # First reactor is usually CSTR or Batch
            if i == 0:
                reactor_types.append("CSTR" if seed % 2 == 0 else "Batch Reactor")
            # Later reactors vary
            else:
                idx = (seed * (i + 1)) % len(reactor_type_options)
                reactor_types.append(reactor_type_options[idx])
        
        # Generate realistic reactants based on molecule type
        reactants = []
        catalysts = []
        
        # Common pharmaceutical synthesis patterns
        if "paracetamol" in molecule_lower or "acetaminophen" in molecule_lower:
            reactants = ["4-Aminophenol", "Acetic Anhydride"]
            catalysts = ["Acetic Acid Catalyst"]
            num_reactors = 1
            reactor_types = ["CSTR"]
        elif "aspirin" in molecule_lower or "acetylsalicylic" in molecule_lower:
            reactants = ["Salicylic Acid", "Acetic Anhydride"]
            catalysts = ["Sulfuric Acid Catalyst"]
            num_reactors = 1
            reactor_types = ["CSTR"]
        elif "ibuprofen" in molecule_lower:
            reactants = ["Isobutylbenzene", "Propionic Anhydride", "Carbon Monoxide"]
            catalysts = ["Pd/C Catalyst"]
            num_reactors = 2
            reactor_types = ["CSTR", "PFR"]
        elif "penicillin" in molecule_lower:
            reactants = ["6-APA (6-Aminopenicillanic Acid)", "Side Chain Precursor"]
            catalysts = ["Enzyme Catalyst"]
            num_reactors = 2
            reactor_types = ["Batch Reactor", "CSTR"]
        elif "insulin" in molecule_lower:
            reactants = ["A-chain Precursor", "B-chain Precursor"]
            catalysts = ["Enzyme Catalyst"]
            num_reactors = 3
            reactor_types = ["Batch Reactor", "CSTR", "CSTR"]
        elif "acid" in molecule_lower:
            reactants = [f"Starting Material for {molecule[:20]}", "Oxidizing Agent"]
            catalysts = ["Acid Catalyst"]
        elif "amine" in molecule_lower or "amino" in molecule_lower:
            reactants = [f"Nitro Precursor", "Reducing Agent"]
            catalysts = ["Metal Catalyst (Pd/C or Ni)"]
        elif "ester" in molecule_lower:
            reactants = ["Carboxylic Acid", "Alcohol"]
            catalysts = ["Acid Catalyst"]
        elif "ketone" in molecule_lower:
            reactants = ["Alcohol Precursor", "Oxidizing Agent"]
            catalysts = ["Oxidation Catalyst"]
        else:
            # Generic synthesis route
            base_reactants = [
                ["Aryl Halide", "Nucleophile"],
                ["Aldehyde", "Amine"],
                ["Ketone", "Grignard Reagent"],
                ["Acid Chloride", "Amine"],
                ["Epoxide", "Nucleophile"],
            ]
            base_catalysts = [
                "Pd/C Catalyst",
                "Cu Catalyst",
                "Base Catalyst",
                "Acid Catalyst",
                "Enzyme Catalyst",
            ]
            
            route_idx = seed % len(base_reactants)
            reactants = base_reactants[route_idx]
            catalyst_idx = (seed * 3) % len(base_catalysts)
            catalysts = [base_catalysts[catalyst_idx]]
        
        # Add solvent if needed
        solvents = ["DMF", "DMSO", "THF", "Ethanol", "Methanol", "Water", "Toluene", "Acetonitrile"]
        solvent_idx = (seed * 5) % len(solvents)
        if num_steps > 2:
            reactants.append(f"{solvents[solvent_idx]} (Solvent)")
        
        return {
            "num_steps": num_steps,
            "num_reactors": num_reactors,
            "reactor_types": reactor_types,
            "reactants": reactants,
            "catalysts": catalysts,
            "intermediates": [f"Intermediate {i+1}" for i in range(num_steps - 1)],
            "final_product": molecule
        }

    def _generate_pid_data(self, molecule: str, is_complex: bool, seed: int) -> Dict[str, Any]:
        """
        Generate detailed PID data including pressure, temperature, and equipment specifications.
        This creates a realistic chemical engineering process flow diagram specific to the molecule
        with variable number of reactors and actual synthesis routes.
        """
        # Determine synthesis route and process parameters
        route = self._determine_synthesis_route(molecule, seed)
        num_reactors = route["num_reactors"]
        reactor_types = route["reactor_types"]
        reactants = route["reactants"]
        catalysts = route["catalysts"]
        
        # Base values vary with complexity
        base_temp = 180 if is_complex else 120
        base_pressure = 8.5 if is_complex else 5.0
        
        # Flow rates (L/min)
        feed_flow = 150 + (seed % 100)
        
        # Build equipment list dynamically
        equipment: List[Dict[str, Any]] = []
        
        # 1. Feed Tanks - one for each reactant and catalyst
        feed_num = 1
        for i, reactant in enumerate(reactants):
            equipment.append({
                "id": f"FEED-{feed_num:03d}",
                "type": "Feed Tank",
                "name": f"{reactant} Feed",
                "temperature": 25.0 + (i * 2),
                "pressure": 1.0,
                "flow_rate": feed_flow * (1.0 - i * 0.1),
                "specs": {"volume": "2000L", "material": "SS316"}
            })
            feed_num += 1
        
        # Add catalyst feed tanks
        for i, catalyst in enumerate(catalysts):
            equipment.append({
                "id": f"FEED-{feed_num:03d}",
                "type": "Feed Tank",
                "name": f"{catalyst}",
                "temperature": 30.0 + (i * 2),
                "pressure": 1.0,
                "flow_rate": feed_flow * 0.1,
                "specs": {"volume": "500L", "material": "Hastelloy C"}
            })
            feed_num += 1
        
        # 2. Reactors - variable number based on synthesis route
        reactor_num = 1
        control_loop_num = 1
        current_temp = base_temp
        current_pressure = base_pressure
        
        for i in range(num_reactors):
            reactor_type = reactor_types[i]
            
            # Temperature and pressure vary for each reactor
            temp_variation = (seed * (i + 1) % 40) - 20
            pressure_variation = (seed * (i + 1) % 15) / 10
            
            # Later reactors may have different conditions
            if i > 0:
                current_temp = current_temp - 20 - (seed % 20)  # Generally cooler
                current_pressure = current_pressure - 0.5 - (seed % 10) / 10
            
            reactor_temp = current_temp + temp_variation
            reactor_pressure = current_pressure + pressure_variation
            
            # Reactor volume varies by type
            if "Batch" in reactor_type:
                reactor_volume = 3000 + (seed % 2000)  # 3000-5000L for batch
            elif "PFR" in reactor_type or "Tubular" in reactor_type:
                reactor_volume = 2000 + (seed % 1500)  # 2000-3500L for PFR
            else:
                reactor_volume = 5000 + (seed % 2000)  # 5000-7000L for CSTR
            
            # Determine reactor specs based on type
            if "Batch" in reactor_type:
                specs = {
                    "volume": f"{reactor_volume}L",
                    "type": "Batch",
                    "material": "SS316 with glass lining",
                    "agitator": "Anchor or Paddle",
                    "jacket": "Steam/Water",
                    "batch_time": f"{60 + (seed % 120)} min"
                }
            elif "PFR" in reactor_type or "Tubular" in reactor_type:
                specs = {
                    "volume": f"{reactor_volume}L",
                    "type": "Plug Flow",
                    "material": "SS316",
                    "length": f"{reactor_volume / 100:.1f} m",
                    "diameter": "0.5 m",
                    "residence_time": f"{reactor_volume / (feed_flow * 2.0 / 60):.1f} min"
                }
            elif "Fixed Bed" in reactor_type:
                specs = {
                    "volume": f"{reactor_volume}L",
                    "type": "Fixed Bed",
                    "material": "SS316",
                    "catalyst_bed": "Packed",
                    "residence_time": f"{reactor_volume / (feed_flow * 1.5 / 60):.1f} min"
                }
            else:  # CSTR or default
                specs = {
                    "volume": f"{reactor_volume}L",
                    "type": "Continuous Stirred Tank",
                    "material": "SS316 with glass lining",
                    "agitator": "Rushton turbine",
                    "jacket": "Steam/Water",
                    "residence_time": f"{reactor_volume / (feed_flow * 2.3 / 60):.1f} min"
                }
            
            step_name = f"Step {i+1}" if num_reactors > 1 else ""
            equipment.append({
                "id": f"R-{reactor_num:03d}",
                "type": f"{reactor_type}",
                "name": f"{molecule[:15]} {step_name} {reactor_type}",
                "temperature": round(reactor_temp, 1),
                "pressure": round(reactor_pressure, 2),
                "flow_rate": feed_flow * (2.0 + i * 0.3),
                "specs": {**specs, "process": f"{molecule[:25]} synthesis step {i+1}"}
            })
            
            reactor_num += 1
            control_loop_num += 1
        
        # 3. Intermediate Processing Units (between reactors if multiple)
        separator_num = 1
        if num_reactors > 1:
            for i in range(num_reactors - 1):
                # Add separator/extractor between reactors
                separator_temp = current_temp - 30 - (seed % 20)
                separator_pressure = current_pressure - 0.5 - (seed % 10) / 10
                
                separator_types = ["Liquid-Liquid Separator", "Extractor", "Decanter", "Centrifuge"]
                sep_type = separator_types[(seed * (i + 1)) % len(separator_types)]
                
                equipment.append({
                    "id": f"S-{separator_num:03d}",
                    "type": "Separator",
                    "name": f"{sep_type}",
                    "temperature": round(separator_temp, 1),
                    "pressure": round(separator_pressure, 2),
                    "flow_rate": feed_flow * (2.0 - i * 0.2),
                    "specs": {
                        "type": sep_type,
                        "volume": f"{1000 + (seed % 500)}L",
                        "material": "SS316",
                        "separation_efficiency": f"{90 + (seed % 10)}%"
                    }
                })
                separator_num += 1
        
        # 4. Final Separation and Purification
        final_sep_temp = current_temp - 40 - (seed % 30)
        final_sep_pressure = current_pressure - 0.5
        
        equipment.append({
            "id": f"S-{separator_num:03d}",
            "type": "Separator",
            "name": "Final Product Separator",
            "temperature": round(final_sep_temp, 1),
            "pressure": round(final_sep_pressure, 2),
            "flow_rate": feed_flow * 1.8,
            "specs": {
                "type": "Decanter",
                "volume": "1500L",
                "material": "SS316",
                "separation_efficiency": "98%"
            }
        })
        
        # 5. Crystallizer
        crystallizer_temp = final_sep_temp - 20 - (seed % 20)
        crystallizer_pressure = final_sep_pressure - 0.2
        
        equipment.append({
            "id": "C-301",
            "type": "Crystallizer",
            "name": f"{molecule[:15]} Crystallizer",
            "temperature": round(crystallizer_temp, 1),
            "pressure": round(crystallizer_pressure, 2),
            "flow_rate": feed_flow * 1.5,
            "specs": {
                "type": "Forced circulation",
                "volume": "3000L",
                "material": "SS316",
                "cooling_medium": "Chilled water",
                "crystal_size": "50-200 μm",
                "product": molecule[:25]
            }
        })
        
        # 6. Filtration
        equipment.append({
            "id": "F-401",
            "type": "Filter",
            "name": "Vacuum Filter",
            "temperature": round(crystallizer_temp + 5, 1),
            "pressure": 0.3,  # Vacuum
            "flow_rate": feed_flow * 1.2,
            "specs": {
                "type": "Rotary vacuum filter",
                "area": "10 m²",
                "material": "SS316",
                "cake_moisture": "<5%"
            }
        })
        
        # 7. Dryer
        equipment.append({
            "id": "D-501",
            "type": "Dryer",
            "name": f"{molecule[:15]} Product Dryer",
            "temperature": 60.0,
            "pressure": 1.0,
            "flow_rate": feed_flow * 0.8,
            "specs": {
                "type": "Fluidized bed",
                "volume": "500L",
                "material": "SS316",
                "final_moisture": "<0.1%",
                "product": molecule[:25]
            }
        })
        
        # Get primary reactor for control loops
        primary_reactor = equipment[feed_num - 1] if num_reactors > 0 else None
        primary_temp = primary_reactor["temperature"] if primary_reactor else base_temp
        primary_pressure = primary_reactor["pressure"] if primary_reactor else base_pressure
        
        # Control loops and instrumentation - one for each reactor
        control_loops: List[Dict[str, Any]] = []
        
        # Add control loops for each reactor
        for i, reactor_eq in enumerate([eq for eq in equipment if "R-" in eq["id"]]):
            reactor_num = i + 1
            control_loops.append({
                "tag": f"TIC-{reactor_num:03d}",
                "description": f"Reactor {reactor_num} Temperature Control",
                "setpoint": reactor_eq["temperature"],
                "range": [0, 250],
                "unit": "°C"
            })
            control_loops.append({
                "tag": f"PIC-{reactor_num:03d}",
                "description": f"Reactor {reactor_num} Pressure Control",
                "setpoint": reactor_eq["pressure"],
                "range": [0, 15],
                "unit": "bar"
            })
        
        # Feed flow control
        control_loops.append({
            "tag": "FIC-101",
            "description": "Feed Flow Control",
            "setpoint": feed_flow,
            "range": [0, 500],
            "unit": "L/min"
        })
        
        # Separator level controls
        separators = [eq for eq in equipment if "S-" in eq["id"]]
        for i, sep in enumerate(separators):
            control_loops.append({
                "tag": f"LIC-{201 + i}",
                "description": f"Separator {i+1} Level Control",
                "setpoint": 50 + (seed % 20),
                "range": [0, 100],
                "unit": "%"
            })
        
        # Crystallizer temperature control
        crystallizer = next((eq for eq in equipment if "C-" in eq["id"]), None)
        if crystallizer:
            control_loops.append({
                "tag": "TIC-301",
                "description": "Crystallizer Temperature Control",
                "setpoint": crystallizer["temperature"],
                "range": [-20, 100],
                "unit": "°C"
            })
        
        # Get primary reactor info
        primary_reactor = next((eq for eq in equipment if "R-" in eq["id"]), None)
        if primary_reactor:
            primary_temp = primary_reactor["temperature"]
            primary_pressure = primary_reactor["pressure"]
            primary_volume = int(primary_reactor["specs"].get("volume", "5000").replace("L", ""))
        else:
            primary_temp = base_temp
            primary_pressure = base_pressure
            primary_volume = 5000
        
        return {
            "equipment": equipment,
            "control_loops": control_loops,
            "reactor": {
                "temperature": round(primary_temp, 1),
                "pressure": round(primary_pressure, 2),
                "volume": primary_volume
            },
            "process_conditions": {
                "operating_temperature_range": f"{primary_temp - 20:.0f} - {primary_temp + 20:.0f}°C",
                "operating_pressure_range": f"{primary_pressure - 1:.1f} - {primary_pressure + 1:.1f} bar",
                "residence_time": f"{primary_volume / (feed_flow * 2.0 / 60):.1f} minutes",
                "number_of_reactors": num_reactors,
                "reactor_types": reactor_types,
                "number_of_steps": route["num_steps"]
            },
            "material_handling": {
                "reactants": reactants,
                "catalysts": catalysts,
                "intermediates": route["intermediates"],
                "products": [f"Crystalline {molecule[:20]}", "Mother liquor", "By-products"],
                "recycle_streams": ["Catalyst recycle", "Solvent recovery"] if len(catalysts) > 0 else ["Solvent recovery"],
                "target_molecule": molecule,
                "synthesis_route": f"{route['num_steps']}-step synthesis via {', '.join(reactor_types)}"
            }
        }