"""
ClinicalTrials.gov API v2 integration: intent-based search (same logic as ClinicalTrails.gov helper).
Uses SearchIntent and AgentDecision to query clinicaltrials.gov with the correct params.
"""
import requests
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum
from collections import Counter


class SearchIntent(str, Enum):
    DISCOVERY = "DISCOVERY"
    VALIDATION = "VALIDATION"
    BROAD = "BROAD"
    REVERSE_DISCOVERY = "REVERSE_DISCOVERY"


class AgentDecision(BaseModel):
    drug: Optional[str] = Field(None, description="The drug name. REQUIRED unless intent is REVERSE_DISCOVERY.")
    disease: Optional[str] = Field(None, description="The disease name. REQUIRED if intent is REVERSE_DISCOVERY.")
    intent: SearchIntent = Field(..., description="The classification of the user's research goal.")
    reasoning: str = Field(..., description="Brief explanation of why you chose this intent.")


def execute_clinical_search(decision: AgentDecision) -> Dict[str, Any]:
    """
    Call ClinicalTrials.gov API v2 with params determined by AgentDecision intent.
    Returns dict with decision, analytics (phase_distribution, sponsor_distribution, total_found), and results list.
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    status_filter = "RECRUITING,COMPLETED,WITHDRAWN,TERMINATED"
    field_list = [
        "NCTId", "BriefTitle", "Condition", "OverallStatus",
        "LeadSponsorName", "LeadSponsorClass",
        "DescriptionModule",
        "EligibilityModule",
        "OutcomesModule",
        "DesignModule"
    ]
    params: Dict[str, Any] = {
        "format": "json",
        "filter.overallStatus": status_filter,
        "fields": ",".join(field_list),
        "pageSize": 25,
    }

    if decision.intent == SearchIntent.REVERSE_DISCOVERY and decision.disease:
        disease_term = (decision.disease or "").strip().split(",")[0].strip()
        if not disease_term:
            disease_term = "Pain"
        params["query.term"] = disease_term
    elif decision.intent == SearchIntent.DISCOVERY and decision.drug:
        query_term = f'{decision.drug} NOT "{decision.disease}"' if decision.disease else decision.drug
        params["query.term"] = query_term
    elif decision.intent == SearchIntent.VALIDATION and decision.drug and decision.disease:
        query_term = f'{decision.drug} AND "{decision.disease}"'
        params["query.term"] = query_term
    elif decision.intent == SearchIntent.BROAD and decision.drug:
        params["query.term"] = decision.drug

    try:
        print(f"[ClinicalTrials] Calling API: {base_url} with params: {params}")
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        studies = data.get("studies", [])
        print(f"[ClinicalTrials] API returned {len(studies)} studies")

        clean_results = []
        phases_list = []
        sponsors_list = []

        for s in studies:
            proto = s.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
            desc_mod = proto.get("descriptionModule", {})
            elig_mod = proto.get("eligibilityModule", {})
            out_mod = proto.get("outcomesModule", {})

            brief_summary = desc_mod.get("briefSummary", "No summary.")
            detailed_desc = desc_mod.get("detailedDescription", "No detailed description available.")
            primary_outcomes = out_mod.get("primaryOutcomes", [])
            outcome_measure = primary_outcomes[0].get("measure", "Not defined") if primary_outcomes else "Not defined"
            criteria = elig_mod.get("eligibilityCriteria", "Not defined")

            nct_id = ident.get("nctId")
            title = ident.get("briefTitle")
            trial_status = status.get("overallStatus")
            sponsor_name = sponsor_mod.get("leadSponsor", {}).get("name", "Unknown")
            sponsor_class = sponsor_mod.get("leadSponsor", {}).get("class", "UNKNOWN")
            trial_phases = design.get("phases", ["Not Applicable"])
            conditions = proto.get("conditionsModule", {}).get("conditions", [])

            phases_list.extend(trial_phases)
            sponsors_list.append(sponsor_class)

            clean_results.append({
                "id": nct_id,
                "title": title,
                "status": trial_status,
                "phases": trial_phases,
                "sponsor": sponsor_name,
                "conditions": conditions[:3],
                "brief_summary": brief_summary,
                "detailed_description": detailed_desc,
                "primary_outcome": outcome_measure,
                "eligibility": criteria,
            })

        result = {
            "decision": decision.model_dump(),
            "analytics": {
                "phase_distribution": dict(Counter(phases_list)),
                "sponsor_distribution": dict(Counter(sponsors_list)),
                "total_found": len(studies),
            },
            "results": clean_results,
        }
        print(f"[ClinicalTrials] Built result: total_found={len(studies)}, analytics={result['analytics']}")
        return result
    except Exception as e:
        print(f"[ClinicalTrials] API error: {e}")
        return {"error": str(e)}
