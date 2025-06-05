from typing import Optional, Dict, List
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

from ..models.evidence import VariantEvidence, FunctionalEvidence, CohortEvidence, SegregationEvidence
from ..models.state import AbstractEvidence, EvidenceType, EvidenceLevel

class VariantEvidenceAgent:
    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=VariantEvidence)
        
        self.prompt = PromptTemplate(
            template="""Analyze this abstract for genetic variants in {gene} related to {disease}.
            
Look for: specific variants, variant types, patient counts, inheritance patterns, pathogenicity.

Evidence levels:
- STRONG: Multiple patients, clear pathogenic variants, segregation data
- MODERATE: Few patients but clear variant descriptions  
- WEAK: Variants mentioned but limited detail

Abstract: {abstract}

{format_instructions}""",
            input_variables=["gene", "disease", "abstract"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    async def analyze(self, pmid: str, abstract_data: Dict, gene: str, disease: str) -> Optional[AbstractEvidence]:
        
        try:
            response = await self.llm.ainvoke(
                self.prompt.format(
                    gene=gene,
                    disease=disease,
                    abstract=abstract_data["abstract"][:1500]
                )
            )
            
            result = self.parser.parse(response.content)
            
            #     (Pdb) result
            # VariantEvidence(has_evidence=True, evidence_level='WEAK', variants_found=[], variant_types=[], num_patients=None, inheritance_pattern='de novo', description='The abstract discusses the role of de novo variants in the SCN1A gene related to Dravet syndrome, but does not specify particular variants or patient counts.', confidence=0.5, key_terms=['Dravet syndrome', 'SCN1A', 'de novo variants', 'haploinsufficiency', 'TANGO technology'])
            #     import pdb; pdb.set_trace()
            if not result.has_evidence:
                # import pdb; pdb.set_trace()
                return None
            
            return AbstractEvidence(
                pmid=pmid,
                evidence_type=EvidenceType.VARIANT,
                evidence_level=EvidenceLevel(result.evidence_level.lower()),
                description=result.description,
                confidence=result.confidence,
                extracted_by="VariantEvidenceAgent",
                key_terms=result.key_terms[:5],
                raw_data=result.dict()
            )
        except Exception as e:
            
            print(f"Error in VariantEvidenceAgent: {e}")
            import pdb; pdb.set_trace()
            return None


class FunctionalEvidenceAgent:
    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=FunctionalEvidence)
        
        self.prompt = PromptTemplate(
            template="""Analyze this abstract for functional studies of {gene} related to {disease}.

Look for: experimental methods, assays, model organisms, rescue experiments, mechanism.

Evidence levels:
- STRONG: Clear functional defects, rescue experiments, mechanism shown
- MODERATE: Basic functional studies with disease relevance
- WEAK: Functional studies mentioned but limited detail

Abstract: {abstract}

{format_instructions}""",
            input_variables=["gene", "disease", "abstract"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    async def analyze(self, pmid: str, abstract_data: Dict, gene: str, disease: str) -> Optional[AbstractEvidence]:
        try:
            response = await self.llm.ainvoke(
                self.prompt.format(
                    gene=gene,
                    disease=disease,
                    abstract=abstract_data["abstract"][:1500]
                )
            )
            
            result = self.parser.parse(response.content)
            # import pdb; pdb.set_trace()
            # (Pdb) result
            # FunctionalEvidence(has_evidence=False, evidence_level='WEAK', experiment_types=[], key_findings=[], disease_mechanism=None, rescue_experiment=False, description='The abstract discusses Dravet syndrome and its association with SCN1A mutations but lacks specific details on experimental methods, assays, model organisms, or any functional studies.', confidence=2.0)
            
            
            if not result.has_evidence:
                return None
            
            confidence = result.confidence * 1.2 if result.rescue_experiment else result.confidence
            
            return AbstractEvidence(
                pmid=pmid,
                evidence_type=EvidenceType.FUNCTIONAL,
                evidence_level=EvidenceLevel(result.evidence_level.lower()),
                description=result.description,
                confidence=min(1.0, confidence),
                extracted_by="FunctionalEvidenceAgent",
                key_terms=result.experiment_types[:3],
                raw_data=result.dict()
            )
        except:
            return None


class CohortEvidenceAgent:
    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=CohortEvidence)
        
        self.prompt = PromptTemplate(
            template="""Analyze this abstract for cohort/population studies of {gene} and {disease}.

Look for: patient numbers, study design, statistics, controls.

Evidence levels:
- STRONG: Large cohort (>50), controls, statistical significance
- MODERATE: Medium cohort (10-50) or good design
- WEAK: Small cohort (<10) or case series

Abstract: {abstract}

{format_instructions}""",
            input_variables=["gene", "disease", "abstract"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    async def analyze(self, pmid: str, abstract_data: Dict, gene: str, disease: str) -> Optional[AbstractEvidence]:
        try:
            response = await self.llm.ainvoke(
                self.prompt.format(
                    gene=gene,
                    disease=disease,
                    abstract=abstract_data["abstract"][:1500]
                )
            )
            
            result = self.parser.parse(response.content)
            
            if not result.has_evidence:
                return None
            
            return AbstractEvidence(
                pmid=pmid,
                evidence_type=EvidenceType.COHORT,
                evidence_level=EvidenceLevel(result.evidence_level.lower()),
                description=result.description,
                confidence=result.confidence,
                extracted_by="CohortEvidenceAgent",
                key_terms=[result.study_type],
                raw_data=result.dict()
            )
        except:
            return None


class SegregationEvidenceAgent:
    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=SegregationEvidence)
        
        self.prompt = PromptTemplate(
            template="""Analyze this abstract for family segregation of {gene} with {disease}.

Look for: families studied, affected members, inheritance patterns, segregation confirmation.

Evidence levels:
- STRONG: Multiple families, clear segregation
- MODERATE: Few families but clear segregation
- WEAK: Family data mentioned but limited

Abstract: {abstract}

{format_instructions}""",
            input_variables=["gene", "disease", "abstract"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    async def analyze(self, pmid: str, abstract_data: Dict, gene: str, disease: str) -> Optional[AbstractEvidence]:
        try:
            response = await self.llm.ainvoke(
                self.prompt.format(
                    gene=gene,
                    disease=disease,
                    abstract=abstract_data["abstract"][:1500]
                )
            )
            
            result = self.parser.parse(response.content)
            
            if not result.has_evidence:
                return None
            
            return AbstractEvidence(
                pmid=pmid,
                evidence_type=EvidenceType.SEGREGATION,
                evidence_level=EvidenceLevel(result.evidence_level.lower()),
                description=result.description,
                confidence=result.confidence,
                extracted_by="SegregationEvidenceAgent",
                key_terms=[result.inheritance_pattern] if result.inheritance_pattern else ["segregation"],
                raw_data=result.dict()
            )
        except:
            return None