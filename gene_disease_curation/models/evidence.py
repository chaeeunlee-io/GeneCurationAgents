from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class EvidenceType(str, Enum):
    VARIANT = "variant"
    FUNCTIONAL = "functional"
    COHORT = "cohort"
    SEGREGATION = "segregation"

class EvidenceLevel(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"

class VariantEvidence(BaseModel):
    has_evidence: bool = Field(description="Whether variant evidence exists")
    evidence_level: str = Field(description="STRONG, MODERATE, or WEAK")
    variants_found: List[str] = Field(default_factory=list, description="Specific variants")
    variant_types: List[str] = Field(default_factory=list, description="Types (missense, etc)")
    num_patients: Optional[int] = Field(None, description="Number of patients")
    inheritance_pattern: Optional[str] = Field(None, description="de novo, inherited, etc")
    description: str = Field(description="Summary of variant evidence")
    confidence: float = Field(description="Confidence score 0-1")
    key_terms: List[str] = Field(default_factory=list, description="Key supporting terms")

class FunctionalEvidence(BaseModel):
    has_evidence: bool
    evidence_level: str
    experiment_types: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    disease_mechanism: Optional[str] = None
    rescue_experiment: bool = False
    description: str
    confidence: float

class CohortEvidence(BaseModel):
    has_evidence: bool
    evidence_level: str
    cohort_size: Optional[int] = None
    num_families: Optional[int] = None
    study_type: str
    statistical_significance: Optional[str] = None
    description: str
    confidence: float

class SegregationEvidence(BaseModel):
    has_evidence: bool
    evidence_level: str
    num_families: Optional[int] = None
    affected_members: Optional[int] = None
    inheritance_pattern: Optional[str] = None
    segregation_confirmed: bool = False
    description: str
    confidence: float