"""
PDF Template Data Transformation Layer

Transforms SearchResponse data into template-ready format for Jinja2 templates.
Enhanced version with full UI data support.
"""

import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel


def get_confidence_class(score: float) -> str:
    """Return CSS class based on confidence score."""
    if score >= 80:
        return "very-high"
    elif score >= 65:
        return "high"
    elif score >= 50:
        return "moderate"
    elif score >= 35:
        return "low"
    return "very-low"


def get_confidence_label(score: float) -> str:
    """Return human-readable confidence label."""
    if score >= 80:
        return "Very High"
    elif score >= 65:
        return "High"
    elif score >= 50:
        return "Moderate"
    elif score >= 35:
        return "Low"
    return "Very Low"


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get a value from dict or object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def to_dict(obj: Any) -> Any:
    """Convert Pydantic model or dict to dict recursively."""
    if obj is None:
        return None
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    return obj


def calculate_radar_points(scientific: float, market: float,
                           competitive: float, feasibility: float) -> str:
    """
    Calculate SVG polygon points for 4-axis radar chart.

    The radar has 4 axes at 90-degree intervals:
    - Top (0°): Scientific Evidence
    - Right (90°): Market Opportunity
    - Bottom (180°): Competitive Landscape
    - Left (270°): Development Feasibility
    """
    def normalize(val: float) -> float:
        """Normalize score (0-100) to radius (0-80)."""
        return (val / 100) * 80

    values = [scientific, market, competitive, feasibility]
    angles = [90, 0, 270, 180]  # Degrees: top, right, bottom, left

    points = []
    for angle, value in zip(angles, values):
        rad = math.radians(angle)
        r = normalize(value)
        x = r * math.cos(rad)
        y = -r * math.sin(rad)  # Negative for SVG coordinate system
        points.append(f"{x:.1f},{y:.1f}")

    return " ".join(points)


def format_source_name(source: str) -> str:
    """Format source name for display."""
    source_names = {
        'clinical_trials': 'Clinical Trials',
        'literature': 'Literature',
        'bioactivity': 'Bioactivity',
        'patent': 'Patents',
        'internal': 'Internal',
        'openfda': 'OpenFDA',
        'opentargets': 'OpenTargets',
        'semantic_scholar': 'Semantic Scholar',
        'dailymed': 'DailyMed',
        'kegg': 'KEGG',
        'uniprot': 'UniProt',
        'orange_book': 'Orange Book',
        'rxnorm': 'RxNorm',
        'who': 'WHO',
        'drugbank': 'DrugBank',
        'market_data': 'Market Data',
    }
    return source_names.get(source.lower(), source.replace('_', ' ').title())


def format_source_class(source: str) -> str:
    """Format source name for CSS class."""
    return source.lower().replace(' ', '').replace('_', '')


def transform_evidence_by_source(evidence_list: List[Dict]) -> List[Dict]:
    """
    Group evidence by source for the evidence catalog.

    Returns list of: {'name': str, 'count': int, 'percentage': float}
    """
    source_counts = {}
    for e in evidence_list:
        source = safe_get(e, 'source', 'Unknown')
        source_counts[source] = source_counts.get(source, 0) + 1

    total = len(evidence_list)
    result = []
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        result.append({
            'name': format_source_name(source),
            'count': count,
            'percentage': (count / total * 100) if total > 0 else 0
        })

    return result


def extract_dimension_score(composite: Any, dimension: str, default: float = 50.0) -> float:
    """Extract dimension score from composite score object."""
    if composite is None:
        return default

    if isinstance(composite, dict):
        dim_data = composite.get(dimension)
        if dim_data is None:
            return default
        if isinstance(dim_data, dict):
            return dim_data.get('score', default)
        return getattr(dim_data, 'score', default)

    dim_obj = getattr(composite, dimension, None)
    if dim_obj is None:
        return default
    return safe_get(dim_obj, 'score', default)


def extract_weighted_score(composite: Any, dimension: str, default: float = 0.0) -> float:
    """Extract weighted_score from dimension."""
    if composite is None:
        return default

    if isinstance(composite, dict):
        dim_data = composite.get(dimension)
        if dim_data is None:
            return default
        if isinstance(dim_data, dict):
            return dim_data.get('weighted_score', default)
        return getattr(dim_data, 'weighted_score', default)

    dim_obj = getattr(composite, dimension, None)
    if dim_obj is None:
        return default
    return safe_get(dim_obj, 'weighted_score', default)


def extract_dimension_weight(composite: Any, dimension: str) -> float:
    """Extract weight from dimension (returns percentage 0-100)."""
    if composite is None:
        # Default weights
        defaults = {
            'scientific_evidence': 40,
            'market_opportunity': 25,
            'competitive_landscape': 20,
            'development_feasibility': 15
        }
        return defaults.get(dimension, 25)

    if isinstance(composite, dict):
        dim_data = composite.get(dimension)
        if dim_data is None:
            return 25
        if isinstance(dim_data, dict):
            weight = dim_data.get('weight', 0.25)
            return weight * 100 if weight <= 1 else weight
        weight = getattr(dim_data, 'weight', 0.25)
        return weight * 100 if weight <= 1 else weight

    dim_obj = getattr(composite, dimension, None)
    if dim_obj is None:
        return 25
    weight = safe_get(dim_obj, 'weight', 0.25)
    return weight * 100 if weight <= 1 else weight


def transform_insights(composite: Any, key: str) -> List[Dict]:
    """
    Transform insights with full details (title, description, severity, source_dimension).

    Args:
        composite: Composite score object
        key: 'key_strengths', 'key_risks', or 'recommended_next_steps'

    Returns:
        List of insight dicts with full details
    """
    if composite is None:
        return []

    insights_raw = safe_get(composite, key, []) or []
    insights = []

    for insight in insights_raw:
        insights.append({
            'title': safe_get(insight, 'title', 'Insight'),
            'description': safe_get(insight, 'description', ''),
            'severity': safe_get(insight, 'severity', 'medium'),
            'source_dimension': format_dimension_name(safe_get(insight, 'source_dimension', '')),
            'category': safe_get(insight, 'category', key.replace('key_', '').replace('recommended_', ''))
        })

    return insights


def format_dimension_name(dimension: str) -> str:
    """Format dimension name for display."""
    names = {
        'scientific_evidence': 'Scientific Evidence',
        'market_opportunity': 'Market Opportunity',
        'competitive_landscape': 'Competitive Landscape',
        'development_feasibility': 'Development Feasibility'
    }
    return names.get(dimension, dimension.replace('_', ' ').title())


def extract_competitors(composite: Any) -> List[Dict]:
    """
    Extract competitor list from competitive_landscape dimension.

    Returns list of: {'drug': str, 'company': str, 'phase': str}
    """
    if composite is None:
        return []

    # Try to get from competitive_landscape dimension
    comp_dim = safe_get(composite, 'competitive_landscape')
    if comp_dim is None:
        return []

    # Check for competitors list in the dimension
    competitors_raw = safe_get(comp_dim, 'competitors', []) or []

    competitors = []
    for comp in competitors_raw:
        competitors.append({
            'drug': safe_get(comp, 'drug', 'Unknown Drug'),
            'company': safe_get(comp, 'company', 'Unknown Company'),
            'phase': safe_get(comp, 'phase', 'Unknown')
        })

    return competitors


def extract_market_factor(composite: Any, factor: str, default: Any = None) -> Any:
    """Extract specific market factor value from market_opportunity dimension."""
    if composite is None:
        return default

    market_dim = safe_get(composite, 'market_opportunity')
    if market_dim is None:
        return default

    factors = safe_get(market_dim, 'factors', {}) or {}
    return factors.get(factor, default)


def transform_evidence_full(evidence_list: List[Dict], limit: int = 10) -> List[Dict]:
    """
    Transform evidence with URL, date, and key metadata.

    Args:
        evidence_list: Raw evidence items
        limit: Maximum number of items to return

    Returns:
        List of enhanced evidence dicts
    """
    result = []

    for e in evidence_list[:limit]:
        relevance = safe_get(e, 'relevance_score', 0.7)
        if relevance is not None and relevance <= 1:
            relevance = relevance * 100  # Convert 0-1 to 0-100

        metadata = safe_get(e, 'metadata', {}) or {}

        result.append({
            'source': format_source_name(safe_get(e, 'source', 'Unknown')),
            'source_class': format_source_class(safe_get(e, 'source', 'unknown')),
            'title': safe_get(e, 'title', 'Untitled') or 'Untitled',
            'summary': safe_get(e, 'summary', ''),
            'indication': safe_get(e, 'indication', ''),
            'relevance': relevance or 70,
            'url': safe_get(e, 'url', ''),
            'date': safe_get(e, 'date', ''),
            'metadata': {
                'pmid': metadata.get('pmid', ''),
                'nct_id': metadata.get('nct_id', ''),
                'year': metadata.get('year', ''),
                'citations': metadata.get('citations', ''),
            }
        })

    return result


def extract_data_completeness(composite: Any, default: float = 0.5) -> float:
    """Extract data completeness from composite score (returns 0-100)."""
    if composite is None:
        return default * 100

    completeness = safe_get(composite, 'data_completeness', default)
    # Convert from 0-1 to 0-100 if needed
    if completeness is not None and completeness <= 1:
        return completeness * 100
    return completeness or (default * 100)


def transform_enhanced_opportunity(enhanced: Dict) -> Dict:
    """
    Transform enhanced opportunity data (comparisons, segments, science) for template.

    Args:
        enhanced: EnhancedOpportunityData dict

    Returns:
        Dict with template-ready enhanced data
    """
    result = {}

    # Comparator drugs
    comparator_drugs = safe_get(enhanced, 'comparator_drugs', []) or []
    result['comparator_drugs'] = []
    for comp in comparator_drugs[:5]:  # Limit to 5
        result['comparator_drugs'].append({
            'drug_name': safe_get(comp, 'drug_name', 'Unknown'),
            'mechanism': safe_get(comp, 'mechanism', 'Unknown'),
            'administration_route': safe_get(comp, 'administration_route', 'N/A'),
            'dosing_frequency': safe_get(comp, 'dosing_frequency', 'N/A'),
            'typical_duration': safe_get(comp, 'typical_duration', 'N/A'),
            'age_restrictions': safe_get(comp, 'age_restrictions', 'None'),
            'key_side_effects': safe_get(comp, 'key_side_effects', [])[:3],
            'contraindications': safe_get(comp, 'contraindications', [])[:3],
            'average_monthly_cost': safe_get(comp, 'average_monthly_cost'),
            'approval_year': safe_get(comp, 'approval_year'),
            'market_share_percent': safe_get(comp, 'market_share_percent'),
        })

    # Comparative advantages
    comparative_advantages = safe_get(enhanced, 'comparative_advantages', []) or []
    result['comparative_advantages'] = []
    for adv in comparative_advantages[:6]:  # Limit to 6
        result['comparative_advantages'].append({
            'category': safe_get(adv, 'category', 'general'),
            'description': safe_get(adv, 'description', ''),
            'comparator_value': safe_get(adv, 'comparator_value', ''),
            'candidate_value': safe_get(adv, 'candidate_value', ''),
            'impact': safe_get(adv, 'impact', 'medium'),
            'patient_benefit': safe_get(adv, 'patient_benefit', ''),
        })

    # Side effect comparison
    side_effect_comparison = safe_get(enhanced, 'side_effect_comparison')
    if side_effect_comparison:
        result['side_effect_comparison'] = {
            'comparator_drug': safe_get(side_effect_comparison, 'comparator_drug', 'Standard Treatment'),
            'eliminated_effects': safe_get(side_effect_comparison, 'eliminated_effects', [])[:5],
            'reduced_effects': safe_get(side_effect_comparison, 'reduced_effects', [])[:5],
            'new_concerns': safe_get(side_effect_comparison, 'new_concerns', [])[:3],
            'safety_advantage_score': safe_get(side_effect_comparison, 'safety_advantage_score', 0),
            'safety_summary': safe_get(side_effect_comparison, 'safety_summary', ''),
        }
    else:
        result['side_effect_comparison'] = None

    # Market segment
    market_segment = safe_get(enhanced, 'market_segment')
    if market_segment:
        result['market_segment'] = {
            'segment_name': safe_get(market_segment, 'segment_name', 'General Market'),
            'parent_indication': safe_get(market_segment, 'parent_indication', ''),
            'segment_size_billions': safe_get(market_segment, 'segment_size_billions'),
            'patient_subpopulation': safe_get(market_segment, 'patient_subpopulation'),
            'segment_share_percent': safe_get(market_segment, 'segment_share_percent'),
            'unmet_need': safe_get(market_segment, 'unmet_need', 'Medium'),
            'target_patient_profile': safe_get(market_segment, 'target_patient_profile', ''),
            'key_differentiators': safe_get(market_segment, 'key_differentiators', [])[:4],
            'growth_rate_percent': safe_get(market_segment, 'growth_rate_percent'),
            'competitive_intensity': safe_get(market_segment, 'competitive_intensity', 'Medium'),
        }
    else:
        result['market_segment'] = None

    # Scientific details
    scientific_details = safe_get(enhanced, 'scientific_details')
    if scientific_details:
        # Structure key publications with full details
        raw_pubs = safe_get(scientific_details, 'key_publications', []) or []
        publications = []
        for pub in raw_pubs[:3]:
            publications.append({
                'title': safe_get(pub, 'title', 'Untitled'),
                'authors': safe_get(pub, 'authors', ''),
                'journal': safe_get(pub, 'journal', ''),
                'year': safe_get(pub, 'year', ''),
                'citation_count': safe_get(pub, 'citation_count', 0),
                'key_finding': safe_get(pub, 'key_finding', ''),
                'url': safe_get(pub, 'url', ''),
                'pmid': safe_get(pub, 'pmid', ''),
            })

        result['scientific_details'] = {
            'mechanism_of_action': safe_get(scientific_details, 'mechanism_of_action', 'Not specified'),
            'target_protein': safe_get(scientific_details, 'target_protein', 'Unknown'),
            'target_gene': safe_get(scientific_details, 'target_gene', 'Unknown'),
            'target_class': safe_get(scientific_details, 'target_class', 'Unknown'),
            'pathways': safe_get(scientific_details, 'pathways', [])[:5],
            'binding_affinity_nm': safe_get(scientific_details, 'binding_affinity_nm'),
            'selectivity_profile': safe_get(scientific_details, 'selectivity_profile', ''),
            'key_publications': publications,
            'biomarkers': safe_get(scientific_details, 'biomarkers', [])[:5],
            'preclinical_models': safe_get(scientific_details, 'preclinical_models', [])[:6],
            'clinical_evidence_summary': safe_get(scientific_details, 'clinical_evidence_summary', ''),
            'mechanistic_rationale': safe_get(scientific_details, 'mechanistic_rationale', ''),
        }
    else:
        result['scientific_details'] = None

    return result


def transform_opportunity(opp: Dict, evidence_list: List[Dict]) -> Dict:
    """
    Transform a single opportunity for the template.

    Handles both old-style (IndicationResult) and new-style (EnhancedIndicationResult)
    data structures. Enhanced version includes all UI data.
    """
    indication = safe_get(opp, 'indication', 'Unknown')

    # Get score - handle both old and new data structures
    score = safe_get(opp, 'confidence_score') or safe_get(opp, 'score') or 0

    # Try to get score from composite_score
    composite = safe_get(opp, 'composite_score')
    if composite:
        overall = safe_get(composite, 'overall_score')
        if overall is not None:
            score = overall

    # Get dimension scores
    if composite:
        scientific = extract_dimension_score(composite, 'scientific_evidence', 50)
        market = extract_dimension_score(composite, 'market_opportunity', 50)
        competitive = extract_dimension_score(composite, 'competitive_landscape', 50)
        feasibility = extract_dimension_score(composite, 'development_feasibility', 50)
    else:
        scientific = safe_get(opp, 'scientific_score', 50)
        market = safe_get(opp, 'market_score', 50)
        competitive = safe_get(opp, 'competitive_score', 50)
        feasibility = safe_get(opp, 'feasibility_score', 50)

    # Get dimension weights and weighted scores
    scientific_weight = extract_dimension_weight(composite, 'scientific_evidence')
    market_weight = extract_dimension_weight(composite, 'market_opportunity')
    competitive_weight = extract_dimension_weight(composite, 'competitive_landscape')
    feasibility_weight = extract_dimension_weight(composite, 'development_feasibility')

    scientific_weighted = extract_weighted_score(composite, 'scientific_evidence', scientific * 0.4)
    market_weighted = extract_weighted_score(composite, 'market_opportunity', market * 0.25)
    competitive_weighted = extract_weighted_score(composite, 'competitive_landscape', competitive * 0.2)
    feasibility_weighted = extract_weighted_score(composite, 'development_feasibility', feasibility * 0.15)

    # Get evidence for this opportunity
    indication_lower = indication.lower()
    opp_evidence = [
        e for e in evidence_list
        if safe_get(e, 'indication', '').lower() == indication_lower
    ]

    # If no direct match, use evidence_items from the opportunity
    if not opp_evidence:
        opp_evidence = safe_get(opp, 'evidence_items', []) or []

    # Get unique sources
    sources_set = set()
    for e in opp_evidence:
        src = safe_get(e, 'source', 'Unknown')
        sources_set.add(format_source_name(src))

    # Also check supporting_sources
    supporting = safe_get(opp, 'supporting_sources', []) or []
    for src in supporting:
        sources_set.add(format_source_name(src))

    sources = list(sources_set)[:5]

    # Get full insights with metadata
    strengths_full = transform_insights(composite, 'key_strengths')
    risks_full = transform_insights(composite, 'key_risks')
    next_steps = transform_insights(composite, 'recommended_next_steps')

    # Build simplified strengths/risks for backward compatibility
    strengths = []
    risks = []

    for s in strengths_full[:3]:
        strengths.append({
            'title': s['title'],
            'description': s['description'][:100] if len(s['description']) > 100 else s['description']
        })

    for r in risks_full[:3]:
        risks.append({
            'title': r['title'],
            'description': r['description'][:100] if len(r['description']) > 100 else r['description']
        })

    # Default strengths if none found
    if not strengths:
        if score >= 65:
            strengths.append({
                'title': 'Strong Evidence Base',
                'description': 'Multiple supporting data points across sources'
            })
        if scientific >= 70:
            strengths.append({
                'title': 'Clinical Validation',
                'description': 'Clinical trial data supports this indication'
            })
        if market >= 70:
            strengths.append({
                'title': 'Large Market',
                'description': 'Substantial commercial potential'
            })
        if feasibility >= 70:
            strengths.append({
                'title': 'Development Ready',
                'description': 'Favorable regulatory pathway and safety profile'
            })

    # Default risks if none found
    if not risks:
        if competitive < 50:
            risks.append({
                'title': 'Competitive Market',
                'description': 'Multiple competitors in development'
            })
        if market < 40:
            risks.append({
                'title': 'Limited Market',
                'description': 'Smaller market size may limit commercial potential'
            })

    # Get market data from composite score factors
    market_size = extract_market_factor(composite, 'market_size_raw_billions')
    cagr = extract_market_factor(composite, 'cagr_percent_raw')
    patient_population = extract_market_factor(composite, 'patient_population_millions')
    pricing_potential = extract_market_factor(composite, 'pricing_potential_raw')
    unmet_need_raw = extract_market_factor(composite, 'unmet_need_raw')

    if unmet_need_raw is not None:
        if unmet_need_raw >= 70:
            unmet_need = "High"
        elif unmet_need_raw >= 40:
            unmet_need = "Medium"
        else:
            unmet_need = "Low"
    else:
        unmet_need = "Medium"

    # Get competitors
    competitors = extract_competitors(composite)

    # Get data completeness
    data_completeness = extract_data_completeness(composite)

    # Format enhanced evidence (top 10 with full details)
    evidence_full = transform_evidence_full(opp_evidence, limit=10)

    # Format basic evidence for backward compatibility (top 5)
    top_evidence = []
    for e in opp_evidence[:5]:
        relevance = safe_get(e, 'relevance_score', 0.7)
        if relevance is not None and relevance <= 1:
            relevance = relevance * 100

        top_evidence.append({
            'source': format_source_name(safe_get(e, 'source', 'Unknown')),
            'title': (safe_get(e, 'title', 'Untitled') or 'Untitled')[:60],
            'indication': safe_get(e, 'indication'),
            'relevance': relevance or 70
        })

    evidence_count = safe_get(opp, 'evidence_count', len(opp_evidence))

    return {
        'indication': indication,
        'score': score,
        'confidence_class': get_confidence_class(score),
        'confidence_label': get_confidence_label(score),

        # Dimension scores (raw)
        'scientific_score': scientific,
        'market_score': market,
        'competitive_score': competitive,
        'feasibility_score': feasibility,

        # Dimension weights (percentage)
        'scientific_weight': scientific_weight,
        'market_weight': market_weight,
        'competitive_weight': competitive_weight,
        'feasibility_weight': feasibility_weight,

        # Dimension weighted scores
        'scientific_weighted': scientific_weighted,
        'market_weighted': market_weighted,
        'competitive_weighted': competitive_weighted,
        'feasibility_weighted': feasibility_weighted,

        # Evidence and sources
        'evidence_count': evidence_count,
        'sources': sources,
        'source_count': len(sources),

        # Insights (simplified for backward compat)
        'strengths': strengths[:3],
        'risks': risks[:3],

        # Full insights with metadata
        'strengths_full': strengths_full,
        'risks_full': risks_full,
        'next_steps': next_steps,

        # Market data
        'market_size': market_size,
        'cagr': cagr,
        'patient_population': patient_population,
        'pricing_potential': pricing_potential,
        'unmet_need': unmet_need,

        # Competitive data
        'competitors': competitors,
        'competitor_count': len(competitors),

        # Data quality
        'data_completeness': data_completeness,

        # Evidence (basic for backward compat)
        'top_evidence': top_evidence,

        # Enhanced evidence with URLs/dates
        'evidence_full': evidence_full,

        # For radar chart
        'radar_points': calculate_radar_points(scientific, market, competitive, feasibility),
        'color': '#00B4D8'  # Default cyan, will be overridden for top 3
    }


def prepare_opportunity_template_data(
    drug_name: str,
    opportunity: Union[Dict, BaseModel],
    evidence_items: List[Union[Dict, BaseModel]],
    enhanced_opportunity: Optional[Dict] = None,
) -> Dict:
    """
    Transform a single opportunity into template-ready data for the mini report.

    Reuses existing transform functions for consistency with the full report.

    Args:
        drug_name: Name of the drug
        opportunity: Single opportunity dict or Pydantic model
        evidence_items: Evidence items for this indication
        enhanced_opportunity: Enhanced data (comparisons, market, science)

    Returns:
        Dict ready for Jinja2 template rendering
    """
    opp_dict = to_dict(opportunity)
    evidence_list = [to_dict(e) for e in evidence_items]

    # Reuse the core opportunity transformer
    transformed = transform_opportunity(opp_dict, evidence_list)

    # Merge enhanced data if available
    if enhanced_opportunity:
        enhanced_dict = to_dict(enhanced_opportunity)
        transformed.update(transform_enhanced_opportunity(enhanced_dict))

    # Get evidence source distribution
    indication = transformed.get('indication', 'Unknown')
    indication_lower = indication.lower()
    indication_evidence = [
        e for e in evidence_list
        if safe_get(e, 'indication', '').lower() == indication_lower
    ]
    if not indication_evidence:
        indication_evidence = evidence_list

    evidence_by_source = transform_evidence_by_source(indication_evidence)

    # Expand evidence to 20 items for the mini report (full report uses 10)
    transformed['evidence_full'] = transform_evidence_full(indication_evidence, limit=20)
    transformed['evidence_count'] = len(indication_evidence)

    # Get unique sources
    sources = set()
    for e in indication_evidence:
        sources.add(format_source_name(safe_get(e, 'source', 'Unknown')))
    source_count = len(sources)

    now = datetime.now()

    # Calculate total pages (3-5 based on content)
    has_comparative = bool(transformed.get('comparator_drugs') or transformed.get('comparative_advantages'))
    has_market = bool(transformed.get('market_segment'))
    has_science = bool(transformed.get('scientific_details'))
    total_pages = 2  # Cover+scoring + insights+comparative are always present
    if has_market or has_science:
        total_pages += 1  # Market & Science page
    total_pages += 1  # Evidence catalog always present
    if len(indication_evidence) > 15:
        total_pages += 1  # Overflow page

    return {
        **transformed,
        'drug_name': drug_name,
        'evidence_by_source': evidence_by_source,
        'source_count': source_count,
        'generated_at': now.strftime('%B %d, %Y'),
        'generated_at_full': now.strftime('%Y-%m-%d %H:%M UTC'),
        'total_pages': total_pages,
    }


def prepare_template_data(result: Union[Dict, BaseModel]) -> Dict:
    """
    Transform SearchResponse into template-ready data.

    Args:
        result: SearchResponse dict or Pydantic model

    Returns:
        Dict ready for Jinja2 template rendering
    """
    # Convert to dict if Pydantic model
    if hasattr(result, 'model_dump'):
        result = result.model_dump()
    elif hasattr(result, 'dict'):
        result = result.dict()

    result = to_dict(result)

    drug_name = safe_get(result, 'drug_name', 'Unknown Drug')
    evidence_list = safe_get(result, 'all_evidence', []) or []

    # Convert evidence items to dicts
    evidence_list = [to_dict(e) for e in evidence_list]

    # Get opportunities from either enhanced or ranked
    raw_opportunities = (
        safe_get(result, 'enhanced_indications', []) or
        safe_get(result, 'ranked_indications', []) or
        []
    )

    # Get enhanced opportunities data (comparisons, segments, science)
    enhanced_opportunities = safe_get(result, 'enhanced_opportunities', {}) or {}

    # Transform opportunities
    opportunities = []
    radar_colors = ['#00B4D8', '#10B981', '#F59E0B']  # Cyan, Emerald, Gold

    for i, opp in enumerate(raw_opportunities):
        opp_dict = to_dict(opp)
        transformed = transform_opportunity(opp_dict, evidence_list)
        if i < 3:
            transformed['color'] = radar_colors[i]

        # Merge enhanced opportunity data if available
        indication = transformed['indication']
        enhanced_data = enhanced_opportunities.get(indication)
        if enhanced_data:
            enhanced_dict = to_dict(enhanced_data)
            transformed.update(transform_enhanced_opportunity(enhanced_dict))

        opportunities.append(transformed)

    # Sort by score descending
    opportunities.sort(key=lambda x: x['score'], reverse=True)

    # Re-apply radar colors after sort
    for i, opp in enumerate(opportunities[:3]):
        opp['color'] = radar_colors[i]

    # Get synthesis
    synthesis = safe_get(result, 'synthesis', '') or ''
    if isinstance(synthesis, dict):
        synthesis = safe_get(synthesis, 'summary', '') or safe_get(synthesis, 'text', '') or str(synthesis)

    # Truncate synthesis for summary
    synthesis_summary = synthesis[:500] + '...' if len(synthesis) > 500 else synthesis

    # Calculate totals
    opportunity_count = len(opportunities)
    evidence_count = len(evidence_list)
    sources = set(safe_get(e, 'source', 'unknown') for e in evidence_list)
    source_count = len(sources)
    execution_time = safe_get(result, 'execution_time', 0) or 0

    # Top opportunity
    top_opportunity = opportunities[0] if opportunities else None

    # Top 3 for radar chart
    top_3_opportunities = opportunities[:3]

    # Evidence by source
    evidence_by_source = transform_evidence_by_source(evidence_list)

    # Top 5 get full detail, rest get summary table
    top_5_opportunities = opportunities[:5]
    remaining_opportunities = opportunities[5:]

    # Calculate total pages
    # Cover (1) + Exec Summary (1) + Rankings (1-2) + Top 5 Details (2 each) + Remaining (0-1) + Methodology (1)
    top_5_count = min(5, len(opportunities))
    detail_pages = top_5_count * 2  # 2 pages per top-5 opportunity
    rankings_pages = 2 if len(opportunities) > 12 else 1
    remaining_pages = 1 if len(remaining_opportunities) > 0 else 0
    total_pages = 1 + 1 + rankings_pages + detail_pages + remaining_pages + 1

    now = datetime.now()

    full_report_extensions = safe_get(result, 'full_report_extensions', None) or {}

    return {
        'drug_name': drug_name,
        'opportunity_count': opportunity_count,
        'evidence_count': evidence_count,
        'source_count': source_count,
        'execution_time': execution_time,
        'generated_at': now.strftime('%B %d, %Y'),
        'generated_at_full': now.strftime('%Y-%m-%d %H:%M UTC'),
        'top_opportunity': top_opportunity,
        'top_3_opportunities': top_3_opportunities,
        'top_5_opportunities': top_5_opportunities,
        'remaining_opportunities': remaining_opportunities,
        'opportunities': opportunities,
        'evidence_by_source': evidence_by_source,
        'synthesis_summary': synthesis_summary,
        'full_report_extensions': full_report_extensions,
        'total_pages': total_pages,
        'page_number': total_pages - 1,  # For evidence catalog page
    }
