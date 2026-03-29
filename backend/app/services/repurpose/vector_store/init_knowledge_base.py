"""
Initialize the Knowledge Base with pharmaceutical documents.
Run this script to populate the vector database with foundational knowledge.
"""

import logging
from typing import List, Dict

from .knowledge_base import KnowledgeBase, get_knowledge_base

logger = logging.getLogger(__name__)

# ============================================================================
# DRUG MECHANISMS - How drugs work at the molecular level
# ============================================================================

DRUG_MECHANISMS = [
    {
        "text": "Metformin primarily works by inhibiting hepatic gluconeogenesis through activation of AMP-activated protein kinase (AMPK). This reduces glucose production in the liver and improves insulin sensitivity in peripheral tissues. Recent research suggests metformin may also have anti-aging and anti-cancer properties through its effects on cellular metabolism and the mTOR pathway.",
        "metadata": {"drug": "metformin", "category": "mechanism", "source": "pharmacology"}
    },
    {
        "text": "Aspirin (acetylsalicylic acid) irreversibly inhibits cyclooxygenase enzymes (COX-1 and COX-2), preventing the synthesis of prostaglandins and thromboxanes. Low-dose aspirin preferentially inhibits platelet COX-1, reducing thromboxane A2 production and providing antiplatelet effects useful in cardiovascular prevention.",
        "metadata": {"drug": "aspirin", "category": "mechanism", "source": "pharmacology"}
    },
    {
        "text": "Sildenafil inhibits phosphodiesterase type 5 (PDE5), which degrades cyclic GMP. By preventing cGMP breakdown, sildenafil enhances nitric oxide signaling, causing smooth muscle relaxation and vasodilation. Originally developed for angina, this mechanism proved more effective for erectile dysfunction and later pulmonary arterial hypertension.",
        "metadata": {"drug": "sildenafil", "category": "mechanism", "source": "pharmacology"}
    },
    {
        "text": "Thalidomide has multiple mechanisms including anti-angiogenic effects through inhibition of VEGF and bFGF, immunomodulatory effects through TNF-alpha inhibition, and direct anti-myeloma activity. The drug binds to cereblon (CRBN), a component of the E3 ubiquitin ligase complex, leading to degradation of specific proteins.",
        "metadata": {"drug": "thalidomide", "category": "mechanism", "source": "pharmacology"}
    },
    {
        "text": "Rapamycin (Sirolimus) inhibits the mechanistic target of rapamycin (mTOR), a key regulator of cell growth, proliferation, and survival. mTOR inhibition affects protein synthesis, autophagy, and metabolism. This mechanism makes rapamycin relevant for immunosuppression, cancer treatment, and potentially longevity research.",
        "metadata": {"drug": "rapamycin", "category": "mechanism", "source": "pharmacology"}
    },
    {
        "text": "Ibuprofen is a non-selective COX inhibitor that reduces prostaglandin synthesis, providing anti-inflammatory, analgesic, and antipyretic effects. Unlike aspirin, its COX inhibition is reversible. Recent studies suggest potential neuroprotective effects through modulation of neuroinflammation in Alzheimer's disease.",
        "metadata": {"drug": "ibuprofen", "category": "mechanism", "source": "pharmacology"}
    },
    {
        "text": "Statins (HMG-CoA reductase inhibitors) block cholesterol synthesis by inhibiting the rate-limiting enzyme in the mevalonate pathway. Beyond lipid-lowering, statins have pleiotropic effects including anti-inflammatory actions, endothelial function improvement, and antioxidant properties that may benefit various conditions.",
        "metadata": {"drug": "statins", "category": "mechanism", "source": "pharmacology"}
    },
    {
        "text": "Valproic acid has multiple mechanisms: it increases GABA levels by inhibiting GABA transaminase, blocks voltage-gated sodium channels, and inhibits histone deacetylases (HDACs). The HDAC inhibition has led to investigation in cancer and neurodegenerative diseases as an epigenetic modifier.",
        "metadata": {"drug": "valproic_acid", "category": "mechanism", "source": "pharmacology"}
    },
]

# ============================================================================
# DISEASE PATHWAYS - Understanding disease mechanisms
# ============================================================================

DISEASE_PATHWAYS = [
    {
        "text": "Cancer cells often exhibit the Warburg effect, preferring glycolysis over oxidative phosphorylation even in the presence of oxygen. This metabolic reprogramming supports rapid proliferation and provides targets for drugs that modulate glucose metabolism, such as metformin which activates AMPK and reduces cellular energy status.",
        "metadata": {"disease": "cancer", "pathway": "metabolism", "source": "oncology"}
    },
    {
        "text": "Alzheimer's disease pathology involves amyloid-beta plaques, tau tangles, and neuroinflammation. The inflammatory component involves activated microglia and elevated cytokines, suggesting that anti-inflammatory drugs might slow disease progression. NSAIDs have been investigated but clinical trials show mixed results.",
        "metadata": {"disease": "alzheimer", "pathway": "neuroinflammation", "source": "neurology"}
    },
    {
        "text": "Type 2 diabetes involves insulin resistance, beta-cell dysfunction, and chronic low-grade inflammation. The condition increases risk for cardiovascular disease, kidney disease, and certain cancers. Drugs targeting insulin sensitivity, like metformin and thiazolidinediones, address core pathophysiology.",
        "metadata": {"disease": "diabetes", "pathway": "metabolism", "source": "endocrinology"}
    },
    {
        "text": "Pulmonary arterial hypertension (PAH) involves endothelial dysfunction, smooth muscle proliferation, and vasoconstriction in pulmonary arteries. The nitric oxide-cGMP pathway is impaired, making PDE5 inhibitors like sildenafil effective by enhancing remaining NO signaling.",
        "metadata": {"disease": "pulmonary_hypertension", "pathway": "vascular", "source": "cardiology"}
    },
    {
        "text": "Multiple myeloma depends on the bone marrow microenvironment and involves dysregulated protein homeostasis. Immunomodulatory drugs like thalidomide and lenalidomide work through cereblon-mediated protein degradation, anti-angiogenesis, and immune system modulation.",
        "metadata": {"disease": "multiple_myeloma", "pathway": "immune", "source": "oncology"}
    },
    {
        "text": "Inflammatory bowel disease (IBD) involves dysregulated immune responses to gut microbiota. TNF-alpha plays a central role in inflammation, making TNF inhibitors effective treatments. Other pathways including IL-23/IL-17 and JAK-STAT are also therapeutic targets.",
        "metadata": {"disease": "ibd", "pathway": "inflammation", "source": "gastroenterology"}
    },
    {
        "text": "Parkinson's disease is characterized by loss of dopaminergic neurons in the substantia nigra and accumulation of alpha-synuclein. Mitochondrial dysfunction, oxidative stress, and neuroinflammation contribute to pathogenesis. Drugs enhancing mitochondrial function or reducing inflammation are being investigated.",
        "metadata": {"disease": "parkinson", "pathway": "neurodegeneration", "source": "neurology"}
    },
    {
        "text": "Heart failure involves neurohormonal activation (RAAS, sympathetic nervous system), cardiac remodeling, and impaired contractility. SGLT2 inhibitors, originally for diabetes, have shown remarkable benefits in heart failure through mechanisms including improved cardiac metabolism and reduced preload.",
        "metadata": {"disease": "heart_failure", "pathway": "cardiac", "source": "cardiology"}
    },
]

# ============================================================================
# CLINICAL GUIDELINES - Treatment standards and recommendations
# ============================================================================

CLINICAL_GUIDELINES = [
    {
        "text": "FDA guidance on drug repurposing: Existing drugs with established safety profiles may qualify for expedited approval pathways (505(b)(2)) when evidence supports new indications. Phase 2 trials may be sufficient if mechanistic rationale is strong and safety is well-characterized.",
        "metadata": {"type": "regulatory", "agency": "FDA", "source": "guidelines"}
    },
    {
        "text": "Evidence levels for drug repurposing: Level 1 evidence requires randomized controlled trials. Level 2 includes well-designed cohort studies. Retrospective analyses and case reports provide hypothesis-generating data but require prospective validation before clinical adoption.",
        "metadata": {"type": "evidence", "category": "methodology", "source": "guidelines"}
    },
    {
        "text": "Off-label prescribing considerations: Physicians may prescribe approved drugs for unapproved indications when evidence supports benefit, standard treatments have failed, and patients are informed of the off-label status. Documentation and monitoring are essential.",
        "metadata": {"type": "clinical", "category": "prescribing", "source": "guidelines"}
    },
    {
        "text": "Drug repurposing for rare diseases: Orphan Drug Act incentives apply to repurposed drugs for rare diseases (affecting <200,000 patients in US). Seven years of market exclusivity and tax credits may offset development costs for new indications.",
        "metadata": {"type": "regulatory", "category": "orphan", "source": "guidelines"}
    },
    {
        "text": "Clinical trial design for repurposed drugs: Adaptive trial designs can efficiently test multiple doses or patient populations. Basket trials testing a drug across multiple cancer types sharing a molecular target have proven valuable for repurposing investigations.",
        "metadata": {"type": "clinical", "category": "trials", "source": "guidelines"}
    },
]

# ============================================================================
# DRUG INTERACTIONS - Important safety considerations
# ============================================================================

DRUG_INTERACTIONS = [
    {
        "text": "Metformin and iodinated contrast agents: Metformin should be temporarily discontinued before contrast procedures in patients with renal impairment due to risk of contrast-induced nephropathy leading to lactic acidosis. Resume 48 hours after procedure if renal function is stable.",
        "metadata": {"drug": "metformin", "interaction_type": "procedural", "severity": "major"}
    },
    {
        "text": "Aspirin and other NSAIDs: Concurrent use with other NSAIDs increases gastrointestinal bleeding risk. Ibuprofen may interfere with aspirin's antiplatelet effect if taken before aspirin - take aspirin at least 30 minutes before ibuprofen.",
        "metadata": {"drug": "aspirin", "interaction_type": "pharmacodynamic", "severity": "moderate"}
    },
    {
        "text": "Sildenafil and nitrates: Concurrent use is contraindicated due to risk of severe hypotension. PDE5 inhibitors potentiate the hypotensive effects of nitric oxide donors. Wait at least 24-48 hours after sildenafil before administering nitrates.",
        "metadata": {"drug": "sildenafil", "interaction_type": "pharmacodynamic", "severity": "major"}
    },
    {
        "text": "Thalidomide and CNS depressants: Enhanced sedation with benzodiazepines, opioids, and alcohol. Increased risk of deep vein thrombosis when combined with other agents that increase clotting risk. Anticoagulation prophylaxis recommended.",
        "metadata": {"drug": "thalidomide", "interaction_type": "pharmacodynamic", "severity": "moderate"}
    },
    {
        "text": "Statins and CYP3A4 inhibitors: Strong CYP3A4 inhibitors (clarithromycin, itraconazole, HIV protease inhibitors) increase statin levels, particularly simvastatin and lovastatin. Use lowest statin dose or switch to pravastatin/rosuvastatin which are less affected.",
        "metadata": {"drug": "statins", "interaction_type": "pharmacokinetic", "severity": "major"}
    },
]

# ============================================================================
# SUCCESSFUL REPURPOSING CASES - Historical examples
# ============================================================================

REPURPOSING_CASES = [
    {
        "text": "Sildenafil repurposing success: Originally developed by Pfizer for angina, clinical trials showed modest cardiovascular effects but notable improvement in erectile function. Approved for erectile dysfunction in 1998, later approved for pulmonary arterial hypertension in 2005. Revenue exceeded $1 billion annually.",
        "metadata": {"drug": "sildenafil", "original": "angina", "repurposed": "erectile_dysfunction", "outcome": "approved"}
    },
    {
        "text": "Thalidomide repurposing: After withdrawal due to teratogenicity in the 1960s, thalidomide was found effective for erythema nodosum leprosum. Later discovered to have anti-myeloma activity, leading to FDA approval for multiple myeloma in 2006. Strict REMS program manages teratogenic risk.",
        "metadata": {"drug": "thalidomide", "original": "sedative", "repurposed": "multiple_myeloma", "outcome": "approved"}
    },
    {
        "text": "Metformin cancer investigation: Epidemiological studies showed diabetic patients on metformin had lower cancer incidence. Preclinical studies demonstrated anti-proliferative effects via AMPK activation and mTOR inhibition. Multiple clinical trials ongoing for breast, prostate, and colorectal cancer.",
        "metadata": {"drug": "metformin", "original": "diabetes", "repurposed": "cancer", "outcome": "under_investigation"}
    },
    {
        "text": "Aspirin cardiovascular prevention: Originally an analgesic, low-dose aspirin's antiplatelet effects led to repurposing for secondary cardiovascular prevention. Primary prevention benefits are more modest and must be weighed against bleeding risk.",
        "metadata": {"drug": "aspirin", "original": "pain", "repurposed": "cardiovascular_prevention", "outcome": "approved"}
    },
    {
        "text": "Minoxidil for hair loss: Developed as an antihypertensive, patients noticed hair growth as a side effect. Reformulated as a topical solution and approved for androgenetic alopecia in 1988. Demonstrates how adverse effects can reveal new therapeutic applications.",
        "metadata": {"drug": "minoxidil", "original": "hypertension", "repurposed": "hair_loss", "outcome": "approved"}
    },
    {
        "text": "Rituximab expansion: Originally approved for B-cell non-Hodgkin lymphoma, rituximab's CD20-targeting mechanism proved valuable in autoimmune diseases. Now approved for rheumatoid arthritis, granulomatosis with polyangiitis, and chronic lymphocytic leukemia.",
        "metadata": {"drug": "rituximab", "original": "lymphoma", "repurposed": "autoimmune_diseases", "outcome": "approved"}
    },
    {
        "text": "Gabapentin for neuropathic pain: Developed as an anticonvulsant, gabapentin showed efficacy in postherpetic neuralgia and diabetic neuropathy clinical trials. The GABA-mimetic mechanism provides analgesia independent of seizure control. Widely used off-label for various pain conditions.",
        "metadata": {"drug": "gabapentin", "original": "epilepsy", "repurposed": "neuropathic_pain", "outcome": "approved"}
    },
    {
        "text": "SGLT2 inhibitors heart failure breakthrough: Empagliflozin and dapagliflozin, developed for type 2 diabetes, showed unexpected cardiovascular benefits including heart failure hospitalization reduction. Now approved for heart failure regardless of diabetes status, representing a major therapeutic advance.",
        "metadata": {"drug": "sglt2_inhibitors", "original": "diabetes", "repurposed": "heart_failure", "outcome": "approved"}
    },
]


def populate_knowledge_base(kb: KnowledgeBase = None) -> Dict[str, int]:
    """
    Populate the knowledge base with pharmaceutical documents.

    Args:
        kb: KnowledgeBase instance (uses singleton if None)

    Returns:
        Dict with document counts per collection
    """
    if kb is None:
        kb = get_knowledge_base()

    results = {}

    # Add drug mechanisms
    docs = [item["text"] for item in DRUG_MECHANISMS]
    metas = [item["metadata"] for item in DRUG_MECHANISMS]
    kb.add_documents("drug_mechanisms", docs, metas)
    results["drug_mechanisms"] = len(docs)

    # Add disease pathways
    docs = [item["text"] for item in DISEASE_PATHWAYS]
    metas = [item["metadata"] for item in DISEASE_PATHWAYS]
    kb.add_documents("disease_pathways", docs, metas)
    results["disease_pathways"] = len(docs)

    # Add clinical guidelines
    docs = [item["text"] for item in CLINICAL_GUIDELINES]
    metas = [item["metadata"] for item in CLINICAL_GUIDELINES]
    kb.add_documents("clinical_guidelines", docs, metas)
    results["clinical_guidelines"] = len(docs)

    # Add drug interactions
    docs = [item["text"] for item in DRUG_INTERACTIONS]
    metas = [item["metadata"] for item in DRUG_INTERACTIONS]
    kb.add_documents("drug_interactions", docs, metas)
    results["drug_interactions"] = len(docs)

    # Add repurposing cases
    docs = [item["text"] for item in REPURPOSING_CASES]
    metas = [item["metadata"] for item in REPURPOSING_CASES]
    kb.add_documents("repurposing_cases", docs, metas)
    results["repurposing_cases"] = len(docs)

    total = sum(results.values())
    logger.info(f"Knowledge base populated with {total} documents")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = populate_knowledge_base()
    print("Knowledge base initialized:")
    for collection, count in results.items():
        print(f"  - {collection}: {count} documents")
