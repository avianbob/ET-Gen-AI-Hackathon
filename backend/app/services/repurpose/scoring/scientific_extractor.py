"""
Scientific Details Extractor - Extracts detailed scientific data for researchers.

Provides:
- Mechanism of action details
- Target protein and gene information
- Pathway involvement
- Binding affinity data
- Key publications with citations
- Biomarkers
"""

from typing import List, Dict, Any, Optional
from app.schemas.repurpose_scoring import ScientificDetails, KeyPublication
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("scoring.scientific_extractor")


class ScientificDetailsExtractor:
    """Extracts detailed scientific data from evidence items."""

    # Curated mechanism and target data for common drugs
    DRUG_SCIENTIFIC_DATA = {
        "metformin": {
            "mechanism": "Activates AMP-activated protein kinase (AMPK), reducing hepatic glucose production and improving peripheral insulin sensitivity. Also inhibits mitochondrial complex I, leading to altered cellular energy metabolism.",
            "target_protein": "AMPK (AMP-activated protein kinase)",
            "target_gene": "PRKAA1/PRKAA2",
            "target_class": "Kinase",
            "pathways": [
                "AMPK signaling pathway",
                "Insulin signaling pathway",
                "mTOR signaling (inhibition)",
                "Gluconeogenesis regulation",
                "Fatty acid oxidation",
            ],
            "binding_affinity_nm": None,  # Not a direct binder
            "selectivity": "Selective for AMPK pathway activation",
            "biomarkers": ["HbA1c", "Fasting glucose", "HOMA-IR", "Lactate levels"],
            "preclinical_models": ["db/db mice", "Zucker fatty rats", "HFD-induced obesity mice"],
        },
        "sildenafil": {
            "mechanism": "Selective inhibitor of phosphodiesterase type 5 (PDE5), preventing degradation of cyclic GMP (cGMP). This leads to smooth muscle relaxation and vasodilation in pulmonary vasculature and corpus cavernosum.",
            "target_protein": "Phosphodiesterase 5A (PDE5A)",
            "target_gene": "PDE5A",
            "target_class": "Phosphodiesterase",
            "pathways": [
                "cGMP-PKG signaling pathway",
                "Nitric oxide signaling",
                "Vascular smooth muscle relaxation",
                "Pulmonary vasodilation",
            ],
            "binding_affinity_nm": 3.9,
            "selectivity": "41-fold selective for PDE5 over PDE6, >1000-fold over PDE1-4",
            "biomarkers": ["6-minute walk distance (PAH)", "Pulmonary vascular resistance", "BNP levels"],
            "preclinical_models": ["Monocrotaline-induced PAH rats", "Hypoxia-induced PH mice"],
        },
        "aspirin": {
            "mechanism": "Irreversibly inhibits cyclooxygenase-1 (COX-1) and COX-2 enzymes through acetylation of serine residues, blocking prostaglandin and thromboxane A2 synthesis.",
            "target_protein": "Cyclooxygenase-1 (COX-1), Cyclooxygenase-2 (COX-2)",
            "target_gene": "PTGS1/PTGS2",
            "target_class": "Oxidoreductase",
            "pathways": [
                "Arachidonic acid metabolism",
                "Prostaglandin biosynthesis",
                "Platelet aggregation",
                "NF-κB signaling (indirect)",
            ],
            "binding_affinity_nm": 170,  # IC50 for COX-1
            "selectivity": "COX-1 selective at low doses; inhibits both at high doses",
            "biomarkers": ["Platelet aggregation", "Thromboxane B2 levels", "Bleeding time"],
            "preclinical_models": ["ApoE-/- atherosclerosis mice", "Collagen-induced arthritis models"],
        },
        "thalidomide": {
            "mechanism": "Binds to cereblon (CRBN), a component of the CRL4-CRBN E3 ubiquitin ligase, leading to degradation of transcription factors IKZF1 and IKZF3. Also inhibits TNF-α production and angiogenesis.",
            "target_protein": "Cereblon (CRBN)",
            "target_gene": "CRBN",
            "target_class": "E3 ubiquitin ligase substrate receptor",
            "pathways": [
                "Ubiquitin-proteasome pathway",
                "TNF-α signaling inhibition",
                "VEGF-mediated angiogenesis (inhibition)",
                "NF-κB pathway modulation",
            ],
            "binding_affinity_nm": 250,
            "selectivity": "High selectivity for CRBN; degrades specific neo-substrates",
            "biomarkers": ["M-protein (myeloma)", "Free light chains", "IKZF1/3 protein levels"],
            "preclinical_models": ["5T33 myeloma model", "Xenograft tumor models", "TNF-α release assays"],
        },
        "minoxidil": {
            "mechanism": "ATP-sensitive potassium channel opener that causes vasodilation. In hair follicles, it may prolong anagen phase and stimulate dermal papilla cells through increased VEGF expression.",
            "target_protein": "ATP-sensitive potassium channel (KATP)",
            "target_gene": "KCNJ8/ABCC9",
            "target_class": "Ion channel",
            "pathways": [
                "Potassium channel signaling",
                "Vascular smooth muscle relaxation",
                "VEGF signaling (hair growth)",
                "Wnt/β-catenin pathway (hair)",
            ],
            "binding_affinity_nm": None,
            "selectivity": "Relatively non-selective KATP opener",
            "biomarkers": ["Blood pressure", "Hair density", "Hair diameter"],
            "preclinical_models": ["Spontaneously hypertensive rats", "C57BL/6 hair growth models"],
        },
        "finasteride": {
            "mechanism": "Competitive inhibitor of type II 5-alpha reductase, blocking conversion of testosterone to dihydrotestosterone (DHT). Reduces DHT levels in scalp and prostate.",
            "target_protein": "Steroid 5-alpha reductase 2",
            "target_gene": "SRD5A2",
            "target_class": "Oxidoreductase",
            "pathways": [
                "Androgen metabolism",
                "DHT signaling (inhibition)",
                "Prostatic epithelial cell proliferation",
                "Hair follicle androgen response",
            ],
            "binding_affinity_nm": 10,
            "selectivity": "30-fold selective for type II over type I 5-alpha reductase",
            "biomarkers": ["Serum DHT levels", "PSA (prostate)", "Hair count"],
            "preclinical_models": ["Castrated rat prostate models", "Stump-tailed macaque alopecia model"],
        },
        "gabapentin": {
            "mechanism": "Binds to the α2δ-1 subunit of voltage-gated calcium channels, reducing calcium influx and neurotransmitter release. Does not bind GABA receptors despite its name.",
            "target_protein": "Voltage-gated calcium channel α2δ-1 subunit",
            "target_gene": "CACNA2D1",
            "target_class": "Ion channel auxiliary subunit",
            "pathways": [
                "Calcium channel signaling",
                "Glutamate release (reduction)",
                "Descending pain modulation",
                "GABA release (enhancement)",
            ],
            "binding_affinity_nm": 59,
            "selectivity": "Selective for α2δ-1 subunit; no GABA receptor binding",
            "biomarkers": ["Pain scores (VAS)", "Seizure frequency", "Sleep quality measures"],
            "preclinical_models": ["Spinal nerve ligation model", "Diabetic neuropathy models", "PTZ seizure model"],
        },
        "amantadine": {
            "mechanism": "Non-competitive NMDA receptor antagonist that also enhances dopamine release and blocks dopamine reuptake. Originally developed as antiviral (influenza A M2 ion channel blocker).",
            "target_protein": "NMDA receptor, Dopamine transporter",
            "target_gene": "GRIN1/GRIN2A/SLC6A3",
            "target_class": "Ion channel / Transporter",
            "pathways": [
                "Glutamatergic signaling (inhibition)",
                "Dopaminergic signaling (enhancement)",
                "Influenza M2 channel blocking",
            ],
            "binding_affinity_nm": 10000,  # Weak NMDA antagonist
            "selectivity": "Weak, non-selective NMDA antagonist; multiple mechanisms",
            "biomarkers": ["UPDRS scores (Parkinson's)", "Dyskinesia rating scales"],
            "preclinical_models": ["6-OHDA lesioned rats", "MPTP primate models"],
        },
        "rapamycin": {
            "mechanism": "Binds to FKBP12, and the complex inhibits mTORC1, a key regulator of cell growth, proliferation, and metabolism. Leads to cell cycle arrest and immunosuppression.",
            "target_protein": "mTOR (mechanistic target of rapamycin)",
            "target_gene": "MTOR",
            "target_class": "Kinase",
            "pathways": [
                "mTOR signaling pathway",
                "PI3K-Akt pathway",
                "Autophagy regulation",
                "Cell cycle control",
                "Protein synthesis regulation",
            ],
            "binding_affinity_nm": 0.2,
            "selectivity": "Highly selective for mTORC1; minimal mTORC2 inhibition at therapeutic doses",
            "biomarkers": ["S6K1 phosphorylation", "4E-BP1 phosphorylation", "Autophagy markers"],
            "preclinical_models": ["Transplant rejection models", "Cancer xenografts", "Aging studies in mice"],
        },
        "lithium": {
            "mechanism": "Inhibits inositol monophosphatase (IMPase) and glycogen synthase kinase-3 (GSK-3), affecting multiple signaling cascades including Wnt pathway and neurotrophic factors.",
            "target_protein": "Glycogen synthase kinase-3 (GSK-3), Inositol monophosphatase",
            "target_gene": "GSK3A/GSK3B/IMPA1",
            "target_class": "Kinase / Phosphatase",
            "pathways": [
                "GSK-3 signaling",
                "Wnt/β-catenin pathway",
                "Inositol phosphate signaling",
                "BDNF/TrkB signaling",
            ],
            "binding_affinity_nm": None,  # Complex mechanism
            "selectivity": "Non-selective; affects multiple targets",
            "biomarkers": ["Serum lithium levels", "Thyroid function tests", "Renal function"],
            "preclinical_models": ["Forced swim test", "Learned helplessness models", "GSK-3 activity assays"],
        },
    }

    # Common indication-mechanism relationships
    INDICATION_MECHANISMS = {
        "type 2 diabetes": {
            "key_pathways": ["Insulin signaling", "AMPK activation", "GLP-1 receptor signaling", "SGLT2 inhibition"],
            "relevant_biomarkers": ["HbA1c", "Fasting glucose", "HOMA-IR", "C-peptide"],
        },
        "cancer": {
            "key_pathways": ["Cell cycle regulation", "Apoptosis", "Angiogenesis", "Immune checkpoint", "DNA repair"],
            "relevant_biomarkers": ["Tumor markers", "ctDNA", "PD-L1 expression", "TMB"],
        },
        "alzheimer": {
            "key_pathways": ["Amyloid processing", "Tau phosphorylation", "Cholinergic signaling", "Neuroinflammation"],
            "relevant_biomarkers": ["Amyloid PET", "Tau PET", "CSF Aβ42/40", "CSF p-tau"],
        },
        "depression": {
            "key_pathways": ["Serotonergic signaling", "Noradrenergic signaling", "BDNF/TrkB", "HPA axis"],
            "relevant_biomarkers": ["HAM-D score", "MADRS score", "BDNF levels"],
        },
        "parkinson": {
            "key_pathways": ["Dopaminergic signaling", "Alpha-synuclein aggregation", "Mitochondrial function"],
            "relevant_biomarkers": ["UPDRS score", "DAT-SPECT", "Alpha-synuclein (CSF)"],
        },
        "inflammation": {
            "key_pathways": ["NF-κB signaling", "TNF-α pathway", "IL-6 signaling", "JAK-STAT pathway"],
            "relevant_biomarkers": ["CRP", "ESR", "IL-6 levels", "TNF-α levels"],
        },
    }

    def __init__(self):
        """Initialize the scientific details extractor."""
        pass

    async def extract_details(
        self,
        drug_name: str,
        indication: str,
        evidence_items: List[Any] = None
    ) -> ScientificDetails:
        """
        Extract detailed scientific data for a drug-indication pair.

        Args:
            drug_name: Drug name
            indication: Target indication
            evidence_items: List of evidence items to extract from

        Returns:
            ScientificDetails object
        """
        drug_lower = drug_name.lower()

        # Check curated data first
        drug_data = None
        for name, data in self.DRUG_SCIENTIFIC_DATA.items():
            if name in drug_lower or drug_lower in name:
                drug_data = data
                break

        # Extract publications from evidence
        publications = self._extract_publications(evidence_items or [])

        # Extract additional data from evidence metadata
        evidence_mechanism = self._extract_mechanism_from_evidence(evidence_items or [])
        evidence_targets = self._extract_targets_from_evidence(evidence_items or [])
        evidence_pathways = self._extract_pathways_from_evidence(evidence_items or [])
        evidence_biomarkers = self._extract_biomarkers_from_evidence(evidence_items or [], indication)

        # Build scientific details
        if drug_data:
            return ScientificDetails(
                drug_name=drug_name,
                indication=indication,
                mechanism_of_action=drug_data.get("mechanism", evidence_mechanism or "Mechanism under investigation"),
                target_protein=drug_data.get("target_protein", evidence_targets.get("protein")),
                target_gene=drug_data.get("target_gene", evidence_targets.get("gene")),
                target_class=drug_data.get("target_class"),
                pathways=drug_data.get("pathways", evidence_pathways) or evidence_pathways,
                binding_affinity_nm=drug_data.get("binding_affinity_nm"),
                selectivity_profile=drug_data.get("selectivity"),
                key_publications=publications[:10],  # Top 10
                preclinical_models=drug_data.get("preclinical_models", []),
                biomarkers=drug_data.get("biomarkers", evidence_biomarkers) or evidence_biomarkers,
                clinical_evidence_summary=self._generate_clinical_summary(evidence_items or [], indication),
                mechanistic_rationale=self._generate_mechanistic_rationale(drug_name, indication, drug_data),
            )
        else:
            # Build from evidence only
            return ScientificDetails(
                drug_name=drug_name,
                indication=indication,
                mechanism_of_action=evidence_mechanism or "Mechanism under investigation",
                target_protein=evidence_targets.get("protein"),
                target_gene=evidence_targets.get("gene"),
                target_class=evidence_targets.get("class"),
                pathways=evidence_pathways,
                binding_affinity_nm=None,
                selectivity_profile=None,
                key_publications=publications[:10],
                preclinical_models=[],
                biomarkers=evidence_biomarkers,
                clinical_evidence_summary=self._generate_clinical_summary(evidence_items or [], indication),
                mechanistic_rationale=self._generate_mechanistic_rationale(drug_name, indication, None),
            )

    def _extract_publications(self, evidence_items: List[Any]) -> List[KeyPublication]:
        """Extract key publications from evidence items."""
        publications = []
        seen_titles = set()

        for item in evidence_items:
            # Handle both dict and object access
            source = getattr(item, "source", None) or (item.get("source") if isinstance(item, dict) else None)
            if source not in ["literature", "semantic_scholar"]:
                continue

            metadata = getattr(item, "metadata", {}) or (item.get("metadata", {}) if isinstance(item, dict) else {})
            title = getattr(item, "title", None) or (item.get("title") if isinstance(item, dict) else None)
            summary = getattr(item, "summary", "") or (item.get("summary", "") if isinstance(item, dict) else "")

            if not title or title.lower() in seen_titles:
                continue

            seen_titles.add(title.lower())

            pub = KeyPublication(
                pmid=metadata.get("pmid"),
                title=title,
                authors=metadata.get("authors"),
                journal=metadata.get("journal"),
                year=metadata.get("year"),
                key_finding=summary[:300] if summary else "See publication for details",
                citation_count=metadata.get("citation_count") or metadata.get("citations"),
                url=getattr(item, "url", None) or (item.get("url") if isinstance(item, dict) else None),
            )
            publications.append(pub)

        # Sort by citation count
        publications.sort(key=lambda x: x.citation_count or 0, reverse=True)

        return publications

    def _extract_mechanism_from_evidence(self, evidence_items: List[Any]) -> Optional[str]:
        """Extract mechanism information from evidence metadata."""
        mechanisms = []

        for item in evidence_items:
            source = getattr(item, "source", None) or (item.get("source") if isinstance(item, dict) else None)
            metadata = getattr(item, "metadata", {}) or (item.get("metadata", {}) if isinstance(item, dict) else {})

            if source in ["opentargets", "drugbank"]:
                mech = metadata.get("mechanism") or metadata.get("mechanism_of_action")
                if mech and mech not in mechanisms:
                    mechanisms.append(mech)

        return mechanisms[0] if mechanisms else None

    def _extract_targets_from_evidence(self, evidence_items: List[Any]) -> Dict[str, Optional[str]]:
        """Extract target information from evidence."""
        targets = {"protein": None, "gene": None, "class": None}

        for item in evidence_items:
            source = getattr(item, "source", None) or (item.get("source") if isinstance(item, dict) else None)
            metadata = getattr(item, "metadata", {}) or (item.get("metadata", {}) if isinstance(item, dict) else {})

            if source in ["bioactivity", "opentargets", "uniprot", "drugbank"]:
                if not targets["protein"]:
                    targets["protein"] = (
                        metadata.get("target_name") or
                        metadata.get("target") or
                        metadata.get("protein_name")
                    )
                if not targets["gene"]:
                    targets["gene"] = (
                        metadata.get("target_gene") or
                        metadata.get("gene_symbol") or
                        metadata.get("gene")
                    )
                if not targets["class"]:
                    targets["class"] = metadata.get("target_class") or metadata.get("target_type")

        return targets

    def _extract_pathways_from_evidence(self, evidence_items: List[Any]) -> List[str]:
        """Extract pathway information from evidence."""
        pathways = set()

        for item in evidence_items:
            source = getattr(item, "source", None) or (item.get("source") if isinstance(item, dict) else None)
            metadata = getattr(item, "metadata", {}) or (item.get("metadata", {}) if isinstance(item, dict) else {})

            if source == "kegg":
                pathway_list = metadata.get("pathways", [])
                for p in pathway_list:
                    if isinstance(p, str):
                        pathways.add(p)
                    elif isinstance(p, dict):
                        pathways.add(p.get("name", str(p)))

            if source in ["opentargets", "uniprot"]:
                pathway_list = metadata.get("pathways", [])
                if isinstance(pathway_list, list):
                    pathways.update([str(p) for p in pathway_list[:5]])

        return list(pathways)[:10]

    def _extract_biomarkers_from_evidence(
        self,
        evidence_items: List[Any],
        indication: str
    ) -> List[str]:
        """Extract relevant biomarkers based on indication."""
        indication_lower = indication.lower()

        # Get indication-specific biomarkers
        for ind_key, ind_data in self.INDICATION_MECHANISMS.items():
            if ind_key in indication_lower or indication_lower in ind_key:
                return ind_data.get("relevant_biomarkers", [])

        return []

    def _generate_clinical_summary(
        self,
        evidence_items: List[Any],
        indication: str
    ) -> Optional[str]:
        """Generate summary of clinical evidence."""
        clinical_items = []

        for item in evidence_items:
            source = getattr(item, "source", None) or (item.get("source") if isinstance(item, dict) else None)
            if source == "clinical_trials":
                clinical_items.append(item)

        if not clinical_items:
            return "No direct clinical trial evidence identified. Further investigation recommended."

        # Count phases
        phases = {"Phase 1": 0, "Phase 2": 0, "Phase 3": 0, "Phase 4": 0}
        for item in clinical_items:
            metadata = getattr(item, "metadata", {}) or (item.get("metadata", {}) if isinstance(item, dict) else {})
            phase = metadata.get("phase", "").lower()
            for p in phases:
                if p.lower() in phase:
                    phases[p] += 1

        total = sum(phases.values())
        summary_parts = []

        if total > 0:
            summary_parts.append(f"{total} clinical trial(s) identified")
            phase_breakdown = [f"{count} {phase}" for phase, count in phases.items() if count > 0]
            if phase_breakdown:
                summary_parts.append(f"({', '.join(phase_breakdown)})")

        return " ".join(summary_parts) if summary_parts else None

    def _generate_mechanistic_rationale(
        self,
        drug_name: str,
        indication: str,
        drug_data: Optional[Dict]
    ) -> Optional[str]:
        """Generate mechanistic rationale for repurposing."""
        if not drug_data:
            return f"Mechanistic rationale for {drug_name} in {indication} requires further investigation to establish target engagement and pathway relevance."

        mechanism = drug_data.get("mechanism", "")
        pathways = drug_data.get("pathways", [])
        target = drug_data.get("target_protein", "")

        # Get indication-relevant pathways
        indication_lower = indication.lower()
        relevant_pathways = []
        for ind_key, ind_data in self.INDICATION_MECHANISMS.items():
            if ind_key in indication_lower or indication_lower in ind_key:
                relevant_pathways = ind_data.get("key_pathways", [])
                break

        # Find overlapping pathways
        overlapping = set(p.lower() for p in pathways).intersection(
            set(p.lower() for p in relevant_pathways)
        )

        if overlapping:
            return (
                f"{drug_name}'s primary mechanism involves {target if target else 'its molecular target'}, "
                f"which modulates pathways relevant to {indication}, including "
                f"{', '.join(list(overlapping)[:3])}. "
                f"This mechanistic overlap provides rationale for therapeutic investigation."
            )

        return (
            f"{drug_name} acts via {target if target else 'its established mechanism'}, "
            f"and may have therapeutic relevance in {indication} through pathway modulation. "
            f"Further mechanistic studies recommended to validate target engagement."
        )


# Singleton instance
_extractor_instance = None


def get_scientific_extractor() -> ScientificDetailsExtractor:
    """Get singleton instance of ScientificDetailsExtractor."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = ScientificDetailsExtractor()
    return _extractor_instance
