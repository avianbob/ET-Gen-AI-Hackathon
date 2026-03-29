import axios from 'axios';

// 1. Get Base URL from .env
//const API_BASE_URL = import.meta.env.VITE_API_URL;
const API_BASE_URL = (import.meta as ImportMeta).env.VITE_API_URL;

// 2. Define Types (Interfaces)
export interface AgentRequestPayload {
  query: string;
  complexity: number;
}

export interface PIDData {
  equipment?: Array<{
    id: string;
    type: string;
    name: string;
    temperature: number;
    pressure: number;
    flow_rate?: number;
    specs?: Record<string, any>;
  }>;
  control_loops?: Array<{
    tag: string;
    description: string;
    setpoint: number;
    range: number[];
    unit: string;
  }>;
  reactor?: {
    temperature: number;
    pressure: number;
    volume: number;
  };
  process_conditions?: {
    operating_temperature_range?: string;
    operating_pressure_range?: string;
    residence_time?: string;
  };
}

export interface AgentResponseData {
  agent_id: string;
  analysis: string;
  recommendation: string;
  grading?: {
    market_demand: number;
    production_feasibility: number;
    demographics: number;
    patents_and_trials: number;
    competition: number;
    overall_score: number;
  };
  visual_data?: {
    revenue_projection?: Array<{
      year: string;
      revenue: number;
      cost: number;
      profit?: number;
    }>;
    /** Market (IQVIA) agent: trend, CAGR, regional breakdown, technical details */
    market_data?: {
      estimated_market_size_billion_usd?: number;
      cagr?: number;
      cagr_percent?: number;
      key_regions?: string[];
      market_demand_score?: number;
      market_trend?: Array<{ year: string; market_size_billion_usd?: number; sales_billion_usd?: number }>;
      regional_breakdown?: Array<{ region: string; share_percent?: number; value_billion_usd?: number }>;
      estimated_sales_projection?: Array<{ year: string; sales_billion_usd?: number }>;
      technical_details?: Record<string, string | number | undefined>;
    };
    /** EXIM agent: trade trend, regional trade, scores */
    exim_data?: {
      import_dependency_score?: number;
      export_opportunity_score?: number;
      overall_market_demand_score?: number;
      trade_trend?: Array<{
        year: string;
        import_index?: number;
        export_index?: number;
        import_value_billion_usd?: number;
        export_value_billion_usd?: number;
      }>;
      regional_trade?: Array<{
        region: string;
        import_share_percent?: number;
        export_share_percent?: number;
      }>;
      technical_details?: Record<string, string | undefined>;
    };
    /** Demographic agent: plant site recommendations (for map + list) */
    demographic_data?: {
      disease_burden_score?: number;
      age_distribution_fit_score?: number;
      access_affordability_score?: number;
      demographic_overall_score?: number;
      plant_site_recommendations?: Array<{
        name: string;
        city?: string;
        country: string;
        lat: number;
        lng: number;
        region_code?: string;
        energy_ease_score?: number;
        land_availability_score?: number;
        market_proximity_score?: number;
        export_supply_score?: number;
        overall_site_score?: number;
        rationale?: Record<string, string>;
      }>;
      technical_details?: Record<string, string>;
    };
    /** Molecular details (name, family, weight, structure image, brief + physicochemical props) */
    molecular_details?: {
      molecular_name?: string;
      molecular_family?: string;
      molecular_weight_g_per_mol?: number;
      brief_details?: string;
      structure_image_url?: string;
      molecular_weight_impact?: string;
      solubility?: string;
      solubility_why_it_matters?: string;
      lipophilicity_log_p?: string;
      lipophilicity_why_it_matters?: string;
      pka?: string;
      pka_why_it_matters?: string;
      melting_point?: string;
      melting_point_why_it_matters?: string;
      crystalline_nature?: string;
      crystalline_why_it_matters?: string;
      hygroscopicity?: string;
      hygroscopicity_why_it_matters?: string;
      chemical_stability?: string;
      chemical_stability_why_it_matters?: string;
      particle_size_surface_area?: string;
      particle_size_why_it_matters?: string;
      bcs_class?: string;
      permeability_notes?: string;
      permeability_why_it_matters?: string;
      solid_state_properties?: string;
      solid_state_why_it_matters?: string;
      excipient_compatibility?: string;
      excipient_why_it_matters?: string;
    };
  };
  pid_data?: PIDData | null;
  tea_data?: {
    // CAPEX
    equipment_capex_million_usd?: number;
    installation_capex_million_usd?: number;
    piping_instrumentation_capex_million_usd?: number;
    buildings_infrastructure_capex_million_usd?: number;
    engineering_design_capex_million_usd?: number;
    contingency_capex_million_usd?: number;
    total_capex_million_usd?: number;
    // OPEX
    raw_material_cost_million_usd_per_year?: number;
    utility_cost_million_usd_per_year?: number;
    labor_cost_million_usd_per_year?: number;
    maintenance_cost_million_usd_per_year?: number;
    insurance_overhead_cost_million_usd_per_year?: number;
    total_opex_million_usd_per_year?: number;
    // Financial
    revenue_million_usd_per_year?: number;
    gross_profit_million_usd_per_year?: number;
    gross_margin_percent?: number;
    payback_period_years?: number;
    internal_rate_of_return?: number;
    net_present_value_million_usd?: number;
    product_price_usd_per_kg?: number;
    production_capacity_kg_per_year?: number;
    cost_per_kg_usd?: number;
    production_feasibility_score?: number;
    equipment_costs?: Record<string, any>;
    pid_based?: boolean;
  } | null;
  query_context?: {
    drug?: string | null;
    disease?: string | null;
    diseases?: string[] | null;
    symptoms?: string[] | null;
    side_effects?: string[] | null;
    regions?: string[] | null;
    phase?: string | null;
    raw_query?: string | null;
  } | null;
  clinical_trials_data?: {
    decision?: { drug?: string; disease?: string; intent?: string; reasoning?: string };
    analytics?: {
      phase_distribution?: Record<string, number>;
      sponsor_distribution?: Record<string, number>;
      total_found?: number;
    };
    results?: Array<{
      id: string;
      title: string;
      status: string;
      phases: string[];
      sponsor: string;
      conditions: string[];
      brief_summary?: string;
      primary_outcome?: string;
      eligibility?: string;
    }>;
    ongoing_trials_count?: number;
    extracted_insights?: {
      symptoms?: string[];
      diseases?: string[];
      side_effects?: string[];
    };
  } | null;
  /** When Gemini returned 429, Groq was used for these operations */
  llm_fallback_used?: string[];
}

// 3. Create Axios Instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Clinical Trials test response (ClinicalTrials.gov)
export interface ClinicalTrialsDecision {
  drug?: string | null;
  disease?: string | null;
  intent: string;
  reasoning: string;
}
export interface ClinicalTrialsTestResponse {
  decision: ClinicalTrialsDecision;
  search_results: {
    decision?: ClinicalTrialsDecision;
    analytics?: {
      phase_distribution?: Record<string, number>;
      sponsor_distribution?: Record<string, number>;
      total_found?: number;
    };
    results?: Array<{
      id: string;
      title: string;
      status: string;
      phases: string[];
      sponsor: string;
      conditions: string[];
      brief_summary?: string;
      detailed_description?: string;
      primary_outcome?: string;
      eligibility?: string;
    }>;
    error?: string;
  };
}

// 4. Export API Functions
export const AgentAPI = {
  runAgent: async (payload: AgentRequestPayload) => {
    const response = await apiClient.post<AgentResponseData>('/api/run-agent', payload);
    return response.data;
  },
  clinicalTrialsTest: async (prompt: string) => {
    const response = await apiClient.post<ClinicalTrialsTestResponse>('/api/clinical-trials-test', { prompt });
    return response.data;
  },
};