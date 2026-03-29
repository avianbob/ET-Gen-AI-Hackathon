"""
Market Segment Analyzer - Identifies specific market segments within indications.

Provides detailed market segment analysis including:
- Specific therapy segments (e.g., "Second-line NSCLC" vs generic "Lung Cancer")
- Patient subpopulation sizes
- Unmet need characterization
- Target patient profiles
"""

from typing import List, Dict, Any, Optional
from app.schemas.repurpose_scoring import MarketSegment
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("market.segment_analyzer")


class MarketSegmentAnalyzer:
    """Identifies specific market segments for drug repurposing opportunities."""

    # Comprehensive segment data for major indications
    SEGMENT_DATA = {
        # Oncology Segments
        "lung cancer": {
            "total_market_billions": 30.0,
            "total_patients": 2200000,
            "segments": [
                {
                    "name": "First-line NSCLC (PD-L1 high)",
                    "share": 20,
                    "patients_percent": 15,
                    "unmet": "moderate",
                    "unmet_desc": "Good response to checkpoint inhibitors but many patients progress",
                    "profile": "Adults with metastatic NSCLC, PD-L1 TPS ≥50%, no EGFR/ALK alterations, ECOG PS 0-1",
                    "differentiators": ["Oral administration preferred", "Lower immunotoxicity", "Combination potential"],
                    "growth": 12.0,
                    "competition": "high",
                },
                {
                    "name": "Second-line NSCLC (post-immunotherapy)",
                    "share": 15,
                    "patients_percent": 25,
                    "unmet": "very_high",
                    "unmet_desc": "Limited options after checkpoint inhibitor failure; most patients progress within 12 months",
                    "profile": "Adults with metastatic NSCLC who progressed on first-line immunotherapy, ECOG PS 0-2",
                    "differentiators": ["Novel mechanism different from PD-1/PD-L1", "Activity in immunotherapy-resistant tumors"],
                    "growth": 18.0,
                    "competition": "medium",
                },
                {
                    "name": "EGFR-mutant NSCLC (resistant)",
                    "share": 12,
                    "patients_percent": 10,
                    "unmet": "high",
                    "unmet_desc": "Osimertinib resistance emerging; C797S and MET amplification common",
                    "profile": "Adults with EGFR+ NSCLC who progressed on third-generation TKIs",
                    "differentiators": ["Activity against C797S mutation", "CNS penetration"],
                    "growth": 15.0,
                    "competition": "high",
                },
                {
                    "name": "Small Cell Lung Cancer (extensive stage)",
                    "share": 8,
                    "patients_percent": 15,
                    "unmet": "very_high",
                    "unmet_desc": "Aggressive disease with poor prognosis; limited treatment advances in decades",
                    "profile": "Adults with extensive-stage SCLC, typically smokers, rapid progression",
                    "differentiators": ["Novel mechanism beyond platinum/etoposide", "Maintenance therapy potential"],
                    "growth": 8.0,
                    "competition": "low",
                },
            ],
        },
        "breast cancer": {
            "total_market_billions": 25.0,
            "total_patients": 2300000,
            "segments": [
                {
                    "name": "HR+/HER2- metastatic (CDK4/6i resistant)",
                    "share": 25,
                    "patients_percent": 30,
                    "unmet": "very_high",
                    "unmet_desc": "Growing population as CDK4/6 inhibitors become standard; limited second-line options",
                    "profile": "Postmenopausal women with HR+/HER2- mBC who progressed on CDK4/6i + endocrine therapy",
                    "differentiators": ["Novel mechanism post-CDK4/6i", "Oral preferred", "Manageable toxicity"],
                    "growth": 20.0,
                    "competition": "medium",
                },
                {
                    "name": "Triple-negative breast cancer (metastatic)",
                    "share": 15,
                    "patients_percent": 15,
                    "unmet": "very_high",
                    "unmet_desc": "Most aggressive subtype; checkpoint inhibitors only work in PD-L1+ subset",
                    "profile": "Adults with metastatic TNBC, often younger patients, rapid progression",
                    "differentiators": ["Activity in PD-L1 negative", "Novel targeted approach", "Combination with chemo"],
                    "growth": 18.0,
                    "competition": "high",
                },
                {
                    "name": "HER2+ metastatic (trastuzumab-resistant)",
                    "share": 12,
                    "patients_percent": 12,
                    "unmet": "high",
                    "unmet_desc": "Multiple HER2 agents available but resistance develops",
                    "profile": "Adults with HER2+ mBC who progressed on trastuzumab-based regimens",
                    "differentiators": ["Novel anti-HER2 mechanism", "Brain metastasis activity"],
                    "growth": 10.0,
                    "competition": "high",
                },
            ],
        },
        "pancreatic cancer": {
            "total_market_billions": 4.0,
            "total_patients": 495000,
            "segments": [
                {
                    "name": "Metastatic pancreatic adenocarcinoma (first-line)",
                    "share": 45,
                    "patients_percent": 55,
                    "unmet": "very_high",
                    "unmet_desc": "5-year survival <10%; FOLFIRINOX and gem/nab-paclitaxel only marginally effective",
                    "profile": "Adults with metastatic PDAC, good performance status (ECOG 0-1)",
                    "differentiators": ["Improvement over FOLFIRINOX", "Better tolerability", "Stromal targeting"],
                    "growth": 15.0,
                    "competition": "low",
                },
                {
                    "name": "Locally advanced unresectable PDAC",
                    "share": 25,
                    "patients_percent": 30,
                    "unmet": "very_high",
                    "unmet_desc": "Borderline resectable cases need effective neoadjuvant; poor conversion rates",
                    "profile": "Adults with locally advanced PDAC not amenable to surgery",
                    "differentiators": ["High response rate for surgical conversion", "Radiosensitization"],
                    "growth": 12.0,
                    "competition": "low",
                },
            ],
        },
        # CNS/Neurology Segments
        "alzheimer": {
            "total_market_billions": 8.0,
            "total_patients": 55000000,
            "segments": [
                {
                    "name": "Early-stage Alzheimer's (MCI due to AD)",
                    "share": 35,
                    "patients_percent": 20,
                    "unmet": "very_high",
                    "unmet_desc": "New anti-amyloid drugs (lecanemab) show modest efficacy; need for disease modification",
                    "profile": "Adults 55-85 with MCI or early AD, amyloid-positive, no significant comorbidities",
                    "differentiators": ["Non-amyloid mechanism", "Better efficacy than lecanemab", "Oral route"],
                    "growth": 25.0,
                    "competition": "medium",
                },
                {
                    "name": "Moderate-to-severe Alzheimer's",
                    "share": 40,
                    "patients_percent": 50,
                    "unmet": "very_high",
                    "unmet_desc": "Only symptomatic treatments; no disease-modifying options for advanced disease",
                    "profile": "Adults with moderate-severe AD, MMSE 10-20, requiring caregiver support",
                    "differentiators": ["Disease modification in advanced stage", "Symptomatic improvement", "Caregiver burden reduction"],
                    "growth": 15.0,
                    "competition": "low",
                },
                {
                    "name": "Alzheimer's-related agitation",
                    "share": 15,
                    "patients_percent": 40,
                    "unmet": "high",
                    "unmet_desc": "Brexpiprazole recently approved but efficacy modest; antipsychotics have black box",
                    "profile": "Adults with AD-related agitation, behavioral symptoms, often in care facilities",
                    "differentiators": ["Better efficacy than brexpiprazole", "Favorable safety vs antipsychotics"],
                    "growth": 20.0,
                    "competition": "medium",
                },
            ],
        },
        "depression": {
            "total_market_billions": 18.0,
            "total_patients": 280000000,
            "segments": [
                {
                    "name": "Treatment-resistant depression (TRD)",
                    "share": 25,
                    "patients_percent": 30,
                    "unmet": "very_high",
                    "unmet_desc": "30% of MDD patients are treatment-resistant; esketamine effective but requires clinic visits",
                    "profile": "Adults with MDD who failed ≥2 adequate antidepressant trials, significant functional impairment",
                    "differentiators": ["Oral/at-home administration", "Novel mechanism", "Rapid onset"],
                    "growth": 18.0,
                    "competition": "medium",
                },
                {
                    "name": "Major depressive disorder with anxious distress",
                    "share": 20,
                    "patients_percent": 50,
                    "unmet": "high",
                    "unmet_desc": "Anxiety comorbidity predicts worse outcomes; SSRIs often inadequate",
                    "profile": "Adults with MDD and prominent anxiety symptoms, often multiple comorbidities",
                    "differentiators": ["Dual efficacy for depression + anxiety", "Rapid anxiolysis"],
                    "growth": 8.0,
                    "competition": "high",
                },
                {
                    "name": "Adolescent depression",
                    "share": 10,
                    "patients_percent": 10,
                    "unmet": "high",
                    "unmet_desc": "Limited approved options; fluoxetine is first-line but many don't respond",
                    "profile": "Adolescents 12-17 with MDD, high suicide risk population",
                    "differentiators": ["Pediatric safety data", "Non-SSRI mechanism", "Anti-suicidal effect"],
                    "growth": 12.0,
                    "competition": "low",
                },
            ],
        },
        "parkinson": {
            "total_market_billions": 6.5,
            "total_patients": 10000000,
            "segments": [
                {
                    "name": "Early Parkinson's (newly diagnosed)",
                    "share": 30,
                    "patients_percent": 25,
                    "unmet": "high",
                    "unmet_desc": "Levodopa remains gold standard but motor fluctuations develop; need for disease modification",
                    "profile": "Adults newly diagnosed with PD, Hoehn & Yahr stage 1-2, good functional status",
                    "differentiators": ["Disease modification/neuroprotection", "Delay of levodopa initiation"],
                    "growth": 10.0,
                    "competition": "medium",
                },
                {
                    "name": "Advanced PD with motor fluctuations",
                    "share": 35,
                    "patients_percent": 40,
                    "unmet": "high",
                    "unmet_desc": "Wearing-off and dyskinesias affect quality of life; continuous delivery options limited",
                    "profile": "Adults with PD >5 years, experiencing motor fluctuations on levodopa",
                    "differentiators": ["Reduced OFF time", "Less dyskinesia", "Oral administration"],
                    "growth": 8.0,
                    "competition": "high",
                },
            ],
        },
        # Metabolic/Endocrine Segments
        "type 2 diabetes": {
            "total_market_billions": 55.0,
            "total_patients": 462000000,
            "segments": [
                {
                    "name": "T2D with established cardiovascular disease",
                    "share": 30,
                    "patients_percent": 25,
                    "unmet": "moderate",
                    "unmet_desc": "GLP-1 RAs and SGLT2i show CV benefit but not all patients tolerate/respond",
                    "profile": "Adults with T2D and prior MI, stroke, or PAD; high CV risk",
                    "differentiators": ["CV mortality reduction", "Oral alternative to GLP-1", "Renal protection"],
                    "growth": 12.0,
                    "competition": "high",
                },
                {
                    "name": "T2D with chronic kidney disease",
                    "share": 20,
                    "patients_percent": 30,
                    "unmet": "high",
                    "unmet_desc": "Many diabetes drugs contraindicated in CKD; SGLT2i have renal benefits but limitations",
                    "profile": "Adults with T2D and CKD stage 3-4, often elderly with multiple comorbidities",
                    "differentiators": ["Safe in advanced CKD", "Renal disease progression slowing"],
                    "growth": 15.0,
                    "competition": "medium",
                },
                {
                    "name": "T2D in obese patients (BMI >35)",
                    "share": 25,
                    "patients_percent": 40,
                    "unmet": "moderate",
                    "unmet_desc": "GLP-1 RAs dominating but supply issues; tirzepatide highly effective",
                    "profile": "Adults with T2D and severe obesity, often metabolic syndrome",
                    "differentiators": ["Weight loss >15%", "Oral alternative to injection", "Better tolerability"],
                    "growth": 20.0,
                    "competition": "high",
                },
            ],
        },
        "obesity": {
            "total_market_billions": 12.0,
            "total_patients": 650000000,
            "segments": [
                {
                    "name": "Severe obesity (BMI ≥40) without diabetes",
                    "share": 30,
                    "patients_percent": 15,
                    "unmet": "high",
                    "unmet_desc": "GLP-1 RAs effective but expensive and injection-based; many don't tolerate GI effects",
                    "profile": "Adults with BMI ≥40 or ≥35 with comorbidities, no T2D, seeking non-surgical option",
                    "differentiators": ["Oral administration", "Better GI tolerability", "Comparable weight loss"],
                    "growth": 25.0,
                    "competition": "medium",
                },
                {
                    "name": "Weight regain post-bariatric surgery",
                    "share": 10,
                    "patients_percent": 20,
                    "unmet": "very_high",
                    "unmet_desc": "30-50% of patients regain significant weight after surgery; limited pharmacologic options",
                    "profile": "Adults who had bariatric surgery 2+ years ago with >15% weight regain",
                    "differentiators": ["Effective post-surgical", "Novel mechanism", "Long-term maintenance"],
                    "growth": 15.0,
                    "competition": "low",
                },
                {
                    "name": "Adolescent obesity",
                    "share": 8,
                    "patients_percent": 10,
                    "unmet": "high",
                    "unmet_desc": "Limited approved options for adolescents; wegovy recently approved 12+",
                    "profile": "Adolescents 12-17 with BMI ≥95th percentile, obesity-related comorbidities",
                    "differentiators": ["Pediatric safety profile", "Oral preferred", "Lifestyle integration"],
                    "growth": 20.0,
                    "competition": "low",
                },
            ],
        },
        "nafld": {
            "total_market_billions": 8.0,
            "total_patients": 1500000000,
            "segments": [
                {
                    "name": "NASH with fibrosis (F2-F3)",
                    "share": 50,
                    "patients_percent": 15,
                    "unmet": "very_high",
                    "unmet_desc": "No approved therapies; resmetirom recently approved but only for F2-F3 with elevated LFTs",
                    "profile": "Adults with biopsy-confirmed NASH and significant fibrosis (F2-F3), not yet cirrhotic",
                    "differentiators": ["Fibrosis regression", "NASH resolution", "Combination potential"],
                    "growth": 30.0,
                    "competition": "medium",
                },
                {
                    "name": "NASH-related compensated cirrhosis",
                    "share": 25,
                    "patients_percent": 5,
                    "unmet": "very_high",
                    "unmet_desc": "No approved options for F4 NASH; high risk of decompensation and HCC",
                    "profile": "Adults with NASH cirrhosis (F4), compensated liver function, awaiting or ineligible for transplant",
                    "differentiators": ["Safety in cirrhosis", "Prevention of decompensation", "HCC risk reduction"],
                    "growth": 20.0,
                    "competition": "low",
                },
            ],
        },
        # Autoimmune/Inflammatory Segments
        "rheumatoid arthritis": {
            "total_market_billions": 28.0,
            "total_patients": 18000000,
            "segments": [
                {
                    "name": "RA inadequate response to TNFi (TNFi-IR)",
                    "share": 25,
                    "patients_percent": 30,
                    "unmet": "moderate",
                    "unmet_desc": "Multiple options (JAKi, IL-6i, T-cell modulators) but many still don't achieve remission",
                    "profile": "Adults with moderate-severe RA who failed 1+ TNF inhibitor",
                    "differentiators": ["Novel mechanism", "Oral preferred", "Higher remission rates"],
                    "growth": 8.0,
                    "competition": "high",
                },
                {
                    "name": "Early RA (DMARD-naive)",
                    "share": 20,
                    "patients_percent": 25,
                    "unmet": "moderate",
                    "unmet_desc": "MTX remains first-line but many need escalation; window of opportunity concept",
                    "profile": "Adults newly diagnosed with RA, seropositive, early disease (<2 years)",
                    "differentiators": ["Better than MTX monotherapy", "Prevent joint damage", "Oral"],
                    "growth": 5.0,
                    "competition": "high",
                },
                {
                    "name": "Difficult-to-treat RA (D2T RA)",
                    "share": 15,
                    "patients_percent": 15,
                    "unmet": "very_high",
                    "unmet_desc": "Failed multiple bDMARDs/tsDMARDs; limited options, often multimorbid",
                    "profile": "Adults with RA who failed ≥2 bDMARDs with different mechanisms",
                    "differentiators": ["Novel mechanism not yet tried", "Activity in refractory disease"],
                    "growth": 10.0,
                    "competition": "low",
                },
            ],
        },
        "psoriasis": {
            "total_market_billions": 15.0,
            "total_patients": 125000000,
            "segments": [
                {
                    "name": "Moderate-severe plaque psoriasis (biologic-naive)",
                    "share": 35,
                    "patients_percent": 40,
                    "unmet": "moderate",
                    "unmet_desc": "IL-17 and IL-23 inhibitors highly effective but injectable; oral options limited",
                    "profile": "Adults with moderate-severe plaque psoriasis (BSA ≥10%), naive to biologics",
                    "differentiators": ["Oral with biologic-like efficacy", "PASI 90+ response"],
                    "growth": 10.0,
                    "competition": "high",
                },
                {
                    "name": "Psoriasis in special populations (elderly, immunocompromised)",
                    "share": 15,
                    "patients_percent": 15,
                    "unmet": "high",
                    "unmet_desc": "Safety concerns with biologics in elderly/immunocompromised; topicals inadequate",
                    "profile": "Adults >65 or with immunocompromising conditions and moderate-severe psoriasis",
                    "differentiators": ["Favorable safety in special populations", "Lower infection risk"],
                    "growth": 8.0,
                    "competition": "low",
                },
            ],
        },
        "pulmonary hypertension": {
            "total_market_billions": 8.5,
            "total_patients": 100000,
            "segments": [
                {
                    "name": "PAH WHO FC II-III (treatment-naive)",
                    "share": 40,
                    "patients_percent": 50,
                    "unmet": "moderate",
                    "unmet_desc": "Triple therapy now standard but complex; need for oral simplification",
                    "profile": "Adults newly diagnosed with PAH, WHO functional class II-III",
                    "differentiators": ["Oral once-daily", "Combination in single pill", "Non-prostacyclin mechanism"],
                    "growth": 8.0,
                    "competition": "medium",
                },
                {
                    "name": "PAH WHO FC IV (refractory)",
                    "share": 20,
                    "patients_percent": 15,
                    "unmet": "very_high",
                    "unmet_desc": "Poor prognosis despite maximal therapy; transplant only option for many",
                    "profile": "Adults with severe PAH (FC IV), failing maximal medical therapy",
                    "differentiators": ["Novel rescue mechanism", "Bridge to transplant efficacy"],
                    "growth": 12.0,
                    "competition": "low",
                },
            ],
        },
        # Infectious Disease Segments
        "hepatitis b": {
            "total_market_billions": 4.0,
            "total_patients": 296000000,
            "segments": [
                {
                    "name": "Chronic HBV seeking functional cure",
                    "share": 60,
                    "patients_percent": 70,
                    "unmet": "very_high",
                    "unmet_desc": "Current antivirals suppress but don't cure; HBsAg loss rare (<5%)",
                    "profile": "Adults with chronic HBV on long-term nucleos(t)ide therapy, HBsAg positive",
                    "differentiators": ["HBsAg loss/seroconversion", "Finite therapy duration", "Immune modulation"],
                    "growth": 15.0,
                    "competition": "medium",
                },
            ],
        },
    }

    # Indication aliases for matching
    INDICATION_ALIASES = {
        "diabetes": "type 2 diabetes",
        "t2d": "type 2 diabetes",
        "type 2 diabetes mellitus": "type 2 diabetes",
        "diabetic": "type 2 diabetes",
        "nsclc": "lung cancer",
        "non-small cell lung cancer": "lung cancer",
        "small cell lung cancer": "lung cancer",
        "sclc": "lung cancer",
        "alzheimer's": "alzheimer",
        "alzheimer's disease": "alzheimer",
        "ad": "alzheimer",
        "dementia": "alzheimer",
        "mdd": "depression",
        "major depressive disorder": "depression",
        "major depression": "depression",
        "parkinson's": "parkinson",
        "parkinson's disease": "parkinson",
        "pd": "parkinson",
        "nash": "nafld",
        "fatty liver": "nafld",
        "nonalcoholic steatohepatitis": "nafld",
        "nonalcoholic fatty liver disease": "nafld",
        "ra": "rheumatoid arthritis",
        "rheumatoid": "rheumatoid arthritis",
        "pah": "pulmonary hypertension",
        "pulmonary arterial hypertension": "pulmonary hypertension",
        "hbv": "hepatitis b",
        "chronic hepatitis b": "hepatitis b",
        "tnbc": "breast cancer",
        "triple negative breast cancer": "breast cancer",
        "her2+ breast cancer": "breast cancer",
        "pdac": "pancreatic cancer",
        "pancreatic adenocarcinoma": "pancreatic cancer",
    }

    def __init__(self):
        """Initialize the market segment analyzer."""
        pass

    def _normalize_indication(self, indication: str) -> str:
        """Normalize indication name to match segment data keys."""
        indication_lower = indication.lower().strip()

        # Check direct match first
        if indication_lower in self.SEGMENT_DATA:
            return indication_lower

        # Check aliases
        if indication_lower in self.INDICATION_ALIASES:
            return self.INDICATION_ALIASES[indication_lower]

        # Partial match
        for key in self.SEGMENT_DATA.keys():
            if key in indication_lower or indication_lower in key:
                return key

        for alias, canonical in self.INDICATION_ALIASES.items():
            if alias in indication_lower or indication_lower in alias:
                return canonical

        return indication_lower

    async def identify_segment(
        self,
        indication: str,
        evidence_items: List[Any] = None,
        drug_characteristics: Dict = None
    ) -> Optional[MarketSegment]:
        """
        Identify the most relevant market segment for an indication.

        Args:
            indication: Disease/indication name
            evidence_items: List of evidence items (for context-aware segment selection)
            drug_characteristics: Drug characteristics (for matching to best segment)

        Returns:
            MarketSegment object or None
        """
        normalized = self._normalize_indication(indication)

        if normalized not in self.SEGMENT_DATA:
            logger.info(f"No segment data for indication: {indication} (normalized: {normalized})")
            return self._create_default_segment(indication)

        indication_data = self.SEGMENT_DATA[normalized]
        segments = indication_data["segments"]

        # Select best segment based on unmet need and competition
        # Prioritize: very_high unmet need, low competition
        best_segment = None
        best_score = -1

        for seg in segments:
            # Score: higher unmet need + lower competition = better opportunity
            unmet_scores = {"very_high": 4, "high": 3, "moderate": 2, "low": 1}
            competition_scores = {"low": 3, "medium": 2, "high": 1}

            score = (
                unmet_scores.get(seg["unmet"], 2) * 2 +
                competition_scores.get(seg["competition"], 2) +
                seg["growth"] / 10
            )

            if score > best_score:
                best_score = score
                best_segment = seg

        if not best_segment:
            return self._create_default_segment(indication)

        # Calculate segment-specific numbers
        total_market = indication_data["total_market_billions"]
        total_patients = indication_data["total_patients"]

        segment_size = total_market * (best_segment["share"] / 100)
        segment_patients = int(total_patients * (best_segment["patients_percent"] / 100))

        return MarketSegment(
            segment_name=best_segment["name"],
            parent_indication=indication.title(),
            segment_size_billions=round(segment_size, 2),
            total_indication_size_billions=total_market,
            segment_share_percent=best_segment["share"],
            patient_subpopulation=segment_patients,
            total_indication_population=total_patients,
            unmet_need_level=best_segment["unmet"],
            unmet_need_description=best_segment["unmet_desc"],
            target_patient_profile=best_segment["profile"],
            key_differentiators=best_segment["differentiators"],
            growth_rate_percent=best_segment["growth"],
            competitive_intensity=best_segment["competition"],
        )

    async def get_all_segments(self, indication: str) -> List[MarketSegment]:
        """
        Get all market segments for an indication.

        Args:
            indication: Disease/indication name

        Returns:
            List of MarketSegment objects
        """
        normalized = self._normalize_indication(indication)

        if normalized not in self.SEGMENT_DATA:
            default = self._create_default_segment(indication)
            return [default] if default else []

        indication_data = self.SEGMENT_DATA[normalized]
        segments = []

        for seg in indication_data["segments"]:
            total_market = indication_data["total_market_billions"]
            total_patients = indication_data["total_patients"]

            segment_size = total_market * (seg["share"] / 100)
            segment_patients = int(total_patients * (seg["patients_percent"] / 100))

            segments.append(MarketSegment(
                segment_name=seg["name"],
                parent_indication=indication.title(),
                segment_size_billions=round(segment_size, 2),
                total_indication_size_billions=total_market,
                segment_share_percent=seg["share"],
                patient_subpopulation=segment_patients,
                total_indication_population=total_patients,
                unmet_need_level=seg["unmet"],
                unmet_need_description=seg["unmet_desc"],
                target_patient_profile=seg["profile"],
                key_differentiators=seg["differentiators"],
                growth_rate_percent=seg["growth"],
                competitive_intensity=seg["competition"],
            ))

        return segments

    def _create_default_segment(self, indication: str) -> Optional[MarketSegment]:
        """Create a default market segment for unknown indications."""
        return MarketSegment(
            segment_name=f"{indication.title()} - General Market",
            parent_indication=indication.title(),
            segment_size_billions=None,
            total_indication_size_billions=None,
            segment_share_percent=100.0,
            patient_subpopulation=None,
            total_indication_population=None,
            unmet_need_level="moderate",
            unmet_need_description="Market segment analysis not available for this indication",
            target_patient_profile="Patients with " + indication.lower(),
            key_differentiators=["Further market research recommended"],
            growth_rate_percent=None,
            competitive_intensity="unknown",
        )


# Singleton instance
_analyzer_instance = None


def get_segment_analyzer() -> MarketSegmentAnalyzer:
    """Get singleton instance of MarketSegmentAnalyzer."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = MarketSegmentAnalyzer()
    return _analyzer_instance
