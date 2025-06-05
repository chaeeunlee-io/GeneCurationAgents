import asyncio
from typing import List, Dict, Optional
from langchain.callbacks.tracers import LangChainTracer
from langchain_openai import ChatOpenAI

from ..models.state import AbstractEvidence
from .agents import VariantEvidenceAgent, FunctionalEvidenceAgent, CohortEvidenceAgent, SegregationEvidenceAgent

class EvidenceExtractionOrchestrator:
    """Orchestrates all evidence extraction agents"""
    
    def __init__(self, tracer: Optional[LangChainTracer] = None):

        if tracer is None:
            tracer = LangChainTracer(
                project_name="gene-disease-curation"
            )
        self.tracer = tracer

        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, callbacks=[tracer])

        self.variant_agent = VariantEvidenceAgent(self.llm)
        self.functional_agent = FunctionalEvidenceAgent(self.llm)
        self.cohort_agent = CohortEvidenceAgent(self.llm)
        self.segregation_agent = SegregationEvidenceAgent(self.llm)
    
    async def extract_all_evidence(self, pmid: str, abstract_data: Dict, gene: str, disease: str) -> List[AbstractEvidence]:
        """Run all agents in parallel for a single abstract"""

        print(f"Extracting evidence from PMID {pmid}")
        
        tasks = [
            self.variant_agent.analyze(pmid, abstract_data, gene, disease),
            self.functional_agent.analyze(pmid, abstract_data, gene, disease),
            self.cohort_agent.analyze(pmid, abstract_data, gene, disease),
            self.segregation_agent.analyze(pmid, abstract_data, gene, disease)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        evidence_items = []
        for result in results:
            if result and not isinstance(result, Exception):
                evidence_items.append(result)
        
        # Remove the pdb.set_trace() line that's causing the debugger to stop
        # import pdb; pdb.set_trace()
        
        # print(f"Found {len(evidence_items)} evidence items in PMID {pmid}")
        return evidence_items
