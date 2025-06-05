import asyncio
from typing import Dict, List, Any, Optional
import httpx
from datetime import datetime
import re
from collections import defaultdict

from langchain_openai import ChatOpenAI
from langchain.callbacks.tracers import LangChainTracer
from langsmith import trace

from ..models.state import CurationState, AbstractEvidence, EvidenceType, EvidenceLevel
# Remove the import of get_tracer
from ..config import SETTINGS
from ..agents.orchestrator import EvidenceExtractionOrchestrator
from ..api.tmvar import TMVarClient
from ..api.pubmed import PubMedManager
from ..ner.entity_extractor import BiomedicalNER
from ..vector_db.embeddings import EmbeddingModel
from ..vector_db.document_store import VectorDocumentStore

ner_model = BiomedicalNER()
embedding_model = EmbeddingModel()
document_store = VectorDocumentStore(embedding_model=embedding_model)
tmvar_client = TMVarClient()

async def search_literature(state: CurationState) -> Dict:
    """Search PubMed for relevant papers"""
    # remove the tracer.new_trace code that's causing the error
    pubmed = PubMedManager()
    
    pmids = await pubmed.search_papers(state["gene"], state["disease"])
    
    if not pmids:
        return {
            "pmids": [],
            "errors": [f"No papers found for {state['gene']} and {state['disease']}"],
            "current_stage": "complete",
            "messages": ["No literature found"]
        }
    
    return {
        "pmids": pmids,
        "current_stage": "fetch_abstracts",
        "messages": [f"Found {len(pmids)} papers"]
    }

async def fetch_abstracts(state: CurationState, tracer: Optional[LangChainTracer] = None) -> Dict:
    """Fetch abstracts for all PMIDs"""
    # use provided tracer or create a new one
    if tracer is None:
        tracer = LangChainTracer(
            project_name="gene-disease-curation"
        )
    
    # remove the tracer.new_trace code
    pubmed = PubMedManager()
    
    abstracts = await pubmed.fetch_abstracts(state["pmids"])
    
    # extract metadata
    years = [a["year"] for a in abstracts.values() if a.get("year")]
    authors = set(a["first_author"] for a in abstracts.values() if a.get("first_author"))
    
    result = {
        "abstracts": abstracts,
        "abstracts_analyzed": len(abstracts),
        "publication_years": sorted(years) if years else [],
        "independent_groups": len(authors),
        "current_stage": "extract_evidence",
        "messages": [f"Fetched {len(abstracts)} abstracts"]
    }
    return result

async def extract_evidence(state: CurationState, tracer: Optional[LangChainTracer] = None) -> Dict:
    """Extract evidence from all abstracts using parallel agents"""
    # use provided tracer or create a new one
    if tracer is None:
        tracer = LangChainTracer(
            project_name="gene-disease-curation"
        )
    
    # remove the tracer.new_trace code
    orchestrator = EvidenceExtractionOrchestrator(tracer=tracer)
    
    all_evidence = []
    
    batch_size = 5
    pmids = list(state["abstracts"].keys())
    
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i+batch_size]
        
        # create tasks for this batch
        tasks = []
        for pmid in batch:
            abstract_data = state["abstracts"][pmid]
            task = orchestrator.extract_all_evidence(
                pmid, abstract_data, state["gene"], state["disease"]
            )
            tasks.append(task)
        
        # parallel
        batch_results = await asyncio.gather(*tasks)
        
        for evidence_list in batch_results:
            all_evidence.extend(evidence_list)
    
    result = {
        "evidence_items": all_evidence,
        "current_stage": "calculate_scores",
        "messages": [f"Extracted {len(all_evidence)} evidence items"]
    }
    return result

async def calculate_scores(state: CurationState) -> Dict:
    """Calculate scores for each evidence type"""
    evidence_items = state["evidence_items"]
    
    # group evidence by type
    evidence_by_type = defaultdict(list)
    for evidence in evidence_items:
        # Check if evidence is a dict (TypedDict) or an object
        if isinstance(evidence, dict):
            evidence_type = evidence["evidence_type"]
        else:
            evidence_type = evidence.evidence_type
            
        evidence_by_type[evidence_type].append(evidence)
    
    # calculate scores for each type
    variant_score = _calculate_type_score(evidence_by_type[EvidenceType.VARIANT])
    functional_score = _calculate_type_score(evidence_by_type[EvidenceType.FUNCTIONAL])
    segregation_score = _calculate_type_score(evidence_by_type[EvidenceType.SEGREGATION])
    cohort_score = _calculate_type_score(evidence_by_type[EvidenceType.COHORT])
    
    # calculate total score with weights
    weights = {
        EvidenceType.VARIANT: 1.0,
        EvidenceType.FUNCTIONAL: 0.8,
        EvidenceType.SEGREGATION: 1.2,
        EvidenceType.COHORT: 1.5
    }
    
    total_score = (
        variant_score * weights[EvidenceType.VARIANT] +
        functional_score * weights[EvidenceType.FUNCTIONAL] +
        segregation_score * weights[EvidenceType.SEGREGATION] +
        cohort_score * weights[EvidenceType.COHORT]
    )
    
    # number of independent research groups?
    pmids = set()
    for evidence in evidence_items:
        if isinstance(evidence, dict):
            pmids.add(evidence["pmid"])
        else:
            pmids.add(evidence.pmid)
    
    independent_groups = min(len(pmids), 10)  # Cap at 10
    
    return {
        "variant_score": variant_score,
        "functional_score": functional_score,
        "segregation_score": segregation_score,
        "cohort_score": cohort_score,
        "total_score": total_score,
        "independent_groups": independent_groups,
        "current_stage": "classify_relationship",
        "messages": state["messages"] + [f"Total evidence score: {total_score:.2f}"]
    }

def _calculate_type_score(evidence_list: List[AbstractEvidence]) -> float:
    """Calculate score for a specific evidence type"""
    if not evidence_list:
        return 0.0
    
    # map evidence levels to scores
    level_scores = {
        EvidenceLevel.STRONG: 3.0,
        EvidenceLevel.MODERATE: 1.5,
        EvidenceLevel.WEAK: 0.5
    }
    
    # calculate base score from evidence levels
    base_score = 0.0
    for evidence in evidence_list:
        if isinstance(evidence, dict):
            level = evidence["evidence_level"]
        else:
            level = evidence.evidence_level
        base_score += level_scores[level]
    
    # apply diminishing returns for multiple pieces of evidence
    if len(evidence_list) > 1:
        # Log-based scaling to prevent scores from growing linearly
        scaling_factor = 1.0 + 0.5 * (len(evidence_list) - 1) ** 0.5
        base_score = base_score * scaling_factor / len(evidence_list)
    
    # apply confidence adjustments
    confidence_sum = 0.0
    for evidence in evidence_list:
        if isinstance(evidence, dict):
            confidence_sum += evidence["confidence"]
        else:
            confidence_sum += evidence.confidence
    
    confidence_adjustment = confidence_sum / len(evidence_list)
    
    return base_score * confidence_adjustment

async def classify_relationship(state: CurationState) -> Dict:
    """Classify the gene-disease relationship"""
    total_score = state["total_score"]
    
    thresholds = {
        "definitive": 30.0,
        "strong": 15.0,
        "moderate": 5.0,
        "limited": 2.0,
        "disputed": 0.0
    }
    
    classification = "no evidence"
    for level, threshold in thresholds.items():
        if total_score >= threshold:
            classification = level
            break
    
    # calculate confidence based on evidence diversity and independent sources
    evidence_types = set()
    for evidence in state["evidence_items"]:
        if isinstance(evidence, dict):
            evidence_types.add(evidence["evidence_type"])
        else:
            evidence_types.add(evidence.evidence_type)
    
    evidence_diversity = min(1.0, len(evidence_types) / 4.0)
    source_diversity = min(1.0, state["independent_groups"] / 5.0)
    
    confidence_level = 0.5 + 0.25 * evidence_diversity + 0.25 * source_diversity
    
    # adjust confidence based on publication years
    if state["publication_years"]:
        year_span = max(state["publication_years"]) - min(state["publication_years"])
        confidence_level *= (1 - (year_span / 100))  # Decrease confidence for older studies
    
    return {
        "classification_suggestion": classification,
        "confidence_level": confidence_level,
        "current_stage": "complete",
        "messages": state["messages"] + [f"Classification: {classification} with confidence {confidence_level:.2f}"]
    }
