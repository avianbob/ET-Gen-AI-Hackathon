"""
Internal Agent - Simulates proprietary R&D database for demonstration purposes.
Returns mock internal research data to showcase enterprise capability.
"""

from typing import Dict, List, Any
import asyncio
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem


class InternalAgent(BaseAgent):
    """Agent for simulating internal proprietary data."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

        # Mock internal database - maps drug names to internal research data
        # Comprehensive database of 50+ drugs with repurposing potential
        self.internal_database = {
            # Original entries
            "metformin": {
                "indications": ["Longevity", "Cancer Prevention", "Neuroprotection"],
                "notes": [
                    "Phase 1 longevity trial showing promising AMPK activation (Q3 2024)",
                    "Safety profile excellent for cardiovascular patients - 5-year study confirms",
                    "Research team hypothesis: anti-cancer properties via metabolic pathway modulation"
                ],
                "priority": "high"
            },
            "aspirin": {
                "indications": ["Colorectal Cancer Prevention", "Alzheimer's Prevention"],
                "notes": [
                    "Meta-analysis of internal trials shows 20% reduction in colorectal cancer risk",
                    "Preliminary data suggests anti-inflammatory effects may slow cognitive decline",
                    "Long-term safety monitoring ongoing for low-dose regimens"
                ],
                "priority": "medium"
            },
            "ibuprofen": {
                "indications": ["Alzheimer's Prevention", "Parkinson's Disease"],
                "notes": [
                    "Epidemiological data suggests reduced AD risk with long-term use",
                    "Neuroprotective mechanisms under investigation in animal models",
                    "Clinical trial planning for preventive use in at-risk populations"
                ],
                "priority": "medium"
            },
            "sildenafil": {
                "indications": ["Pulmonary Hypertension", "Raynaud's Phenomenon", "Alzheimer's Disease"],
                "notes": [
                    "Already approved for pulmonary arterial hypertension - expanding indications",
                    "Phase 2 trial for Raynaud's shows improvement in digital blood flow",
                    "Recent studies show 69% reduced Alzheimer's risk - mechanism under investigation"
                ],
                "priority": "high"
            },
            "thalidomide": {
                "indications": ["Multiple Myeloma", "Leprosy"],
                "notes": [
                    "Successful redemption story - now key treatment for multiple myeloma",
                    "Strict REMS program in place due to teratogenicity",
                    "Exploring immunomodulatory effects for other hematologic malignancies"
                ],
                "priority": "high"
            },
            "rapamycin": {
                "indications": ["Longevity", "Age-related Diseases"],
                "notes": [
                    "mTOR inhibition shows life-extension in multiple animal models",
                    "Internal aging research program investigating optimal dosing for humans",
                    "Preliminary data on cognitive benefits in older adults"
                ],
                "priority": "high"
            },
            "hydroxychloroquine": {
                "indications": ["Lupus", "Rheumatoid Arthritis"],
                "notes": [
                    "Well-established for autoimmune conditions with good safety profile",
                    "Investigating combination therapies for refractory cases",
                    "Long-term retinal monitoring protocols optimized"
                ],
                "priority": "medium"
            },
            "tamoxifen": {
                "indications": ["Breast Cancer Prevention", "Bipolar Disorder"],
                "notes": [
                    "Proven efficacy in breast cancer - exploring psychiatric applications",
                    "Small pilot study suggests mood-stabilizing effects",
                    "Mechanism may involve estrogen modulation in brain"
                ],
                "priority": "low"
            },
            "valproic acid": {
                "indications": ["Cancer", "HIV Latency Reversal"],
                "notes": [
                    "HDAC inhibitor properties suggest anti-cancer potential",
                    "Preclinical data for glioblastoma combination therapy",
                    "HIV cure research exploring latency reversal mechanisms"
                ],
                "priority": "medium"
            },
            "ketoconazole": {
                "indications": ["Prostate Cancer", "Cushing's Syndrome"],
                "notes": [
                    "Anti-androgen effects useful in castration-resistant prostate cancer",
                    "Steroid synthesis inhibition for hypercortisolism",
                    "Monitoring liver function essential with prolonged use"
                ],
                "priority": "medium"
            },
            # Statins
            "atorvastatin": {
                "indications": ["Cancer Prevention", "Multiple Sclerosis", "Sepsis"],
                "notes": [
                    "Pleiotropic effects beyond cholesterol reduction show anti-cancer potential",
                    "Immunomodulatory properties being explored for MS treatment",
                    "Sepsis trials show reduced mortality in preliminary data"
                ],
                "priority": "high"
            },
            "simvastatin": {
                "indications": ["Breast Cancer", "Parkinson's Disease", "COPD"],
                "notes": [
                    "Anti-proliferative effects observed in breast cancer cell lines",
                    "Neuroprotective mechanisms via cholesterol pathway modulation",
                    "Anti-inflammatory effects may benefit COPD patients"
                ],
                "priority": "medium"
            },
            "rosuvastatin": {
                "indications": ["Heart Failure", "Venous Thromboembolism"],
                "notes": [
                    "JUPITER trial showed cardiovascular benefits beyond LDL reduction",
                    "Investigating endothelial function improvement mechanisms",
                    "VTE prevention trials showing promising preliminary results"
                ],
                "priority": "medium"
            },
            # Antidepressants
            "fluoxetine": {
                "indications": ["Stroke Recovery", "Cancer", "Obesity"],
                "notes": [
                    "FLAME trial showed improved motor recovery post-stroke",
                    "Anti-proliferative effects in various cancer models",
                    "Appetite suppression effects being studied for weight management"
                ],
                "priority": "medium"
            },
            "sertraline": {
                "indications": ["Cardiovascular Disease", "Cancer"],
                "notes": [
                    "SADHART trial showed safety in cardiac patients",
                    "Platelet function effects may reduce thrombosis risk",
                    "Anti-cancer properties in preclinical studies"
                ],
                "priority": "low"
            },
            "amitriptyline": {
                "indications": ["Fibromyalgia", "Irritable Bowel Syndrome", "Chronic Pain"],
                "notes": [
                    "Well-established off-label use for chronic pain conditions",
                    "Mechanism involves serotonin/norepinephrine modulation",
                    "Low-dose regimens show good tolerability"
                ],
                "priority": "medium"
            },
            # Beta-blockers
            "propranolol": {
                "indications": ["Infantile Hemangioma", "Anxiety Disorders", "Cancer Metastasis"],
                "notes": [
                    "Now first-line for infantile hemangioma - successful repurposing",
                    "Beta-adrenergic blockade reduces cancer cell migration in models",
                    "PTSD treatment trials ongoing with promising results"
                ],
                "priority": "high"
            },
            "metoprolol": {
                "indications": ["Heart Failure", "Migraine Prevention"],
                "notes": [
                    "Well-established for heart failure with reduced ejection fraction",
                    "Effective migraine prophylaxis in clinical trials",
                    "Good safety profile for long-term use"
                ],
                "priority": "medium"
            },
            "atenolol": {
                "indications": ["Marfan Syndrome", "Hyperthyroidism"],
                "notes": [
                    "Aortic root protection in Marfan syndrome patients",
                    "Symptom control in thyroid storm situations",
                    "Long-term cardiovascular outcomes being studied"
                ],
                "priority": "low"
            },
            # Antibiotics with repurposing potential
            "doxycycline": {
                "indications": ["Cancer", "Malaria Prevention", "Periodontal Disease"],
                "notes": [
                    "MMP inhibition shows anti-metastatic potential",
                    "Sub-antimicrobial doses effective for rosacea",
                    "Anti-angiogenic properties being explored"
                ],
                "priority": "medium"
            },
            "azithromycin": {
                "indications": ["COPD Exacerbations", "Cystic Fibrosis", "Malaria"],
                "notes": [
                    "Long-term low-dose reduces COPD exacerbations",
                    "Anti-inflammatory effects benefit CF patients",
                    "Combination therapy potential for malaria"
                ],
                "priority": "medium"
            },
            "minocycline": {
                "indications": ["Schizophrenia", "Stroke", "Rheumatoid Arthritis"],
                "notes": [
                    "Neuroprotective and anti-inflammatory effects observed",
                    "Adjunctive therapy trials for schizophrenia ongoing",
                    "Microglial modulation may explain neurological benefits"
                ],
                "priority": "medium"
            },
            # Pain medications
            "naproxen": {
                "indications": ["Alzheimer's Prevention", "Colorectal Cancer Prevention"],
                "notes": [
                    "ADAPT trial explored AD prevention - complex results",
                    "COX-2 inhibition may reduce polyp formation",
                    "Cardiovascular safety better than some other NSAIDs"
                ],
                "priority": "low"
            },
            "celecoxib": {
                "indications": ["Colon Cancer Prevention", "Bipolar Disorder"],
                "notes": [
                    "FAP patients show reduced polyp burden",
                    "Anti-inflammatory effects explored for mood disorders",
                    "Cardiovascular monitoring essential"
                ],
                "priority": "medium"
            },
            "gabapentin": {
                "indications": ["Hot Flashes", "Alcohol Dependence", "Restless Leg Syndrome"],
                "notes": [
                    "Effective for menopausal symptoms when HRT contraindicated",
                    "Reduces alcohol craving in preliminary studies",
                    "First-line for RLS treatment"
                ],
                "priority": "medium"
            },
            # Antipsychotics
            "haloperidol": {
                "indications": ["Delirium", "Intractable Hiccups", "Cancer Pain"],
                "notes": [
                    "ICU delirium management - ongoing MIND-USA trials",
                    "Dopamine blockade effective for persistent hiccups",
                    "Adjuvant analgesic in palliative care"
                ],
                "priority": "low"
            },
            "olanzapine": {
                "indications": ["Chemotherapy-Induced Nausea", "Anorexia Nervosa"],
                "notes": [
                    "Highly effective antiemetic for chemotherapy patients",
                    "Weight gain side effect beneficial in anorexia",
                    "5-HT3 and dopamine receptor effects explain efficacy"
                ],
                "priority": "medium"
            },
            "risperidone": {
                "indications": ["Autism-Related Irritability", "Tourette Syndrome"],
                "notes": [
                    "FDA-approved for irritability in autism",
                    "Effective for tic suppression in Tourette's",
                    "Metabolic monitoring required"
                ],
                "priority": "medium"
            },
            # Antivirals
            "acyclovir": {
                "indications": ["Alzheimer's Disease", "Bell's Palsy"],
                "notes": [
                    "HSV hypothesis for AD being tested in clinical trials",
                    "Combined with steroids for Bell's palsy treatment",
                    "Long-term safety well established"
                ],
                "priority": "medium"
            },
            "ribavirin": {
                "indications": ["RSV Infection", "Hemorrhagic Fevers"],
                "notes": [
                    "Aerosolized form for severe RSV in immunocompromised",
                    "Lassa fever treatment in endemic regions",
                    "Broad-spectrum antiviral mechanism"
                ],
                "priority": "low"
            },
            "amantadine": {
                "indications": ["Parkinson's Disease", "Traumatic Brain Injury", "Fatigue in MS"],
                "notes": [
                    "Dopaminergic effects useful for PD motor symptoms",
                    "TBI recovery acceleration in clinical studies",
                    "Multiple sclerosis fatigue reduction observed"
                ],
                "priority": "medium"
            },
            # Diabetes drugs
            "pioglitazone": {
                "indications": ["NASH", "Alzheimer's Disease", "Polycystic Ovary Syndrome"],
                "notes": [
                    "Insulin sensitization improves liver histology in NASH",
                    "PPARγ activation may reduce amyloid burden",
                    "Metabolic benefits in PCOS patients"
                ],
                "priority": "high"
            },
            "sitagliptin": {
                "indications": ["Cardiovascular Protection", "NASH"],
                "notes": [
                    "DPP-4 inhibition may have cardioprotective effects",
                    "Incretin effects being studied for liver fat reduction",
                    "Weight-neutral glucose control"
                ],
                "priority": "low"
            },
            # Cardiac drugs
            "digoxin": {
                "indications": ["Cancer", "Atrial Fibrillation with Heart Failure"],
                "notes": [
                    "Cardiac glycosides show anti-cancer effects in vitro",
                    "Mechanism involves Na+/K+-ATPase and HIF-1α inhibition",
                    "Narrow therapeutic index requires careful monitoring"
                ],
                "priority": "medium"
            },
            "amiodarone": {
                "indications": ["Thyroid Dysfunction", "Ventricular Arrhythmias"],
                "notes": [
                    "Iodine content affects thyroid function - both hyper and hypo",
                    "Most effective antiarrhythmic for life-threatening VT",
                    "Multiple organ toxicity monitoring essential"
                ],
                "priority": "low"
            },
            "verapamil": {
                "indications": ["Diabetes", "Cluster Headaches", "Hypertrophic Cardiomyopathy"],
                "notes": [
                    "Beta cell protection observed in type 1 diabetes studies",
                    "First-line prophylaxis for cluster headaches",
                    "Reduces outflow obstruction in HCM"
                ],
                "priority": "medium"
            },
            # GI drugs
            "omeprazole": {
                "indications": ["Cancer Prevention", "Antifungal Potentiation"],
                "notes": [
                    "Proton pump inhibition may affect tumor microenvironment",
                    "Enhances antifungal drug activity in resistant infections",
                    "Long-term use concerns with bone density"
                ],
                "priority": "low"
            },
            "famotidine": {
                "indications": ["COVID-19", "Allergic Reactions"],
                "notes": [
                    "Observational data suggested COVID-19 benefit - studies ongoing",
                    "H2 receptor blockade adjunct for anaphylaxis",
                    "Good safety profile for OTC use"
                ],
                "priority": "low"
            },
            "metoclopramide": {
                "indications": ["Gastroparesis", "Migraine", "Hiccups"],
                "notes": [
                    "Prokinetic effects useful for diabetic gastroparesis",
                    "Adjunct therapy for acute migraine treatment",
                    "Movement disorder risk with chronic use"
                ],
                "priority": "low"
            },
            # Immunosuppressants
            "cyclosporine": {
                "indications": ["Dry Eye Disease", "Ulcerative Colitis", "Psoriasis"],
                "notes": [
                    "Topical formulation (Restasis) for chronic dry eye",
                    "Rescue therapy for severe UC flares",
                    "Calcineurin inhibition effective in autoimmune conditions"
                ],
                "priority": "medium"
            },
            "mycophenolate": {
                "indications": ["Lupus Nephritis", "Myasthenia Gravis"],
                "notes": [
                    "Non-inferior to cyclophosphamide for lupus nephritis induction",
                    "Steroid-sparing agent for myasthenia gravis",
                    "Teratogenicity requires strict contraception"
                ],
                "priority": "medium"
            },
            "azathioprine": {
                "indications": ["Inflammatory Bowel Disease", "Multiple Sclerosis"],
                "notes": [
                    "Maintenance therapy for Crohn's and UC",
                    "Historical use in MS before newer agents",
                    "TPMT testing recommended before initiation"
                ],
                "priority": "low"
            },
            # Cancer drugs repurposed
            "dasatinib": {
                "indications": ["Pulmonary Arterial Hypertension", "Alzheimer's Disease"],
                "notes": [
                    "Src family kinase inhibition may benefit PAH",
                    "Senolytic properties being explored for aging",
                    "Currently in clinical trials for AD"
                ],
                "priority": "high"
            },
            "sorafenib": {
                "indications": ["Hepatocellular Carcinoma", "Thyroid Cancer"],
                "notes": [
                    "Multi-kinase inhibitor already approved for HCC",
                    "Differentiated thyroid cancer treatment option",
                    "Dermatologic side effects common"
                ],
                "priority": "medium"
            },
            "imatinib": {
                "indications": ["Pulmonary Arterial Hypertension", "Diabetes"],
                "notes": [
                    "PDGF receptor inhibition may benefit PAH",
                    "Case reports of diabetes remission during treatment",
                    "Paradigm-shifting drug in CML treatment"
                ],
                "priority": "high"
            },
            # Other notable repurposing candidates
            "colchicine": {
                "indications": ["Cardiovascular Disease", "Pericarditis", "Behçet's Disease"],
                "notes": [
                    "COLCOT trial showed CV benefit post-MI",
                    "Anti-inflammatory effects reduce pericarditis recurrence",
                    "Narrow therapeutic index requires careful dosing"
                ],
                "priority": "high"
            },
            "allopurinol": {
                "indications": ["Cardiovascular Disease", "Chronic Kidney Disease"],
                "notes": [
                    "Xanthine oxidase inhibition may reduce oxidative stress",
                    "Trials exploring CV benefits beyond gout treatment",
                    "CKD progression potentially slowed"
                ],
                "priority": "medium"
            },
            "minoxidil": {
                "indications": ["Hair Loss", "Heart Failure"],
                "notes": [
                    "Originally developed for hypertension - topical use for alopecia",
                    "Potassium channel opening causes vasodilation",
                    "One of most successful repurposing examples"
                ],
                "priority": "high"
            },
            "finasteride": {
                "indications": ["Prostate Cancer Prevention", "Hair Loss"],
                "notes": [
                    "PCPT trial showed reduced prostate cancer risk",
                    "5-alpha reductase inhibition affects DHT levels",
                    "Sexual side effects limit widespread prevention use"
                ],
                "priority": "medium"
            },
            "lithium": {
                "indications": ["Alzheimer's Disease", "ALS", "Cluster Headaches"],
                "notes": [
                    "GSK-3 inhibition may have neuroprotective effects",
                    "Microdose studies for AD ongoing",
                    "Prophylactic for cluster headaches"
                ],
                "priority": "medium"
            },
            "disulfiram": {
                "indications": ["Cancer", "Lyme Disease", "Cocaine Addiction"],
                "notes": [
                    "ALDH inhibition and copper chelation show anti-cancer effects",
                    "Clinical trials for glioblastoma combination therapy",
                    "Dopamine beta-hydroxylase inhibition for addiction"
                ],
                "priority": "high"
            },
            "niclosamide": {
                "indications": ["Cancer", "Metabolic Disorders", "COVID-19"],
                "notes": [
                    "Wnt pathway inhibition shows broad anti-cancer activity",
                    "AMPK activation and mitochondrial uncoupling effects",
                    "Antiviral activity against multiple viruses"
                ],
                "priority": "high"
            },
            "ivermectin": {
                "indications": ["Scabies", "Rosacea", "River Blindness"],
                "notes": [
                    "Approved for onchocerciasis - Nobel Prize winning discovery",
                    "Topical formulation for rosacea (Soolantra)",
                    "Mass drug administration in endemic regions"
                ],
                "priority": "medium"
            },
            "tretinoin": {
                "indications": ["Acute Promyelocytic Leukemia", "Photoaging"],
                "notes": [
                    "Differentiation therapy revolutionized APL treatment",
                    "Retinoid receptor activation affects gene expression",
                    "Combination with arsenic trioxide highly effective"
                ],
                "priority": "high"
            },
            "losartan": {
                "indications": ["Marfan Syndrome", "Diabetic Nephropathy"],
                "notes": [
                    "TGF-β modulation may protect aorta in Marfan patients",
                    "Renoprotective beyond blood pressure effects",
                    "Well-tolerated ARB with good safety profile"
                ],
                "priority": "medium"
            },
            "spironolactone": {
                "indications": ["Heart Failure", "Acne", "Hair Loss"],
                "notes": [
                    "RALES trial established HF mortality benefit",
                    "Anti-androgen effects useful for hormonal acne",
                    "Female pattern hair loss treatment option"
                ],
                "priority": "medium"
            }
        }

    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch mock internal data.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of internal research records
        """
        # Simulate database query latency
        await asyncio.sleep(0.5)

        drug_name_lower = drug_name.lower().strip()

        # Check if we have internal data for this drug
        if drug_name_lower in self.internal_database:
            data = self.internal_database[drug_name_lower]
            self.logger.info(f"Found internal data for: {drug_name}")

            # Structure data as research records
            records = []
            for i, (indication, note) in enumerate(zip(data["indications"], data["notes"])):
                records.append({
                    "indication": indication,
                    "note": note,
                    "priority": data["priority"],
                    "record_id": f"INT-{drug_name_lower.upper()}-{i+1}",
                    "last_updated": "2024-01-15"
                })

            return records
        else:
            # Return generic placeholder data for any other drug
            self.logger.info(f"No specific internal data for {drug_name}, returning generic data")
            return [
                {
                    "indication": "Under Investigation",
                    "note": f"Internal research ongoing for {drug_name}. No conclusive data yet.",
                    "priority": "low",
                    "record_id": f"INT-GENERIC-001",
                    "last_updated": "2024-01-15"
                }
            ]

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process internal records into evidence items.

        Args:
            raw_data: List of internal research records

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for record in raw_data:
            try:
                record_id = record.get("record_id", "")
                indication = record.get("indication", "Unknown")

                evidence = EvidenceItem(
                    source="internal",
                    indication=indication,
                    summary=record.get("note", ""),
                    date=record.get("last_updated", ""),
                    url=None,  # Internal data - no public URL
                    title=f"Internal Research: {indication}",
                    metadata={
                        "record_id": record_id,
                        "priority": record.get("priority", "low"),
                        "source_type": "proprietary_database",
                        "confidential": True
                    },
                    relevance_score=self._calculate_relevance(record)
                )

                evidence_items.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process internal record: {e}")
                continue

        return evidence_items

    def _calculate_relevance(self, record: Dict[str, Any]) -> float:
        """
        Calculate relevance score for internal record.

        Args:
            record: Internal research record

        Returns:
            Relevance score (0-1)
        """
        # Base score on priority level
        priority = record.get("priority", "low")

        priority_scores = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }

        return priority_scores.get(priority, 0.5)
