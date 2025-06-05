from typing import Dict, List, TypedDict, Annotated
import operator
from .evidence import EvidenceType, EvidenceLevel

class AbstractEvidence(TypedDict):
    pmid: str
    evidence_type: EvidenceType
    evidence_level: EvidenceLevel
    description: str
    confidence: float
    extracted_by: str
    key_terms: List[str]
    raw_data: Dict  

class CurationState(TypedDict):

    gene: str
    disease: str
    
    pmids: List[str]
    abstracts: Dict[str, Dict]  # pmid -> abstract data
    evidence_items: Annotated[List[AbstractEvidence], operator.add]

    variant_score: float
    functional_score: float
    segregation_score: float
    cohort_score: float
    total_score: float

    publication_years: List[int]
    independent_groups: int
    abstracts_analyzed: int

    classification_suggestion: str
    confidence_level: float
    
    current_stage: str
    errors: List[str]
    processing_time: float
    
    messages: Annotated[List[str], operator.add]