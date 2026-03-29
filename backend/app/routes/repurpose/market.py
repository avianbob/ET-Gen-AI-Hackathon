"""
Market Analysis API Routes - Endpoints for market intelligence.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.repurpose.market.market_analyzer import MarketAnalyzer, MarketOpportunity
from app.services.repurpose.market.competitor_tracker import CompetitorTracker, CompetitorInfo, CompetitiveLandscape
from app.services.repurpose.utils.logger import get_logger

router = APIRouter()
logger = get_logger("api.market")


# Request/Response Models
class MarketAnalysisRequest(BaseModel):
    """Request for market analysis."""
    drug_name: str = Field(..., min_length=1, description="Name of the drug")
    indications: List[str] = Field(..., min_items=1, description="List of indications to analyze")
    include_competitors: bool = Field(default=True, description="Include competitor analysis")
    max_indications: int = Field(default=5, le=10, description="Maximum indications to analyze")


class MarketOpportunityResponse(BaseModel):
    """Response for a single market opportunity."""
    indication: str
    drug_name: str
    estimated_market_size_usd: int
    market_size_category: str
    patient_population_global: int
    patient_population_us: int
    cagr_percent: float
    unmet_need_score: float
    existing_treatments_count: int
    average_treatment_cost_usd: int
    potential_price_premium: float
    geographic_hotspots: List[str]
    key_competitors: List[str]
    market_drivers: List[str]
    market_barriers: List[str]
    opportunity_score: float


class CompetitorResponse(BaseModel):
    """Response for competitor analysis."""
    indication: str
    total_competitors: int
    active_trials: int
    companies: List[str]
    phase_distribution: Dict[str, int]
    competitive_intensity: str
    competitive_score: float
    competitors: List[Dict[str, Any]]


class MarketAnalysisResponse(BaseModel):
    """Complete market analysis response."""
    drug_name: str
    analysis_timestamp: str
    market_opportunities: List[MarketOpportunityResponse]
    top_opportunity: Optional[MarketOpportunityResponse]
    total_addressable_market: int
    execution_time: float


@router.post("/market/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(request: MarketAnalysisRequest):
    """
    Analyze market opportunity for drug repurposing indications.

    Args:
        request: MarketAnalysisRequest with drug name and indications

    Returns:
        MarketAnalysisResponse with market analysis for each indication
    """
    import time
    from datetime import datetime

    start_time = time.time()
    logger.info(f"Analyzing market for {request.drug_name} with {len(request.indications)} indications")

    analyzer = MarketAnalyzer()
    competitor_tracker = CompetitorTracker()

    market_opportunities = []
    total_tam = 0

    for indication in request.indications[:request.max_indications]:
        try:
            # Analyze market opportunity
            opportunity = await analyzer.analyze_market(indication, request.drug_name)
            opportunity_score = analyzer.calculate_opportunity_score(opportunity)

            # Get competitor landscape if requested
            if request.include_competitors:
                landscape = await competitor_tracker.get_competitive_landscape(
                    indication,
                    drug_name=request.drug_name
                )
                # Adjust opportunity based on competition
                competitive_score = competitor_tracker.calculate_competitive_score(landscape)
                # Blend market and competitive scores
                adjusted_score = (opportunity_score * 0.6) + (competitive_score * 0.4)
            else:
                adjusted_score = opportunity_score

            market_response = MarketOpportunityResponse(
                indication=opportunity.indication,
                drug_name=opportunity.drug_name,
                estimated_market_size_usd=opportunity.estimated_market_size_usd,
                market_size_category=opportunity.market_size_category.value,
                patient_population_global=opportunity.patient_population_global,
                patient_population_us=opportunity.patient_population_us,
                cagr_percent=opportunity.cagr_percent,
                unmet_need_score=opportunity.unmet_need_score,
                existing_treatments_count=opportunity.existing_treatments_count,
                average_treatment_cost_usd=opportunity.average_treatment_cost_usd,
                potential_price_premium=opportunity.potential_price_premium,
                geographic_hotspots=opportunity.geographic_hotspots,
                key_competitors=opportunity.key_competitors,
                market_drivers=opportunity.market_drivers,
                market_barriers=opportunity.market_barriers,
                opportunity_score=round(adjusted_score, 1)
            )

            market_opportunities.append(market_response)
            total_tam += opportunity.estimated_market_size_usd

        except Exception as e:
            logger.error(f"Failed to analyze market for {indication}: {e}")
            continue

    # Sort by opportunity score
    market_opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)

    execution_time = time.time() - start_time

    return MarketAnalysisResponse(
        drug_name=request.drug_name,
        analysis_timestamp=datetime.now().isoformat(),
        market_opportunities=market_opportunities,
        top_opportunity=market_opportunities[0] if market_opportunities else None,
        total_addressable_market=total_tam,
        execution_time=round(execution_time, 2)
    )


@router.get("/market/competitors/{indication}", response_model=CompetitorResponse)
async def get_competitors(
    indication: str,
    drug_name: Optional[str] = Query(None, description="Drug to exclude from results")
):
    """
    Get competitor analysis for a specific indication.

    Args:
        indication: Disease/indication to analyze
        drug_name: Optional drug to exclude from analysis

    Returns:
        CompetitorResponse with competitive landscape
    """
    logger.info(f"Getting competitors for: {indication}")

    tracker = CompetitorTracker()

    try:
        landscape = await tracker.get_competitive_landscape(indication, drug_name=drug_name)
        competitive_score = tracker.calculate_competitive_score(landscape)

        return CompetitorResponse(
            indication=landscape.indication,
            total_competitors=landscape.total_competitors,
            active_trials=landscape.active_trials,
            companies=landscape.companies,
            phase_distribution=landscape.phase_distribution,
            competitive_intensity=landscape.competitive_intensity,
            competitive_score=round(competitive_score, 1),
            competitors=[c.to_dict() for c in landscape.competitor_details]
        )

    except Exception as e:
        logger.error(f"Failed to get competitors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/size/{indication}")
async def get_market_size(
    indication: str,
    geography: str = Query("global", enum=["global", "us", "eu", "asia"])
):
    """
    Get market size estimation for an indication.

    Args:
        indication: Disease/indication
        geography: Geographic region for estimate

    Returns:
        Market size information
    """
    logger.info(f"Getting market size for: {indication} ({geography})")

    analyzer = MarketAnalyzer()

    try:
        opportunity = await analyzer.analyze_market(indication)

        # Adjust for geography
        if geography == "us":
            multiplier = 0.45  # US is ~45% of global pharma market
        elif geography == "eu":
            multiplier = 0.25  # EU is ~25%
        elif geography == "asia":
            multiplier = 0.20  # Asia-Pacific is ~20%
        else:
            multiplier = 1.0

        return {
            "indication": indication,
            "geography": geography,
            "estimated_market_size_usd": int(opportunity.estimated_market_size_usd * multiplier),
            "market_size_category": opportunity.market_size_category.value,
            "patient_population": int(opportunity.patient_population_global * multiplier) if geography != "us" else opportunity.patient_population_us,
            "cagr_percent": opportunity.cagr_percent,
            "data_sources": ["WHO Global Health Observatory", "Industry Reports", "Published Research"]
        }

    except Exception as e:
        logger.error(f"Failed to get market size: {e}")
        raise HTTPException(status_code=500, detail=str(e))
